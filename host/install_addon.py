#!/usr/bin/env python3
"""install_addon.py — install (or refresh) the addon in Stremio with no typing.

Why this exists: `stremio://<url>` upgrades to https, and this addon is served over plain HTTP
on the LAN, so the familiar one-click install from a web page cannot work. The in-app flow can:
Stremio is on the same device, and we can drive it.

    ./install_addon.py                 # uses the live addon's own URL
    ./install_addon.py <manifest-url>  # any addon URL

It is the exact sequence that works by hand: launch Stremio → sidebar → Addons → Add addon →
type the URL → ADD → Install, with a UI-dump check at each step instead of a fixed sleep. It
ends by confirming the addon screen offers "Uninstall", which only happens when installed.

Exit 0 = installed, 1 = could not complete a step (the step is named in the output).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

try:                                    # reuse the CLI's adb resolution instead of guessing
    from dshtv import adb_bin, adb_devices
except Exception:                       # noqa: BLE001 - the tap fallback is optional
    adb_bin = adb_devices = None
DSHTV = HERE / "dshtv.py"
STREMIO = "com.stremio.one"
LIVE_DIR = Path(os.environ.get("DSHTV_ADDON_DATA")
                or (Path.home() / "Library" / "Application Support" / "dsh-tv-addon"))


# ----------------------------------------------------------------- primitives
def run(cmd: list[str], timeout: int = 60) -> tuple[int, str]:
    proc = subprocess.run([sys.executable] + cmd, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def dshtv(*args: str) -> tuple[int, str]:
    return run([str(DSHTV), *args])


def ui() -> dict:
    code, out = dshtv("ui")
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return {"nodes": [], "focused": {}}


def texts(node: dict | None = None) -> list[str]:
    data = node if node is not None else ui()
    return [(n.get("text") or "").strip() for n in data.get("nodes", []) if (n.get("text") or "").strip()]


def focused_label() -> str:
    f = ui().get("focused") or {}
    return (f.get("text") or "").strip()


def bounds_of(label: str) -> tuple[int, int] | None:
    """Centre of the first node with this text — the same lookup used by hand."""
    import re
    for n in ui().get("nodes", []):
        if (n.get("text") or "").strip() == label:
            nums = [int(x) for x in re.findall(r"-?\d+", n.get("bounds") or "")]
            if len(nums) >= 4:
                return ((nums[0] + nums[2]) // 2, (nums[1] + nums[3]) // 2)
    return None


def key(name: str, wait: float = 0.7) -> None:
    dshtv("key", name)
    time.sleep(wait)


def type_text(value: str) -> None:
    """Type into the focused field.

    This used the bridge's /text first, but that needs the accessibility service, which an app
    update disables — so installing the addon would silently depend on a setting. adb's input
    injection needs nothing but debugging on, and spaces must be `%s` or the string truncates
    at the first one.
    """
    if not adb_bin:
        raise RuntimeError("adb not available")
    escaped = value.replace(" ", "%s")
    try:
        serial = (adb_devices() or [{}])[0].get("serial")
    except Exception:  # noqa: BLE001
        serial = None
    cmd = [adb_bin()] + (["-s", serial] if serial else []) + ["shell", "input", "text", escaped]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if proc.returncode != 0:
        raise RuntimeError(f"adb input text failed: {(proc.stderr or proc.stdout or '').strip()[-120:]}")
    time.sleep(0.8)


def wheel_to(label: str, up: bool, tries: int = 12) -> bool:
    """Walk a focus list until it lands on `label`."""
    for _ in range(tries):
        if focused_label() == label:
            return True
        key("up" if up else "down", 0.5)
    return focused_label() == label


# ----------------------------------------------------------------- flow
def ensure_stremio() -> None:
    code, out = dshtv("launch", "stremio")
    if code != 0:
        subprocess.run([sys.executable, str(DSHTV), "apps"], capture_output=True)
        raise RuntimeError(f"could not launch Stremio: {out.strip()[-160:]}")


def on_board(labels: list[str]) -> bool:
    return any("Continue Watching" in t or "TMDB" in t for t in labels)


def ensure_board(seconds: int = 60) -> bool:
    """Stremio resumes wherever it was left, which may be the add-on screen. Walk BACK to the
    board before starting; pressing BACK on the board itself would exit the app, so stop as
    soon as board markers appear."""
    deadline = time.time() + seconds
    while time.time() < deadline:
        labels = texts()
        if on_board(labels):
            return True
        if labels:
            key("back", 2.0)
        time.sleep(1.5)
    return on_board(texts())


def open_addons() -> None:
    key("left", 1.2)                          # sidebar
    target = bounds_of("Addons")
    if target is None:
        raise RuntimeError("sidebar has no Addons item")
    goal = target[1]
    for _ in range(12):
        f = ui().get("focused") or {}
        import re
        nums = [int(x) for x in re.findall(r"-?\d+", f.get("bounds") or "")]
        if nums and abs(nums[1] - goal) <= 45:
            break
        key("down" if (not nums or nums[1] < goal) else "up", 0.5)
    key("ok", 2.5)


def open_add_dialog() -> None:
    if not wheel_to("Add addon", up=True):
        target = bounds_of("Add addon")
        if target and tap(*target):
            key("ok", 2.0)
        if focused_label() != "Add addon" and "You can add an addon" not in " ".join(texts()):
            raise RuntimeError("could not focus 'Add addon'")
    key("ok", 2.5)
    if "Add addon" not in " ".join(texts()[:4]):
        raise RuntimeError("add-addon dialog did not open")


def submit_url(url: str) -> None:
    type_text(url)
    time.sleep(1.0)
    for _ in range(5):
        if focused_label() == "ADD":
            key("ok", 6.0)
            return
        dshtv("key", "tab")
        time.sleep(0.7)
    raise RuntimeError("could not focus the ADD button")


def confirm_install() -> None:
    for _ in range(6):
        labels = texts()
        if any("Uninstall" in t for t in labels if len(t) < 40):
            return
        if "Install" in labels:
            if focused_label() != "Install":
                dshtv("key", "tab")
                time.sleep(0.6)
                continue
            key("ok", 6.0)
            continue
        time.sleep(1.5)


def default_url(token: str | None) -> str:
    """The live addon's own URL — the token and port the daemon was started with."""
    cfg = {}
    try:
        for line in (LIVE_DIR / "config.env").read_text().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
    except FileNotFoundError:
        pass
    token = token or cfg.get("TOKEN")
    if not token:
        return ""
    return f"http://{live_lan_ip()}:{cfg.get('PORT', '8890')}/{token}/manifest.json"


def classify(labels: list[str]) -> str:
    """Name the screen, so the loop can act on what is actually showing rather than on what the
    previous step assumed. This is the fix for the fixed-script failures."""
    joined = " ".join(labels)
    if "TV Apps" in joined or "Navigation menu" in joined:
        return "launcher"          # BACK went too far and closed Stremio
    if "You can add an addon" in joined or ("ADD" in labels and "CANCEL" in labels):
        return "dialog"
    if "Install" in labels and "Cancel" not in labels and "Add addon" not in labels:
        return "confirm"
    if "Add addon" in labels and "Installed" in labels:
        return "addons"
    if "Continue Watching" in joined or "TMDB" in joined:
        return "board"
    return "other"


def tap(x: int, y: int) -> bool:
    """WebView buttons are ordinary touch targets — the reliable fallback when focus
    navigation cannot reach them."""
    if not adb_bin:
        return False
    try:
        serial = (adb_devices() or [{}])[0].get("serial")
    except Exception:  # noqa: BLE001
        serial = None
    cmd = [adb_bin()] + (["-s", serial] if serial else []) + ["shell", "input", "tap", str(x), str(y)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    time.sleep(1.2)
    return proc.returncode == 0


def click(label: str) -> bool:
    target = bounds_of(label)
    return bool(target and tap(*target))


def classify(labels: list[str]) -> str:
    """Name the screen, so the loop acts on what is actually showing rather than on what the
    previous step assumed. This is the fix for the fixed-script failures."""
    joined = " ".join(labels)
    if "TV Apps" in joined or "Navigation menu" in joined:
        return "launcher"          # BACK went too far and closed Stremio
    if "You can add an addon" in joined or ("ADD" in labels and "CANCEL" in labels):
        return "dialog"
    if "Uninstall" in labels:
        return "installed"
    if "Add addon" in labels and "Installed" in labels:
        return "addons"
    if "Continue Watching" in joined or "TMDB" in joined:
        return "board"
    return "other"


def click(label: str) -> bool:
    target = bounds_of(label)
    return bool(target and tap(*target))


def live_lan_ip() -> str:
    """The address the TV should use — the same one the daemon advertises."""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("192.168.4.1", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except OSError:
        return "127.0.0.1"


def main(argv) -> int:
    ap = argparse.ArgumentParser(description="Install or refresh the addon in Stremio.")
    ap.add_argument("url", nargs="?", help="manifest URL (default: the live addon's own URL)")
    ap.add_argument("--token", help="token, when not reading it from config.env")
    ap.add_argument("--steps", type=int, default=60, help="safety cap on actions")
    ap.add_argument("--keep", action="store_true",
                    help="re-add without removing first (keeps the row set Stremio snapshotted)")
    args = ap.parse_args(argv)

    url = args.url or default_url(args.token)
    if not url:
        print(json.dumps({"ok": False, "error": "no URL given and no token in config.env"}))
        return 1

    try:
        ensure_stremio()
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"ok": False, "step": "launch Stremio", "error": str(exc)}))
        return 1

    url_typed = False
    removed = False
    for _ in range(args.steps):
        labels = texts()
        screen = classify(labels)
        if screen == "installed":
            # Stremio snapshots the row set at add time and re-adding does NOT refresh it, so a
            # changed manifest (e.g. new row ids) needs a remove first.
            if args.keep or removed:
                print(json.dumps({"ok": True, "url": url,
                                  "confirmed_by": "the add-on screen offers Uninstall",
                                  "row_set": "kept (--keep)"}))
                return 0
            if click("Uninstall"):
                removed = True
                time.sleep(3.0)
                for candidate in ("Remove", "Confirm", "Yes"):
                    if any(t.strip() == candidate for t in texts()):
                        click(candidate)
                        break
                time.sleep(4.0)
                continue
        if screen == "board":
            key("left", 1.2)
            try:
                open_addons()
            except Exception:  # noqa: BLE001 - retried on the next pass
                pass
        elif screen == "addons":
            if not click("Add addon"):
                key("ok", 2.0)
            time.sleep(2.0)
        elif screen == "dialog":
            if not url_typed:
                type_text(url)
                url_typed = True
                time.sleep(1.5)
            if not click("ADD"):
                key("tab")
                time.sleep(0.6)
                key("ok", 4.0)
            else:
                time.sleep(4.0)
            url_typed = False
        elif screen == "launcher":
            try:
                ensure_stremio()
            except Exception:  # noqa: BLE001 - retried on the next pass
                pass
            time.sleep(6.0)
        else:
            key("back", 1.6)
        time.sleep(1.0)

    labels = texts()
    ok = any("Uninstall" in t for t in labels)
    print(json.dumps({"ok": ok, "url": url,
                      "note": "confirmed" if ok else f"gave up; last screen was {classify(labels)}"}))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
