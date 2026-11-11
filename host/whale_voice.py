#!/usr/bin/env python3
"""whale_voice.py — the Mac-side brain for the Whale-chan TV assistant.

Pipeline:  TV mic WAV  ->  Whisper STT  ->  DSH headless (persistent session)
           ->  short spoken reply (returned as JSON; the TV speaks it).

The voice session is a normal DSH Session resumed with `--session-id`, so the
assistant keeps context between utterances. The agent has the workspace bash
tool, which is how it controls the TV: `python3 host/dshtv.py ...` (keys,
launch any app, typing, screenshots, TTS).

Run (daemon):
    dshtv/venv/bin/python dshtv/whale_voice.py --serve --port 8766

Run (one file, for testing):
    dshtv/venv/bin/python dshtv/whale_voice.py --once /tmp/room.wav

Security: every HTTP request needs the token from .auth/whale.token
(header `X-Whale-Token` or `?token=`). Bind defaults to 0.0.0.0 so the TV can
reach it on the LAN; keep it on the LAN, never expose it to the internet.
"""

from __future__ import annotations

import argparse
import queue
import json
import re
import os
import re
import subprocess
import sys
import base64
import secrets
import socket
import tempfile
import wave
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tv_memory  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DSH_HOME = ROOT / ".dsh-voice"
KEY_FILE = ROOT / ".auth" / "deepseek.key"
TOKEN_FILE = ROOT / ".auth" / "whale.token"
SESSION_FILE = DSH_HOME / "whale-session.json"
TV_CONFIG = ROOT / "host" / "config.json"

try:
    import qrcode
except Exception:  # optional: pair via URL/code without a QR image
    qrcode = None

PAIR_TTL_SECONDS = 300
PAIR_MAX = 64
PAIRS: dict = {}
DEFAULT_MODEL = "mlx-community/whisper-base.en-mlx"
MAX_TURN_SECONDS = 600

# The voice brain runs as a sandboxed DSH turn, so it can only write inside the workspace.
# It therefore DRAFTS a catalog; the daemon (an ordinary process, outside that sandbox)
# applies it. Handing the sandbox the live path directly fails with "Operation not permitted",
# which is exactly what the first attempts did.
PENDING_CATALOGS = ROOT / ".dsh-voice" / "pending-catalogs"
INSTALLER = Path.home() / "Library" / "Application Support" / "dsh-tv-addon" / "install_catalog.py"

# The voice agent's standing brief. Kept short: it is prepended to every
# utterance and also costs tokens, but without it the agent does not know that
# it is allowed (and expected) to drive the television.
BRIEF = (
    "You are Whale-chan, the voice assistant for the TV in this house. "
    "You control the TV with the bash tool by running commands from the "
    "workspace, e.g. `python3 host/dshtv.py state` (foreground app + volume), "
    "`python3 host/dshtv.py apps` (installed apps), "
    "`python3 host/dshtv.py launch <app>`, "
    "`python3 host/dshtv.py key up|down|left|right|ok|back|home|recents|playpause|next|prev|rewind|fastforward|volup|voldown|mute`, "
    "`python3 host/dshtv.py text \"...\"`, `python3 host/dshtv.py screenshot --out /tmp/tv.jpg`. "
    "The device is the onn 4K Pro at 192.168.4.58. "
    "Work out the shortest key sequence, run it, check `state` when you need to "
    "know what happened, and never assume an app is open. "
    "Before driving an app you have not used this turn, read its playbook from "
    "host/playbooks/ (index: host/playbooks/README.md) and the app catalog "
    "host/tv-apps.json; prefer their key steps over guessing. Use "
    "`python3 host/dshtv.py ui` to read on-screen labels/focus before and after "
    "a step. "
    "You can also BUILD A CATALOG ROW for the player when the user asks for one - e.g. "
    "\"make me a catalog of films like X\". The row is not a filter: you choose the titles. "
    "Choose 10-18 real films that share a reason to sit together, using their REAL IMDB ids "
    "(tt...); never invent an id. Write a JSON file to "
    ".dsh-voice/pending-catalogs/<slug>.json shaped as a list with one entry: "
    "[{\"id\":\"<slug>\",\"type\":\"movie\",\"name\":\"<row title>\","
    "\"seed\":\"<what the user said>\",\"theme\":\"<one line>\",\"picks\":[\"tt...\", ...]}]. "
    "That directory is inside the workspace, which is the only place you can write. The host "
    "applies it after your turn and checks it against the live addon - you cannot see the live "
    "store, so do NOT claim the row is live and do NOT run any installer yourself. Say what you "
    "put in the row; the host adds the confirmation. If writing the file fails, say that plainly. "
    "The user's request below is a speech transcript and may contain recognition "
    "errors; use judgment. Then reply with ONE short spoken sentence (no lists, "
    "no tool narration). If the request is unclear or dangerous, ask a short "
    "question instead of acting."
)


def lan_ip() -> str:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("192.168.4.1", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except Exception:
        return "127.0.0.1"


def _png_from_matrix(matrix: list, box_size: int = 8) -> bytes:
    """Encode a QR module matrix as an 8-bit greyscale PNG using stdlib only.

    The `qrcode` package is pure Python, but its convenience `.save()` path
    needs Pillow, which the daemon's interpreter does not ship. Get the module
    matrix from `qrcode` and write the PNG chunks directly: black modules are
    byte 0, light modules byte 255, one filter-0 byte per scanline, zlib for
    IDAT. `matrix` already includes the QR quiet-zone border.
    """
    import struct
    import zlib

    modules = len(matrix[0]) if matrix else 0
    if modules == 0 or len(matrix) != modules:
        raise ValueError("qr matrix must be square and non-empty")
    width = modules * box_size
    raw = bytearray()
    for row in matrix:
        line = bytearray()
        for cell in row:
            line.extend(b"\x00" * box_size if cell else b"\xff" * box_size)
        for _ in range(box_size):
            raw.append(0)  # PNG filter type 0 (None)
            raw.extend(line)
    compressed = zlib.compress(bytes(raw), 9)

    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", width, width, 8, 0, 0, 0, 0)  # 8-bit greyscale
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", compressed)
            + chunk(b"IEND", b""))


def qr_png_b64(text: str) -> str | None:
    """Base64 PNG of a QR code for `text`, or None when the QR path is broken."""
    if qrcode is None:
        return None
    try:
        code = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=4,
        )
        code.add_data(text)
        code.make(fit=True)
        return base64.b64encode(_png_from_matrix(code.get_matrix(), box_size=8)).decode()
    except Exception:
        return None


def prune_pairs(now: float | None = None) -> None:
    """Drop expired pairing sessions. Safe to call from any handler."""
    now = time.time() if now is None else now
    for pid in [p for p, e in PAIRS.items() if now - e["created"] > PAIR_TTL_SECONDS]:
        PAIRS.pop(pid, None)


def pending_pairs() -> list[dict]:
    """Unapproved, unexpired pairing sessions, oldest first.

    `createdAt` is epoch milliseconds (the same clock as /health `now`) so the
    DSH pane can format the age without knowing the daemon's clock.
    """
    now = time.time()
    prune_pairs(now)
    pending = [
        {
            "id": pid,
            "code": entry["code"],
            "createdAt": int(entry["created"] * 1000),
            "ageSeconds": max(0, int(now - entry["created"])),
            # The TV's LAN address (best effort): the request source address.
            "host": entry.get("remote") or None,
        }
        for pid, entry in PAIRS.items()
        if not entry.get("approved")
    ]
    pending.sort(key=lambda item: item["createdAt"])
    return pending


def new_pair(remote: str = "") -> tuple[str, str]:
    prune_pairs()
    if len(PAIRS) >= PAIR_MAX:
        oldest = min(PAIRS, key=lambda pid: PAIRS[pid]["created"])
        PAIRS.pop(oldest, None)
    pid = secrets.token_hex(8)
    code = "".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6))
    PAIRS[pid] = {"code": code, "created": time.time(), "approved": False,
                  "remote": remote or ""}
    return pid, code


def pair_config(port: int) -> dict:
    return {"host": lan_ip(), "port": port, "token": read_token()}


def eprint(*a: object) -> None:
    print(*a, file=sys.stderr, flush=True)


def read_key() -> str:
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if key:
        return key
    try:
        return KEY_FILE.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise SystemExit(f"missing DSH API key: {exc}") from exc


def read_token(create: bool = True) -> str:
    try:
        t = TOKEN_FILE.read_text(encoding="utf-8").strip()
        if t:
            return t
    except OSError:
        pass
    if not create:
        return ""
    import secrets
    t = "".join(secrets.choice("abcdefghjkmnpqrstuvwxyz23456789") for _ in range(10))
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(t + "\n", encoding="utf-8")
    os.chmod(TOKEN_FILE, 0o600)
    return t


def normalize_wav(src: Path) -> Path:
    """Far-field mics are quiet; match tv_transcribe.py's filtering."""
    out = Path(tempfile.mkstemp(prefix="whale-norm-", suffix=".wav")[1])
    filt = "highpass=f=100,lowpass=f=7800,dynaudnorm=f=150:g=15:p=0.9,volume=8dB"
    proc = subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
         "-af", filt, "-ar", "16000", "-ac", "1", str(out)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0 or not out.exists():
        try:
            out.unlink()
        except OSError:
            pass
        return src
    return out


def _audio_rms(path) -> float:
    """RMS of 16-bit PCM WAV — used to reject near-silence before Whisper."""
    try:
        with wave.open(str(path), "rb") as w:
            if w.getsampwidth() != 2:
                return 10 ** 9  # let ffmpeg-normalised odd formats through
            frames = w.readframes(w.getnframes())
        if not frames:
            return 0.0
        import array
        samples = array.array("h")
        samples.frombytes(frames)
        if not samples:
            return 0.0
        return (sum(s * s for s in samples) / len(samples)) ** 0.5
    except Exception:
        return 10 ** 9


_LOOP_WORD = re.compile(r"\b(\w+)\b(?:[\s,.!?]+\1\b){4,}", re.IGNORECASE)


def _clean_transcript(text: str) -> str:
    """Drop Whisper's silence/loop hallucinations ("Okay. Okay. Okay. ...")."""
    t = " ".join(text.split())
    if not t:
        return ""
    # one word repeated 5+ times is a decode loop, not speech
    if _LOOP_WORD.search(t):
        return ""
    words = t.split()
    uniq = {w.lower().strip(".,!?") for w in words}
    if len(words) >= 5 and len(uniq) <= 2 and len(words) / max(1, len(uniq)) > 3:
        return ""
    return t


def _node_path() -> str:
    home = Path.home()
    candidates = [
        os.environ.get("DSH_NODE_PATH"),
        os.environ.get("NODE_PATH"),
        str(home / ".local/share/dsh-superagent-runtime/node_modules/.pnpm/node_modules"),
        str(home / ".local/share/dsh-superagent-runtime/node_modules"),
        str(ROOT / "node_modules"),
        str(ROOT / "host" / "node_modules"),
    ]
    for profile in sorted((home / ".dsh/profiles").glob("*/node_modules/.pnpm/node_modules")):
        candidates.append(str(profile))
    seen, parts = set(), []
    for c in candidates:
        if c and c not in seen and Path(c).exists():
            seen.add(c)
            parts.append(c)
    return ":".join(parts)


def _node_env() -> dict:
    env = dict(os.environ)
    np = _node_path()
    if np:
        env["NODE_PATH"] = np
    return env


class _DshWorker:
    """Persistent sherpa-onnx worker: model loads once, ~0.1s per utterance."""

    def __init__(self, model_dir: str | None = None):
        self.model_dir = model_dir
        self.proc: subprocess.Popen | None = None
        self.queue: queue.Queue = queue.Queue()
        self.lock = threading.Lock()
        self.next_id = 0
        self.reader: threading.Thread | None = None

    def _start(self) -> None:
        cmd = [os.environ.get("WHALE_NODE") or "node",
               str(ROOT / "host" / "stt_worker.mjs")]
        if self.model_dir:
            cmd += ["--model-dir", self.model_dir]
        self.proc = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, bufsize=1,
            cwd=str(ROOT), env=_node_env())
        self.queue = queue.Queue()

        def pump(stream):
            for line in stream:
                self.queue.put(line)

        self.reader = threading.Thread(target=pump, args=(self.proc.stdout,), daemon=True)
        self.reader.start()
        # wait for the ready line
        deadline = time.time() + 20
        while time.time() < deadline:
            try:
                line = self.queue.get(timeout=max(0.1, deadline - time.time()))
            except queue.Empty:
                break
            try:
                msg = json.loads(line)
            except ValueError:
                continue
            if msg.get("ready"):
                return
            if msg.get("ready") is False:
                raise RuntimeError(msg.get("error") or "stt worker failed to start")
        raise RuntimeError("stt worker did not become ready")

    def transcribe(self, wav: Path, timeout: float = 30.0) -> dict:
        with self.lock:
            if self.proc is None or self.proc.poll() is not None:
                self._start()
            self.next_id += 1
            rid = self.next_id
            try:
                self.proc.stdin.write(json.dumps({"id": rid, "wav": str(wav)}) + "\n")
                self.proc.stdin.flush()
            except Exception:
                self._stop()
                raise
            deadline = time.time() + timeout
            while time.time() < deadline:
                try:
                    line = self.queue.get(timeout=max(0.05, deadline - time.time()))
                except queue.Empty:
                    break
                try:
                    msg = json.loads(line)
                except ValueError:
                    continue
                if msg.get("id") != rid:
                    continue
                if not msg.get("ok"):
                    raise RuntimeError(msg.get("error") or "stt failed")
                return msg
            self._stop()
            raise RuntimeError("stt worker timeout")

    def _stop(self) -> None:
        try:
            if self.proc:
                self.proc.kill()
        except Exception:
            pass
        self.proc = None

    def close(self) -> None:
        self._stop()


def _transcribe_dsh(wav: Path, model_dir: str | None = None) -> dict:
    """Transcribe with DSH's own SenseVoice model (sherpa-onnx)."""
    script = ROOT / "host" / "dsh_stt.mjs"
    node = os.environ.get("WHALE_NODE") or "node"
    cmd = [node, str(script), "--wav", str(wav)]
    if model_dir:
        cmd += ["--model-dir", model_dir]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=90,
                          cwd=str(ROOT), env=_node_env())
    line = (proc.stdout or "").strip().splitlines()
    if not line:
        raise RuntimeError(f"dsh_stt empty output: {(proc.stderr or '').strip()[:200]}")
    result = json.loads(line[-1])
    if not result.get("ok"):
        raise RuntimeError(str(result.get("error") or "dsh stt failed"))
    return result



_APP_CANON = ["Stremio", "TiviMate", "Nuvio", "CloudStream", "YouTube", "Netflix",
              "Prime Video", "Disney+", "Projectivy", "OwnTV", "JapanTV",
              "Haystack News", "Amazon Music"]
_APP_ALIASES = {
    "netflicks": "Netflix", "netflex": "Netflix", "prime": "Prime Video",
    "disney": "Disney+", "you tube": "YouTube", "youtube": "YouTube",
    "stremio": "Stremio", "streemo": "Stremio", "streemio": "Stremio",
    "streio": "Stremio", "stremo": "Stremio", "tivimate": "TiviMate",
    "tivimates": "TiviMate", "nuvio": "Nuvio", "nubio": "Nuvio",
    "cloudstream": "CloudStream", "cloud stream": "CloudStream",
}
_CANON_LOWER = {c.lower(): c for c in _APP_CANON}


def _app_name_match(word: str) -> str | None:
    import difflib
    w = word.lower()
    if w in _APP_ALIASES:
        return _APP_ALIASES[w]
    if w in _CANON_LOWER:
        return _CANON_LOWER[w]
    if len(w) >= 5:
        hit = difflib.get_close_matches(w, _CANON_LOWER.keys(), n=1, cutoff=0.82)
        if hit:
            return _CANON_LOWER[hit[0]]
    return None


def _correct_app_names(text: str) -> str:
    """Repair STT slips for the app names people actually say on this TV."""
    if not text:
        return text

    def repl(match):
        word = match.group(0)
        low = word.lower()
        if low == "open":
            return word
        if low.startswith("open") and len(low) > 6:
            rest = low[4:]
            name = _app_name_match(rest)
            if name:
                return "open " + name
        name = _app_name_match(low)
        return name or word

    return re.sub(r"[A-Za-z]{4,}", repl, text)


def _transcribe_dsh_oneshot(wav: Path, model_dir: str | None = None) -> dict:
    """One-shot fallback (kept for CLI/tests)."""
    script = ROOT / "host" / "dsh_stt.mjs"
    node = os.environ.get("WHALE_NODE") or "node"
    cmd = [node, str(script), "--wav", str(wav)]
    if model_dir:
        cmd += ["--model-dir", model_dir]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=90, cwd=str(ROOT))
    line = (proc.stdout or "").strip().splitlines()
    if not line:
        raise RuntimeError(f"dsh_stt empty output: {(proc.stderr or '').strip()[:200]}")
    result = json.loads(line[-1])
    if not result.get("ok"):
        raise RuntimeError(str(result.get("error") or "dsh stt failed"))
    return result


class Transcriber:
    """Loads mlx-whisper once; transcribes WAVs on demand."""

    def __init__(self, model: str = DEFAULT_MODEL, engine: str = "dsh",
                 dsh_model_dir: str | None = None):
        self.engine = engine
        self.dsh_model_dir = dsh_model_dir
        self.model = model
        self._lock = threading.Lock()
        self._worker = _DshWorker(dsh_model_dir) if engine == "dsh" else None
        os.environ.setdefault("HF_HOME", str(ROOT / ".tools" / "hf-cache"))
        os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

    def transcribe(self, wav: Path) -> dict:
        rms = _audio_rms(wav)
        if rms < 90:
            return {"text": "", "model": self.engine,
                    "note": f"near-silence rms={rms:.0f}"}
        if self.engine == "dsh":
            prepared = normalize_wav(wav)
            try:
                result = None
                if self._worker is not None:
                    try:
                        result = self._worker.transcribe(prepared)
                    except Exception as exc:  # noqa: BLE001
                        print(f"warm stt worker failed ({exc}); one-shot retry", flush=True)
                if result is None:
                    result = _transcribe_dsh_oneshot(prepared, self.dsh_model_dir)
                text = _correct_app_names(_clean_transcript(result.get("text", "")))
                if text and not re.search(r"[a-zA-Z0-9]", text):
                    text = ""
                return {"text": text, "model": "sensevoice-dsh", "engine": "dsh",
                        "ms": result.get("ms")}
            except Exception as exc:  # noqa: BLE001
                print(f"dsh stt failed: {exc}", flush=True)
            finally:
                if prepared != wav:
                    try:
                        prepared.unlink()
                    except OSError:
                        pass
        prepared = normalize_wav(wav)
        try:
            try:
                import mlx_whisper
            except ImportError as exc:
                raise RuntimeError(
                    "no STT engine available: DSH worker failed and mlx_whisper "
                    "is not installed") from exc

            with self._lock:
                result = mlx_whisper.transcribe(
                    str(prepared),
                    path_or_hf_repo=self.model,
                    language="en",
                    condition_on_previous_text=False,
                    no_speech_threshold=0.6,
                    logprob_threshold=-1.0,
                    compression_ratio_threshold=2.2,
                    verbose=None,
                )
            text = (result.get("text") or "").strip()
            return {"text": _correct_app_names(_clean_transcript(text)),
                    "model": self.model, "engine": "whisper"}
        finally:
            if prepared != wav:
                try:
                    prepared.unlink()
                except OSError:
                    pass


class DshVoice:
    """A persistent DSH headless session. Resumes with --session-id."""

    def __init__(self) -> None:
        self.key = read_key()
        self.lock = threading.Lock()
        self.session_id = self._load_session()

    def _load_session(self) -> str:
        try:
            return json.loads(SESSION_FILE.read_text(encoding="utf-8")).get("sessionId", "")
        except (OSError, ValueError):
            return ""

    def _save_session(self, sid: str) -> None:
        self.session_id = sid
        DSH_HOME.mkdir(parents=True, exist_ok=True)
        SESSION_FILE.write_text(json.dumps({"sessionId": sid, "updated": time.time()}),
                                encoding="utf-8")
        os.chmod(SESSION_FILE, 0o600)

    def ask(self, utterance: str) -> dict:
        try:
            tv_memory.log_event("command", query=utterance)
        except Exception:
            pass
        habits = ""
        try:
            habits = tv_memory.taste_text()
        except Exception:
            pass
        context = ""
        try:
            context = (Path(__file__).resolve().parent / "tv-apps.json").read_text(encoding="utf-8")
            context = context[:6000]
        except Exception:
            pass
        prompt = (f"{BRIEF}\n\n"
                  f"REPO: {ROOT} — the shell may start in the workspace parent; "
                  f"cd {ROOT} first or use absolute paths like "
                  f"`python3 {ROOT}/host/dshtv.py state`.\n\n"
                  f"## Household taste (learned locally)\n{habits}\n\n"
                  f"## App catalog (truncated JSON; full file host/tv-apps.json)\n{context}\n\n"
                  f"Transcript: {utterance}")
        cmd = ["dsh", "--profile", "headless", "--json"]
        if self.session_id:
            cmd += ["--session-id", self.session_id]
        cmd.append(prompt)
        env = dict(os.environ)
        env.update({"DSH_HOME": str(DSH_HOME), "DEEPSEEK_API_KEY": self.key})
        with self.lock:
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  env=env, cwd=str(ROOT),
                                  timeout=MAX_TURN_SECONDS)
        sid, final, error = self.session_id, "", ""
        for line in (proc.stdout or "").splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if event.get("type") == "session" and event.get("sessionId"):
                sid = event["sessionId"]
            elif event.get("type") == "final":
                final = event.get("text") or ""
            elif event.get("type") == "status" and event.get("phase") == "turn_end":
                reason = (event.get("reason") or {})
                if reason.get("kind") == "error":
                    error = str((reason.get("error") or {}).get("message") or "dsh turn failed")
        if sid and sid != self.session_id:
            self._save_session(sid)
        if error and not final:
            final = "Sorry, my brain is not connected right now."

        installed = apply_pending_catalogs()
        reply = final.strip()
        if installed:
            ok_rows = [ln for ln in installed if ln.startswith("OK")]
            if ok_rows and reply:
                names = []
                for ln in ok_rows:
                    m = re.search(r'name="([^"]+)"', ln)
                    count = re.search(r"picks=(\d+)", ln)
                    if m:
                        names.append(m.group(1) + (f", {count.group(1)} titles" if count else ""))
                if names:
                    reply = f"{reply} ({'; '.join(names)} is live.)"
            elif not ok_rows:
                reply = f"{(reply + ' ') if reply else ''}The catalog did not install: {installed[-1]}"
        return {"reply": reply, "sessionId": sid, "installed": installed,
                "stderr": (proc.stderr or "").strip()[-400:]}


def apply_pending_catalogs() -> list[str]:
    """Install anything the assistant drafted, and return one factual line per file.

    This is the whole reason the assistant cannot be trusted to announce its own success: it
    cannot see the live store at all. So the applying happens here, and the result is appended
    to whatever it said.
    """
    results: list[str] = []
    if not PENDING_CATALOGS.is_dir() or not INSTALLER.is_file():
        return results
    for path in sorted(PENDING_CATALOGS.glob("*.json")):
        try:
            proc = subprocess.run([sys.executable, str(INSTALLER), str(path)],
                                  capture_output=True, text=True, timeout=180)
        except Exception as exc:  # noqa: BLE001 - never fail the turn on the installer
            results.append(f"installer-error({exc.__class__.__name__})")
            continue
        lines = [ln.strip() for ln in (proc.stdout or "").splitlines() if ln.strip()]
        verdict = lines[-1] if lines else f"installer-exit-{proc.returncode}"
        results.append(verdict)
        done_dir = PENDING_CATALOGS / "done"
        done_dir.mkdir(exist_ok=True)
        try:
            path.rename(done_dir / path.name)
        except OSError:
            path.unlink(missing_ok=True)
    return results


def tv_health() -> dict:
    try:
        cfg = json.loads(TV_CONFIG.read_text(encoding="utf-8"))
        host, port = cfg.get("host"), int(cfg.get("port") or 8765)
        import urllib.request
        with urllib.request.urlopen(f"http://{host}:{port}/ping", timeout=3) as r:
            return {"ok": json.loads(r.read().decode()).get("ok", False),
                    "host": host, "port": port}
    except Exception as exc:  # noqa: BLE001 - health is best effort
        return {"ok": False, "error": str(exc)}


class Handler(BaseHTTPRequestHandler):
    server_version = "whale-voice"
    sys_version = ""
    protocol_version = "HTTP/1.1"

    transcriber: Transcriber
    brain: DshVoice
    token: str

    def log_message(self, fmt, *args):
        eprint("[%s] %s" % (time.strftime("%H:%M:%S"), fmt % args))

    def _auth(self) -> bool:
        if self.headers.get("X-Whale-Token") == self.token:
            return True
        from urllib.parse import urlparse, parse_qs
        q = parse_qs(urlparse(self.path).query)
        return (q.get("token") or [""])[0] == self.token

    def _json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def _pair_get(self, path: str) -> None:
        from urllib.parse import urlparse, parse_qs
        q = parse_qs(urlparse(self.path).query)
        ip = lan_ip()
        port = self.server.server_address[1]
        if path == "/pair/new":
            pid, code = new_pair(self.client_address[0])
            url = f"http://{ip}:{port}/pair?id={pid}"
            return self._json(200, {"ok": True, "id": pid, "code": code,
                                    "url": url, "qr": qr_png_b64(url),
                                    "expiresIn": PAIR_TTL_SECONDS})
        if path == "/pair/status":
            pid = (q.get("id") or [""])[0]
            entry = PAIRS.get(pid)
            if not entry or time.time() - entry["created"] > PAIR_TTL_SECONDS:
                return self._json(404, {"ok": False, "error": "expired"})
            if entry["approved"]:
                return self._json(200, {"ok": True, "approved": True,
                                        "config": pair_config(port)})
            return self._json(200, {"ok": True, "approved": False})
        if path == "/pair":
            pid = (q.get("id") or [""])[0]
            entry = PAIRS.get(pid)
            if not entry or time.time() - entry["created"] > PAIR_TTL_SECONDS:
                return self._html(404, "<h1>Pairing link expired</h1><p>Open Whale-chan on the TV again.</p>")
            if entry["approved"]:
                return self._html(200, "<h1>TV paired</h1><p>You can close this page.</p>")
            return self._html(200,
                "<h1>Pair this TV with Whale-chan?</h1>"
                f"<p>Confirm the TV shows the code <b>{entry['code']}</b>.</p>"
                f"<form method=post action=/pair/approve><input type=hidden name=id value='{pid}'>"
                "<button type=submit style='font-size:1.4em;padding:.6em 1.2em'>Approve TV</button></form>")
        return self._json(404, {"ok": False, "error": "not found"})

    def _pair_approve(self) -> None:
        pid, parsed = self._pair_id_from_body()
        json_reply = self._wants_json()
        if not parsed:
            return self._pair_error(400, "bad request body", json_reply)
        entry = PAIRS.get(pid)
        if not entry or time.time() - entry["created"] > PAIR_TTL_SECONDS:
            return self._pair_error(404, "expired", json_reply)
        entry["approved"] = True
        if json_reply:
            return self._json(200, {"ok": True, "approved": True, "id": pid})
        return self._html(200, "<h1>Approved</h1><p>The TV will pick up its settings now.</p>")

    def _pair_deny(self) -> None:
        pid, parsed = self._pair_id_from_body()
        json_reply = self._wants_json()
        if not parsed:
            return self._pair_error(400, "bad request body", json_reply)
        if PAIRS.pop(pid, None) is None:
            return self._pair_error(404, "expired", json_reply)
        if json_reply:
            return self._json(200, {"ok": True, "denied": True, "id": pid})
        return self._html(200, "<h1>Denied</h1><p>This pairing request was cancelled.</p>")

    def _pair_pending(self) -> None:
        """Token-authenticated list for the DSH GUI (never on the public /pair page)."""
        return self._json(200, {"ok": True, "pending": pending_pairs(),
                                "now": int(time.time() * 1000)})

    def _pair_error(self, code: int, error: str, json_reply: bool) -> None:
        if json_reply:
            return self._json(code, {"ok": False, "error": error})
        return self._html(code, f"<h1>{error.capitalize()}</h1>")

    def _request_body(self) -> bytes:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return b""
        return self.rfile.read(length)

    def _wants_json(self) -> bool:
        """True when the caller asked for machine-readable output (GUI, curl, scripts)."""
        accept = (self.headers.get("Accept") or "").lower()
        ctype = (self.headers.get("Content-Type") or "").lower()
        return "application/json" in accept or "application/json" in ctype

    def _pair_id_from_body(self) -> tuple[str, bool]:
        """Read the pairing id from a JSON `{id}` body or a form field `id`."""
        raw = self._request_body()
        ctype = (self.headers.get("Content-Type") or "").lower()
        if "application/json" in ctype:
            try:
                data = json.loads(raw.decode("utf-8") or "{}")
            except (ValueError, UnicodeDecodeError):
                return "", False
            if not isinstance(data, dict):
                return "", False
            return str(data.get("id") or "").strip(), True
        from urllib.parse import parse_qs
        fields = parse_qs(raw.decode("utf-8", "replace"))
        return (fields.get("id") or [""])[0].strip(), True

    def _html(self, code: int, body: str) -> None:
        data = ("<!doctype html><meta name=viewport content='width=device-width,initial-scale=1'>"
                "<style>body{font-family:system-ui;margin:3rem auto;max-width:32rem;padding:0 1rem}</style>"
                + body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/pair/pending":
            if not self._auth():
                return self._json(401, {"ok": False, "error": "unauthorized"})
            return self._pair_pending()
        if path.startswith("/pair"):
            return self._pair_get(path)
        if not self._auth():
            return self._json(401, {"ok": False, "error": "unauthorized"})
        if self.path.startswith("/health"):
            return self._json(200, {"ok": True, "sessionId": self.brain.session_id,
                                    "tv": tv_health(), "now": int(time.time() * 1000)})
        if path == "/apps":
            try:
                catalog = json.loads((Path(__file__).resolve().parent / "tv-apps.json")
                                     .read_text(encoding="utf-8"))
                return self._json(200, {"ok": True, **catalog})
            except Exception as exc:  # noqa: BLE001
                return self._json(500, {"ok": False, "error": str(exc)})
        if path == "/memory/summary":
            try:
                return self._json(200, {"ok": True, "summary": tv_memory.summary()})
            except Exception as exc:  # noqa: BLE001
                return self._json(500, {"ok": False, "error": str(exc)})
        if path == "/suggest":
            try:
                return self._json(200, {"ok": True, "suggestion": tv_memory.latest_suggestion()})
            except Exception as exc:  # noqa: BLE001
                return self._json(500, {"ok": False, "error": str(exc)})
        return self._json(404, {"ok": False, "error": "not found"})

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if path == "/pair/approve":
            return self._pair_approve()
        if path == "/pair/deny":
            return self._pair_deny()
        if not self._auth():
            return self._json(401, {"ok": False, "error": "unauthorized"})
        if path == "/feedback":
            length = int(self.headers.get("Content-Length") or 0)
            try:
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                subject = str(body.get("subject") or "").strip()
                verdict = str(body.get("verdict") or "").strip()
            except Exception:
                return self._json(400, {"ok": False, "error": "bad json"})
            if not subject or verdict not in ("like", "dislike", "not_interested", "watched"):
                return self._json(400, {"ok": False, "error": "subject/verdict required"})
            tv_memory.feedback(subject, verdict, body.get("detail"))
            return self._json(200, {"ok": True})
        if path == "/suggest/generate":
            length = int(self.headers.get("Content-Length") or 0)
            try:
                body = json.loads(self.rfile.read(length).decode("utf-8"))
            except Exception:
                body = {}
            topic = str(body.get("topic") or "something new and talked about this week")
            proc = subprocess.run(
                [sys.executable, str(Path(__file__).resolve().parent / "suggest.py"),
                 "--topic", topic],
                capture_output=True, text=True, cwd=str(ROOT), timeout=240)
            try:
                out = json.loads(proc.stdout.strip().splitlines()[-1])
            except Exception:
                out = {"ok": False, "error": proc.stderr[-400:] or "suggest failed"}
            return self._json(200 if out.get("ok") else 502, out)
        if self.path.startswith("/ask"):
            length = int(self.headers.get("Content-Length") or 0)
            try:
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                text = str(body.get("text") or "").strip()
            except Exception:
                return self._json(400, {"ok": False, "error": "bad json"})
            if not text:
                return self._json(400, {"ok": False, "error": "empty text"})
            try:
                brain = self.brain.ask(text)
                return self._json(200, {"ok": True, "reply": brain["reply"],
                                        "sessionId": brain.get("sessionId")})
            except subprocess.TimeoutExpired:
                return self._json(504, {"ok": False, "error": "dsh turn timed out"})
        if not self.path.startswith("/voice") and not self.path.startswith("/stt"):
            return self._json(404, {"ok": False, "error": "not found"})
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 44 or length > 8_000_000:
            return self._json(400, {"ok": False, "error": "bad audio length"})
        audio = self.rfile.read(length)
        started = time.time()
        tmp = Path(tempfile.mkstemp(prefix="whale-mic-", suffix=".wav")[1])
        tmp.write_bytes(audio)
        try:
            stt = self.transcriber.transcribe(tmp)
            text = (stt.get("text") or "").strip()
            if self.path.startswith("/stt"):
                return self._json(200, {"ok": True, "transcript": text})
            if len(re.sub(r"[^a-z0-9]", "", text.lower())) < 2:
                return self._json(200, {"ok": True, "transcript": "", "reply": "",
                                        "note": "empty transcript"})
            brain = self.brain.ask(text)
            return self._json(200, {"ok": True, "transcript": text,
                                    "reply": brain["reply"],
                                    "sessionId": brain.get("sessionId"),
                                    "ms": int((time.time() - started) * 1000)})
        except subprocess.TimeoutExpired:
            return self._json(504, {"ok": False, "error": "dsh turn timed out"})
        except Exception as exc:  # noqa: BLE001
            return self._json(500, {"ok": False, "error": str(exc)})
        finally:
            try:
                tmp.unlink()
            except OSError:
                pass


def main() -> int:
    ap = argparse.ArgumentParser(description="Whale-chan voice daemon")
    ap.add_argument("--serve", action="store_true")
    ap.add_argument("--once", metavar="WAV")
    ap.add_argument("--port", type=int, default=8766)
    ap.add_argument("--bind", default="0.0.0.0")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--stt", choices=["dsh", "whisper"], default="dsh")
    ap.add_argument("--stt-model-dir", default=None)
    args = ap.parse_args()

    transcriber = Transcriber(args.model, engine=args.stt,
                             dsh_model_dir=args.stt_model_dir)
    brain = DshVoice()

    if args.once:
        stt = transcriber.transcribe(Path(args.once))
        text = (stt.get("text") or "").strip()
        print(json.dumps({"transcript": text, "model": stt.get("model")}, ensure_ascii=False))
        if text:
            print(json.dumps({"reply": brain.ask(text)["reply"]}, ensure_ascii=False))
        return 0

    token = read_token()
    Handler.transcriber = transcriber
    Handler.brain = brain
    Handler.token = token
    server = ThreadingHTTPServer((args.bind, args.port), Handler)
    eprint(f"whale-voice listening on {args.bind}:{args.port} (token required)")
    eprint(f"  session: {brain.session_id or '(new on first utterance)'}")
    eprint(f"  tv: {tv_health()}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
