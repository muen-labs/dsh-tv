#!/usr/bin/env python3
"""dshtv - drive the onn. 4K Pro (Google TV) from this Mac mini / DeepSeek Harness.

The onn. box runs the DSH TV Bridge APK (com.jp.dshtv), a small HTTP server on
the LAN.  This client talks to it over HTTP.  ADB-over-TCP is kept as a fallback
for the few things an app cannot do (power/wake, MENU on some apps) and for
first-time setup.

Transport selection:
  app  - the bridge APK's LAN HTTP API (no adb needed at runtime)
  adb  - the always-on ADB channel (requires the box's 5555 to be authorised)
  auto - try app, fall back to adb for operations adb can do (default)

Config file:  dshtv/config.json
  {"host": "192.168.4.55", "port": 8765, "token": "", "serial": "192.168.4.55:5555"}

Exit codes: 0 ok, 1 runtime failure, 2 usage/config problem.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib import error as urlerror
from urllib import parse, request

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = Path(os.environ.get("DSHTV_CONFIG", ROOT / "host" / "config.json"))
CAPTURE_DIR = ROOT / "dshtv" / "captures"
APK_PATH = ROOT / "android" / "tv-assistant" / "TVAssistant.apk"
APP_PACKAGE = "com.jp.dshtv"
APP_ACTIVITY = f"{APP_PACKAGE}/.MainActivity"
ACCESSIBILITY_COMPONENT = f"{APP_PACKAGE}/{APP_PACKAGE}.KeyService"
REMOTE_DIR = ROOT / "dshtv" / "remote"
REMOTE_VENV_PY = ROOT / "dshtv" / "venv" / "bin" / "python"
REMOTE_VOICE_SCRIPT = ROOT / "dshtv" / "tv_remote_voice.py"
TRANSCRIBE_SCRIPT = ROOT / "dshtv" / "tv_transcribe.py"
DEFAULT_STT_MODEL = "mlx-community/whisper-base.en-mlx"
MAC_MIC_DEVICE = os.environ.get("DSHTV_MAC_MIC", ":0")
DEFAULT_PORT = 8765

ADB_KEYCODES = {
    "up": 19,
    "down": 20,
    "left": 21,
    "right": 22,
    "ok": 23,
    "select": 23,
    "center": 23,
    "back": 4,
    "home": 3,
    "recents": 187,
    "menu": 82,
    "playpause": 85,
    "play": 126,
    "pause": 127,
    "next": 87,
    "prev": 88,
    "rewind": 89,
    "fastforward": 90,
    "volup": 24,
    "voldown": 25,
    "mute": 164,
    "power": 26,
    "sleep": 223,
    "wakeup": 224,
    "info": 165,
}


class DshtvError(RuntimeError):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


# ---------------------------------------------------------------------------
# small utilities
# ---------------------------------------------------------------------------

def eprint(*args: object) -> None:
    print(*args, file=sys.stderr)


def adb_bin() -> str:
    env = os.environ.get("DSHTV_ADB")
    if env:
        return env
    env = os.environ.get("DSHTV_ADB")
    if env and Path(env).exists():
        return env
    import shutil
    found = shutil.which("adb")
    if found:
        return found
    local = ROOT / ".tools" / "platform-tools" / "adb"
    if local.exists():
        return str(local)
    found = shutil.which("adb")
    if not found:
        raise DshtvError(
            "adb not found. Expected .tools/platform-tools/adb in the workspace "
            "or set DSHTV_ADB."
        )
    return found


def run_adb(args: list[str], serial: str | None = None, timeout: int = 25,
            binary: bool = False) -> subprocess.CompletedProcess:
    cmd = [adb_bin()]
    if serial:
        cmd += ["-s", serial]
    cmd += args
    try:
        return subprocess.run(cmd, capture_output=True, timeout=timeout,
                              check=False, text=not binary)
    except subprocess.TimeoutExpired as exc:
        raise DshtvError(f"adb timed out: {' '.join(cmd)}") from exc


def adb_text(args: list[str], serial: str | None = None, timeout: int = 25) -> str:
    proc = run_adb(args, serial=serial, timeout=timeout)
    out = (proc.stdout or "") + (proc.stderr or "")
    return out.strip()


def adb_devices() -> list[dict]:
    """Parse `adb devices -l` into dicts with serial/model/state."""
    proc = run_adb(["devices", "-l"], timeout=15)
    out = (proc.stdout or "") + (proc.stderr or "")
    devices = []
    for line in out.splitlines():
        line = line.strip()
        if not line or line.startswith("List of devices") or line.startswith("*"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        serial, state = parts[0], parts[1]
        if state not in ("device", "unauthorized", "offline"):
            continue
        model = ""
        for part in parts:
            if part.startswith("model:"):
                model = part.split(":", 1)[1]
        devices.append({"serial": serial, "state": state, "model": model})
    return devices


def is_onn(device: dict) -> bool:
    hay = (device.get("model") or "").lower()
    serial = (device.get("serial") or "").lower()
    return "onn" in hay or "streaming_device" in hay or "streaming device" in hay


def device_ip(serial: str) -> str:
    """Return the LAN IPv4 of a device given a USB serial or ip:port serial."""
    if re.match(r"^\d+\.\d+\.\d+\.\d+:\d+$", serial):
        return serial.split(":", 1)[0]
    txt = adb_text(["shell", "ip", "-f", "inet", "addr", "show"], serial=serial, timeout=15)
    ips = re.findall(r"inet\s+(\d+\.\d+\.\d+\.\d+)", txt)
    ips = [ip for ip in ips if not ip.startswith("127.")]
    for preferred in ("wlan0", "eth0"):
        section = re.search(preferred + r".*?(?=^\d+:|\Z)", txt, re.S | re.M)
        if section:
            match = re.search(r"inet\s+(\d+\.\d+\.\d+\.\d+)", section.group(0))
            if match:
                return match.group(1)
    return ips[0] if ips else ""


def pick_onn_device(prefer: str | None = None) -> dict:
    devices = adb_devices()
    if prefer:
        for dev in devices:
            if dev["serial"] == prefer or dev["serial"].startswith(prefer + ":"):
                return dev
        # allow a bare IP to mean ip:5555
        if re.match(r"^\d+\.\d+\.\d+\.\d+$", prefer):
            return {"serial": f"{prefer}:5555", "state": "device", "model": ""}
        raise DshtvError(f"device {prefer!r} not in adb devices: {devices}")
    candidates = [dev for dev in devices if is_onn(dev)]
    ready = [dev for dev in candidates if dev["state"] == "device"]
    if ready:
        return ready[0]
    if candidates:
        raise DshtvError(
            f"onn device found but state={candidates[0]['state']}; accept the "
            "USB-debugging prompt on the TV (or run: dshtv adb-connect <ip>)."
        )
    raise DshtvError(
        "no onn device in adb devices. Is ADB debugging enabled and the Mac "
        f"authorised? devices={devices}"
    )


# ---------------------------------------------------------------------------
# config
# ---------------------------------------------------------------------------

def default_config() -> dict:
    return {"host": "", "port": DEFAULT_PORT, "token": "", "serial": ""}


def load_config() -> dict:
    cfg = default_config()
    if CONFIG_PATH.exists():
        try:
            cfg.update(json.loads(CONFIG_PATH.read_text()))
        except Exception as exc:
            raise DshtvError(f"bad config {CONFIG_PATH}: {exc}") from exc
    if os.environ.get("DSHTV_HOST"):
        cfg["host"] = os.environ["DSHTV_HOST"]
    if os.environ.get("DSHTV_PORT"):
        cfg["port"] = int(os.environ["DSHTV_PORT"])
    if os.environ.get("DSHTV_TOKEN"):
        cfg["token"] = os.environ["DSHTV_TOKEN"]
    return cfg


def save_config(cfg: dict) -> Path:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2) + "\n")
    return CONFIG_PATH


def resolve_target(cfg: dict, allow_discovery: bool = True) -> dict:
    """Fill host/port/serial, discovering the onn over adb if needed."""
    cfg.setdefault("port", DEFAULT_PORT)
    if cfg.get("host"):
        if not cfg.get("serial"):
            cfg["serial"] = f"{cfg['host']}:5555"
        return cfg
    if not allow_discovery:
        raise DshtvError("no host configured (run: dshtv discover --write)")
    dev = pick_onn_device(cfg.get("serial") or None)
    cfg["serial"] = dev["serial"]
    cfg["host"] = device_ip(dev["serial"])
    if not cfg["host"]:
        raise DshtvError(f"could not determine IP for {dev['serial']}")
    return cfg


# ---------------------------------------------------------------------------
# app transport (bridge APK HTTP API)
# ---------------------------------------------------------------------------

class Client:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.host = cfg["host"]
        self.port = int(cfg.get("port") or DEFAULT_PORT)
        self.token = cfg.get("token") or ""
        self.serial = cfg.get("serial") or f"{self.host}:5555"

    # -- low level ---------------------------------------------------------
    def _url(self, path: str, params: dict | None = None) -> str:
        clean = {k: v for k, v in (params or {}).items() if v is not None}
        query = parse.urlencode(clean, doseq=True, safe=":/")
        return f"http://{self.host}:{self.port}{path}" + (f"?{query}" if query else "")

    def raw(self, path: str, params: dict | None = None,
            timeout: float = 10.0) -> bytes:
        headers = {"Accept": "*/*"}
        if self.token:
            headers["X-DSH-Token"] = self.token
        req = request.Request(self._url(path, params), headers=headers, method="GET")
        try:
            with request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urlerror.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")[:500]
            raise DshtvError(f"{path}: HTTP {exc.code}: {body}", status=exc.code) from exc
        except Exception as exc:
            raise DshtvError(f"{path}: cannot reach {self.host}:{self.port}: {exc}") from exc

    def json(self, path: str, params: dict | None = None,
             timeout: float = 10.0) -> dict:
        data = self.raw(path, params, timeout=timeout)
        try:
            obj = json.loads(data.decode("utf-8", "replace"))
        except Exception as exc:
            raise DshtvError(f"{path}: invalid JSON: {data[:200]!r}") from exc
        if isinstance(obj, dict) and obj.get("ok") is False:
            raise DshtvError(f"{path}: {obj.get('error') or obj}", status=502)
        return obj

    # -- endpoints ---------------------------------------------------------
    def ping(self) -> dict:
        return self.json("/ping", timeout=4)

    def info(self) -> dict:
        return self.json("/info")

    def state(self) -> dict:
        return self.json("/state")

    def key(self, code: str, repeat: int = 1) -> dict:
        return self.json("/key", {"code": code, "n": repeat})

    def text(self, text: str, enter: bool = False) -> dict:
        return self.json("/text", {"q": text, "enter": 1 if enter else None})

    def launch(self, app: str | None = None, package: str | None = None,
               url: str | None = None) -> dict:
        return self.json("/launch", {"app": app, "pkg": package, "url": url})

    def apps(self) -> dict:
        return self.json("/apps")

    def screenshot(self) -> bytes:
        return self.raw("/screenshot", {"fmt": "jpeg", "quality": 85}, timeout=20)

    def voice(self) -> dict:
        return self.json("/voice", timeout=15)

    def speak(self, text: str) -> dict:
        return self.json("/speak", {"text": text})

    def mic(self, seconds: int = 5, source: str = "voice") -> bytes:
        return self.raw("/mic", {"seconds": seconds, "source": source},
                        timeout=seconds + 20)

    def volume(self, level: int | None = None, delta: int | None = None) -> dict:
        return self.json("/volume", {"level": level, "delta": delta})


# ---------------------------------------------------------------------------
# adb transport (fallback / setup)
# ---------------------------------------------------------------------------

def adb_key(code: str, repeat: int = 1, serial: str | None = None) -> dict:
    keycode = ADB_KEYCODES.get(code)
    if keycode is None:
        raise DshtvError(f"no adb keycode mapped for {code!r}")
    for _ in range(max(1, min(repeat, 20))):
        adb_text(["shell", "input", "keyevent", str(keycode)], serial=serial)
        if repeat > 1:
            time.sleep(0.06)
    return {"ok": True, "via": "adb", "code": code, "n": repeat, "keycode": keycode}


def adb_connect(host: str, port: int = 5555) -> dict:
    out = adb_text(["connect", f"{host}:{port}"], timeout=15)
    if "connected" not in out.lower() and "already" not in out.lower():
        raise DshtvError(f"adb connect failed: {out}")
    return {"ok": True, "output": out}


def adb_launch(package: str, serial: str | None = None) -> dict:
    # LEANBACK_LAUNCHER first, then plain LAUNCHER; -W waits for launch.
    cmds = [
        ["shell", "am", "start", "-W", "-a", "android.intent.action.MAIN",
         "-c", "android.intent.category.LEANBACK_LAUNCHER", "-p", package],
        ["shell", "am", "start", "-W", "-a", "android.intent.action.MAIN",
         "-c", "android.intent.category.LAUNCHER", "-p", package],
    ]
    last = ""
    for cmd in cmds:
        out = adb_text(cmd, serial=serial)
        last = out
        if "Error" not in out and "Exception" not in out and "Warning" not in out:
            return {"ok": True, "via": "adb", "package": package, "output": out}
    raise DshtvError(f"adb launch failed for {package}: {last}")


def adb_text_input(text: str, enter: bool = False, serial: str | None = None) -> dict:
    # `input text` needs spaces escaped as %s and shell metacharacters quoted.
    escaped = text.replace(" ", "%s").replace("'", "\\'")
    adb_text(["shell", "input", "text", escaped], serial=serial)
    if enter:
        adb_text(["shell", "input", "keyevent", "66"], serial=serial)
    return {"ok": True, "via": "adb"}


def adb_voice(serial: str | None = None) -> dict:
    # KEYCODE_VOICE_ASSIST (231) is what the Google TV remote's mic button sends.
    adb_text(["shell", "input", "keyevent", "231"], serial=serial)
    return {"ok": True, "via": "adb", "note": "Assistant voice input triggered on the TV"}


def adb_screenshot(serial: str | None = None) -> bytes:
    proc = run_adb(["exec-out", "screencap", "-p"], serial=serial, timeout=30, binary=True)
    data = proc.stdout or b""
    if not data:
        raise DshtvError("adb screencap returned no data")
    return data


def adb_speak(text: str, serial: str | None = None) -> dict:
    # No TTS shell command exists; use the app endpoint only.
    raise DshtvError("speak requires the app transport (TTS is app-side)")


def adb_info(serial: str | None = None) -> dict:
    props = {}
    raw = adb_text(["shell", "getprop"], serial=serial)
    for line in raw.splitlines():
        match = re.match(r"\[([^\]]+)\]: \[([^\]]*)\]", line.strip())
        if match:
            props[match.group(1)] = match.group(2)
    ip = ""
    if serial:
        ip = device_ip(serial)
    return {
        "ok": True,
        "via": "adb",
        "model": props.get("ro.product.model"),
        "manufacturer": props.get("ro.product.manufacturer"),
        "release": props.get("ro.build.version.release"),
        "sdk": props.get("ro.build.version.sdk"),
        "fingerprint": props.get("ro.build.fingerprint"),
        "ip": ip,
        "serial": serial,
    }


def adb_save(serial: str | None = None) -> dict:
    path = save_bytes(adb_screenshot(serial), None, "tv.png")
    return {"ok": True, "via": "adb", "path": str(path)}


# ---------------------------------------------------------------------------
# setup / doctor / discovery
# ---------------------------------------------------------------------------

def accessibility_services(serial: str) -> str:
    return adb_text(["shell", "settings", "get", "secure",
                     "enabled_accessibility_services"], serial=serial).strip()


def append_accessibility(serial: str, component: str = ACCESSIBILITY_COMPONENT) -> dict:
    current = accessibility_services(serial)
    parts = [p for p in current.split(":") if p]
    already = component in parts
    if not already:
        parts.append(component)
        adb_text(["shell", "settings", "put", "secure",
                  "enabled_accessibility_services", ":".join(parts)], serial=serial)
    adb_text(["shell", "settings", "put", "secure", "accessibility_enabled", "1"], serial=serial)
    return {"ok": True, "already_enabled": already, "services": parts}


def remove_accessibility(serial: str, component: str = ACCESSIBILITY_COMPONENT) -> dict:
    current = accessibility_services(serial)
    parts = [p for p in current.split(":") if p and p != component]
    adb_text(["shell", "settings", "put", "secure",
              "enabled_accessibility_services", ":".join(parts)], serial=serial)
    return {"ok": True, "services": parts}


def cmd_discover(args: argparse.Namespace) -> dict:
    devices = adb_devices()
    result: dict = {"devices": devices, "chosen": None, "ping": None}
    cfg = load_config()
    try:
        dev = pick_onn_device(args.serial)
        cfg["serial"] = dev["serial"]
        cfg["host"] = device_ip(dev["serial"])
        cfg["port"] = int(args.port or cfg.get("port") or DEFAULT_PORT)
        result["chosen"] = {"serial": cfg["serial"], "model": dev.get("model")}
        try:
            result["ping"] = Client(cfg).ping()
        except DshtvError as exc:
            result["ping"] = {"ok": False, "error": str(exc)}
        if args.write and cfg["host"]:
            result["config"] = str(save_config(cfg))
    except DshtvError as exc:
        result["error"] = str(exc)
    return result


def cmd_setup(args: argparse.Namespace) -> dict:
    cfg = load_config()
    host = args.host or cfg.get("host")
    if args.ip:
        host = args.ip
    steps: list[dict] = []

    if host:
        cfg["host"] = host
        cfg["serial"] = f"{host}:5555" if ":" not in host else host
        try:
            steps.append({"step": "adb-connect", **adb_connect(host)})
        except DshtvError as exc:
            steps.append({"step": "adb-connect", "ok": False, "error": str(exc)})

    dev = pick_onn_device(args.serial or cfg.get("serial") or None)
    cfg["serial"] = dev["serial"]
    cfg["host"] = cfg.get("host") or device_ip(dev["serial"])
    if not cfg["host"]:
        raise DshtvError("could not determine the onn's LAN IP")
    steps.append({"step": "device", "serial": dev["serial"], "model": dev.get("model"),
                  "host": cfg["host"]})

    port = int(args.port or cfg.get("port") or DEFAULT_PORT)
    cfg["port"] = port
    if args.token is not None:
        cfg["token"] = args.token

    apk = Path(args.apk) if args.apk else APK_PATH
    if not apk.exists():
        raise DshtvError(f"APK not found: {apk} (build it in .tools/dshtv-app first)")
    install = adb_text(["install", "-r", "-g", str(apk)], serial=cfg["serial"], timeout=120)
    if "Success" not in install:
        raise DshtvError(f"install failed: {install}")
    steps.append({"step": "install", "ok": True})

    grant = adb_text(["shell", "pm", "grant", APP_PACKAGE,
                      "android.permission.RECORD_AUDIO"], serial=cfg["serial"])
    steps.append({"step": "grant-mic", "output": grant.strip()})

    try:
        steps.append({"step": "accessibility",
                      **append_accessibility(cfg["serial"])})
    except DshtvError as exc:
        steps.append({"step": "accessibility", "ok": False, "error": str(exc)})

    start_cmd = ["shell", "am", "start", "-n", APP_ACTIVITY,
                 "--ez", "start_service", "true"]
    if cfg.get("token"):
        start_cmd += ["--es", "set_token", cfg["token"]]
    start_cmd += ["--ei", "set_port", str(port)]
    start = adb_text(start_cmd, serial=cfg["serial"])
    steps.append({"step": "start", "output": start.strip()})

    save_config(cfg)
    ping = None
    for _ in range(20):
        try:
            ping = Client(cfg).ping()
            break
        except DshtvError:
            time.sleep(0.5)
    steps.append({"step": "ping", "ok": ping is not None, "response": ping})
    return {"ok": ping is not None, "config": cfg, "steps": steps}


def cmd_doctor(args: argparse.Namespace) -> dict:
    cfg = load_config()
    out: dict = {"config": cfg, "adb_devices": adb_devices(), "serial": None}
    try:
        thr = resolve_target(cfg)
        out["serial"] = thr["serial"]
        out["app"] = {"present": False}
        pm_path = adb_text(["shell", "pm", "path", APP_PACKAGE], serial=thr["serial"])
        out["app"]["present"] = "package:" in pm_path
        out["app"]["path"] = pm_path.strip()
        out["accessibility_services"] = accessibility_services(thr["serial"])
        out["accessibility_enabled"] = adb_text(
            ["shell", "settings", "get", "secure", "accessibility_enabled"],
            serial=thr["serial"]).strip()
        out["mic_granted"] = bool(re.search(
            r"android\.permission\.RECORD_AUDIO:\s*granted=true",
            adb_text(["shell", "dumpsys", "package", APP_PACKAGE],
                     serial=thr["serial"])))
        try:
            out["ping"] = Client(thr).ping()
            out["info"] = Client(thr).info()
            out["state"] = Client(thr).state()
            if isinstance(out.get("info"), dict) and "micPermission" in out["info"]:
                out["mic_granted"] = bool(out["info"]["micPermission"])
        except DshtvError as exc:
            out["ping"] = {"ok": False, "error": str(exc)}
    except DshtvError as exc:
        out["error"] = str(exc)
    return out


# ---------------------------------------------------------------------------
# output helpers
# ---------------------------------------------------------------------------

def save_bytes(data: bytes, out: str | None, default_name: str) -> Path:
    if out:
        path = Path(out).expanduser()
    else:
        CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
        path = CAPTURE_DIR / default_name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def emit(obj: object) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def make_client(args: argparse.Namespace) -> Client:
    cfg = load_config()
    if getattr(args, "host", None):
        cfg["host"] = args.host
        cfg["serial"] = f"{args.host}:5555"
    if getattr(args, "port", None):
        cfg["port"] = int(args.port)
    if getattr(args, "token", None) is not None:
        cfg["token"] = args.token
    cfg = resolve_target(cfg)
    return Client(cfg)


def transport(args: argparse.Namespace) -> str:
    return getattr(args, "via", "auto")


def app_failed(exc: Exception) -> bool:
    if isinstance(exc, DshtvError):
        # 501 = app does not support this op; everything else is transport/UI.
        return exc.status == 501
    return True


# ---------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------

def cmd_ping(args: argparse.Namespace) -> dict:
    if transport(args) == "adb":
        cfg = load_config()
        cfg = resolve_target(cfg)
        return adb_info(cfg["serial"])
    return make_client(args).ping()


def cmd_info(args: argparse.Namespace) -> dict:
    try:
        return make_client(args).info()
    except DshtvError as exc:
        if transport(args) == "app" or exc.status in (401, 403):
            raise
        cfg = resolve_target(load_config())
        return adb_info(cfg["serial"])


def cmd_state(args: argparse.Namespace) -> dict:
    return make_client(args).state()


def cmd_key(args: argparse.Namespace) -> dict:
    repeat = max(1, min(int(args.repeat), 20))
    via = transport(args)
    if via != "adb":
        try:
            return make_client(args).key(args.code, repeat)
        except DshtvError as exc:
            if via == "app" or exc.status in (401, 403):
                raise
            eprint(f"[dshtv] app key failed ({exc}); falling back to adb")
    cfg = resolve_target(load_config())
    return adb_key(args.code, repeat, cfg["serial"])


def cmd_launch(args: argparse.Namespace) -> dict:
    via = transport(args)
    if via != "adb":
        try:
            return make_client(args).launch(app=args.app, package=args.package,
                                           url=args.url)
        except DshtvError as exc:
            if via == "app" or exc.status in (401, 403, 404):
                raise
            eprint(f"[dshtv] app launch failed ({exc}); falling back to adb")
    pkg = args.package
    if not pkg:
        raise DshtvError("adb launch needs --package (app labels are resolved by the app)")
    cfg = resolve_target(load_config())
    return adb_launch(pkg, cfg["serial"])


def cmd_apps(args: argparse.Namespace) -> dict:
    return make_client(args).apps()


def cmd_text(args: argparse.Namespace) -> dict:
    via = transport(args)
    if via != "adb":
        try:
            return make_client(args).text(args.text, enter=args.enter)
        except DshtvError as exc:
            # 409 means the app found no focused editable field. That is a real
            # answer, not a transport failure, so do not pretend adb fixed it.
            if via == "app" or exc.status in (401, 403, 404, 409):
                raise
            eprint(f"[dshtv] app text failed ({exc}); falling back to adb")
    cfg = resolve_target(load_config())
    return adb_text_input(args.text, args.enter, cfg["serial"])


def remote_voice_say(text: str, timeout: float = 120.0) -> dict:
    """Synthesize text and speak it into Google Assistant over the TV remote protocol.

    PCM16 mono 8 kHz, paired over TLS, fire-and-forget: Assistant's answer stays
    on the TV. This is the headless "DSH talks to Google Assistant" path.
    """
    if not REMOTE_VENV_PY.exists() or not REMOTE_VOICE_SCRIPT.exists():
        raise DshtvError(
            "voice injection is not set up; run: python3 -m venv dshtv/venv && "
            "dshtv/venv/bin/pip install androidtvremote2"
        )
    cfg = resolve_target(load_config())
    if not (REMOTE_DIR / "dshtv-remote.crt").exists():
        raise DshtvError(
            "remote protocol not paired; run: dshtv/venv/bin/python "
            "dshtv/tv_remote_pair.py and enter the code shown on the TV"
        )
    proc = subprocess.run(
        [str(REMOTE_VENV_PY), str(REMOTE_VOICE_SCRIPT),
         "--host", cfg["host"], "--text", text],
        capture_output=True, text=True, timeout=timeout,
    )
    events = []
    for line in (proc.stdout or "").splitlines():
        try:
            events.append(json.loads(line))
        except Exception:
            pass
    if proc.returncode != 0:
        detail = next((e for e in events if e.get("event") == "error"), None)
        if detail is None:
            detail = (proc.stderr or "").strip()[:400] or f"exit {proc.returncode}"
        raise DshtvError(f"voice injection failed: {detail}")
    return {"ok": True, "via": "remote-voice", "text": text,
            "host": cfg["host"], "events": events}


def cmd_voice(args: argparse.Namespace) -> dict:
    if getattr(args, "text", None):
        return remote_voice_say(args.text)
    via = transport(args)
    if via != "adb":
        try:
            return make_client(args).voice()
        except DshtvError as exc:
            if via == "app" or exc.status in (401, 403):
                raise
            eprint(f"[dshtv] app voice failed ({exc}); falling back to adb")
    cfg = resolve_target(load_config())
    return adb_voice(cfg["serial"])


def transcribe_wav(path: Path | str, model: str | None = None,
                   timeout: float = 300.0) -> dict:
    """Transcribe a WAV locally with mlx-whisper in dshtv/venv."""
    if not REMOTE_VENV_PY.exists() or not TRANSCRIBE_SCRIPT.exists():
        raise DshtvError(
            "STT is not set up; run: python3 -m venv dshtv/venv && "
            "dshtv/venv/bin/pip install mlx-whisper"
        )
    cmd = [str(REMOTE_VENV_PY), str(TRANSCRIBE_SCRIPT), "--wav", str(path)]
    if model:
        cmd += ["--model", model]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise DshtvError(f"transcription timed out after {timeout}s") from exc
    events = []
    for line in (proc.stdout or "").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            events.append(json.loads(line))
        except Exception:
            pass
    if proc.returncode != 0 or not events or not events[-1].get("ok"):
        detail = events[-1] if events else (proc.stderr or "").strip()[:400]
        raise DshtvError(f"transcription failed: {detail}")
    return events[-1]


def cmd_speak(args: argparse.Namespace) -> dict:
    return make_client(args).speak(args.text)


def cmd_mic(args: argparse.Namespace) -> dict:
    seconds = max(1, min(int(args.seconds), 30))
    client = make_client(args)
    data = client.mic(seconds, source=args.source)
    path = save_bytes(data, args.out, f"mic-{time.strftime('%Y%m%d-%H%M%S')}.wav")
    return {"ok": True, "path": str(path), "bytes": len(data),
            "seconds": seconds, "source": args.source}


def cmd_listen(args: argparse.Namespace) -> dict:
    seconds = max(1, min(int(args.seconds), 30))
    client = make_client(args)
    data = client.mic(seconds, source=args.source)
    path = save_bytes(data, args.out, f"listen-{time.strftime('%Y%m%d-%H%M%S')}.wav")
    tr = transcribe_wav(path, args.model)
    return {
        "ok": True,
        "path": str(path),
        "seconds": seconds,
        "source": args.source,
        "text": tr.get("text", ""),
        "model": tr.get("model"),
        "language": tr.get("language"),
    }


def record_mac_wav(seconds: int, out: Path | None = None,
                   device: str = MAC_MIC_DEVICE) -> Path:
    """Record from the Mac's default USB microphone via ffmpeg/AVFoundation."""
    if out is None:
        CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
        out = CAPTURE_DIR / f"mac-mic-{time.strftime('%Y%m%d-%H%M%S')}.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-f", "avfoundation", "-i", device,
        "-t", str(seconds), "-ac", "1", "-ar", "16000", "-y", str(out),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=seconds + 20)
    except subprocess.TimeoutExpired as exc:
        raise DshtvError(f"Mac mic recording timed out after {seconds}s") from exc
    if proc.returncode != 0 or not out.exists():
        detail = (proc.stderr or "").strip()[:400]
        raise DshtvError(f"Mac mic recording failed: {detail or 'ffmpeg error'}")
    return out


def cmd_mac_mic(args: argparse.Namespace) -> dict:
    seconds = max(1, min(int(args.seconds), 30))
    out = Path(args.out).expanduser() if args.out else None
    path = record_mac_wav(seconds, out, args.device)
    return {"ok": True, "path": str(path), "seconds": seconds,
            "device": args.device, "via": "mac"}


def cmd_mac_listen(args: argparse.Namespace) -> dict:
    seconds = max(1, min(int(args.seconds), 30))
    out = Path(args.out).expanduser() if args.out else None
    path = record_mac_wav(seconds, out, args.device)
    tr = transcribe_wav(path, args.model)
    return {
        "ok": True,
        "path": str(path),
        "seconds": seconds,
        "device": args.device,
        "via": "mac",
        "text": tr.get("text", ""),
        "model": tr.get("model"),
        "language": tr.get("language"),
    }


def cmd_screenshot(args: argparse.Namespace) -> dict:
    out = args.out
    via = transport(args)
    if via != "adb":
        try:
            data = make_client(args).screenshot()
            path = save_bytes(data, out, f"tv-{time.strftime('%Y%m%d-%H%M%S')}.jpg")
            return {"ok": True, "via": "app", "path": str(path), "bytes": len(data)}
        except DshtvError as exc:
            if via == "app" or exc.status in (401, 403):
                raise
            eprint(f"[dshtv] app screenshot failed ({exc}); falling back to adb")
    cfg = resolve_target(load_config())
    data = adb_screenshot(cfg["serial"])
    if not out:
        out = None
    path = save_bytes(data, out, f"tv-{time.strftime('%Y%m%d-%H%M%S')}.png")
    return {"ok": True, "via": "adb", "path": str(path), "bytes": len(data)}


def cmd_volume(args: argparse.Namespace) -> dict:
    return make_client(args).volume(level=args.level, delta=args.delta)


def cmd_power(args: argparse.Namespace) -> dict:
    cfg = resolve_target(load_config())
    action = args.action
    key = {"on": "wakeup", "wake": "wakeup", "off": "power",
           "sleep": "sleep", "toggle": "power"}[action]
    result = adb_key(key, 1, cfg["serial"])
    return {**result, "action": action}


def cmd_adb_connect(args: argparse.Namespace) -> dict:
    return adb_connect(args.host, args.adb_port)


def cmd_disable(args: argparse.Namespace) -> dict:
    cfg = resolve_target(load_config())
    return remove_accessibility(cfg["serial"])


# ---------------------------------------------------------------------------
# argparse
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--host", help="onn LAN IP (default: config/discovery)")
    common.add_argument("--port", type=int, help=f"bridge HTTP port (default {DEFAULT_PORT})")
    common.add_argument("--token", help="bridge token (default: config)")
    common.add_argument("--via", choices=["auto", "app", "adb"], default="auto",
                        help="transport: auto (default), app only, adb only")
    common.add_argument("--serial", help="adb serial of the onn")

    parser = argparse.ArgumentParser(
        prog="dshtv",
        description="Drive the onn. 4K Pro (Google TV) from this Mac / DSH.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("discover", parents=[common], help="find the onn and probe the bridge")
    p.add_argument("--write", action="store_true", help="save the discovered target to config")
    p.set_defaults(func=cmd_discover)

    p = sub.add_parser("setup", parents=[common],
                       help="install the bridge APK, enable accessibility, grant mic, start")
    p.add_argument("--apk", help="APK path (default .tools/dshtv-app/DSHTVBridge.apk)")
    p.add_argument("--ip", dest="ip", help="onn IP for adb connect during setup")
    p.set_defaults(func=cmd_setup)

    p = sub.add_parser("doctor", parents=[common], help="show device/config/health diagnostics")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("ping", parents=[common], help="bridge health check")
    p.set_defaults(func=cmd_ping)

    p = sub.add_parser("info", parents=[common], help="device/app info")
    p.set_defaults(func=cmd_info)

    p = sub.add_parser("state", parents=[common], help="foreground app and volume state")
    p.set_defaults(func=cmd_state)

    p = sub.add_parser("key", parents=[common], help="inject a remote key")
    p.add_argument("code", help="up|down|left|right|ok|back|home|recents|menu|"
                               "playpause|play|pause|next|prev|rewind|fastforward|"
                               "volup|voldown|mute")
    p.add_argument("--repeat", type=int, default=1)
    p.set_defaults(func=cmd_key)

    p = sub.add_parser("launch", parents=[common], help="launch an app or URL")
    p.add_argument("app", nargs="?", help="app label or substring, e.g. netflix")
    p.add_argument("--package", help="exact package name")
    p.add_argument("--url", help="VIEW intent URL / deep link")
    p.set_defaults(func=cmd_launch)

    p = sub.add_parser("apps", parents=[common], help="list launchable apps")
    p.set_defaults(func=cmd_apps)

    p = sub.add_parser("text", parents=[common], help="type into the focused field")
    p.add_argument("text")
    p.add_argument("--enter", action="store_true")
    p.set_defaults(func=cmd_text)

    p = sub.add_parser("voice", parents=[common],
                       help="open Assistant (no arg), or speak TEXT into it (remote protocol)")
    p.add_argument("text", nargs="?",
                   help="If given, synthesize this and inject it into Google Assistant.")
    p.set_defaults(func=cmd_voice)

    p = sub.add_parser("speak", parents=[common], help="TTS on the TV speakers")
    p.add_argument("text")
    p.set_defaults(func=cmd_speak)

    p = sub.add_parser("mic", parents=[common], help="record the TV's built-in mic to WAV")
    p.add_argument("--seconds", type=int, default=5)
    p.add_argument("--out", help="output .wav path")
    p.add_argument("--source", default="voice",
                   choices=["voice", "mic", "voice_communication", "camcorder", "unprocessed"],
                   help="AudioRecord source (default voice = speech processing)")
    p.set_defaults(func=cmd_mic)

    p = sub.add_parser("listen", parents=[common],
                       help="record the TV's mic and transcribe it locally (speech → text)")
    p.add_argument("--seconds", type=int, default=8)
    p.add_argument("--out", help="output .wav path")
    p.add_argument("--model", default=None,
                   help="mlx-whisper HF repo (default whisper-base.en-mlx)")
    p.add_argument("--source", default="voice",
                   choices=["voice", "mic", "voice_communication", "camcorder", "unprocessed"])
    p.set_defaults(func=cmd_listen)

    p = sub.add_parser("mac-mic", help="record the Mac's USB mic (BOYA BY-CM1) to WAV")
    p.add_argument("--seconds", type=int, default=5)
    p.add_argument("--out", help="output .wav path")
    p.add_argument("--device", default=MAC_MIC_DEVICE,
                   help="AVFoundation audio device (default ':0', env DSHTV_MAC_MIC)")
    p.set_defaults(func=cmd_mac_mic)

    p = sub.add_parser("mac-listen", help="record the Mac's USB mic and transcribe locally")
    p.add_argument("--seconds", type=int, default=8)
    p.add_argument("--out", help="output .wav path")
    p.add_argument("--model", default=None,
                   help="mlx-whisper HF repo (default whisper-base.en-mlx)")
    p.add_argument("--device", default=MAC_MIC_DEVICE,
                   help="AVFoundation audio device (default ':0', env DSHTV_MAC_MIC)")
    p.set_defaults(func=cmd_mac_listen)

    p = sub.add_parser("screenshot", parents=[common], help="capture the TV screen")
    p.add_argument("--out", help="output path (jpg via app, png via adb)")
    p.set_defaults(func=cmd_screenshot)

    p = sub.add_parser("volume", parents=[common], help="set or nudge media volume")
    p.add_argument("--level", type=int)
    p.add_argument("--delta", type=int)
    p.set_defaults(func=cmd_volume)

    p = sub.add_parser("power", parents=[common], help="wake/sleep/power (adb only)")
    p.add_argument("action", choices=["on", "off", "wake", "sleep", "toggle"])
    p.set_defaults(func=cmd_power)

    p = sub.add_parser("adb-connect", parents=[common], help="adb connect <ip>:5555")
    p.add_argument("--adb-port", type=int, default=5555)
    p.set_defaults(func=cmd_adb_connect)

    p = sub.add_parser("disable", parents=[common],
                       help="remove our service from the accessibility list")
    p.set_defaults(func=cmd_disable)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = args.func(args)
        emit(result)
        return 0
    except DshtvError as exc:
        emit({"ok": False, "error": str(exc)})
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
