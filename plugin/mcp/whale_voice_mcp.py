#!/usr/bin/env python3
"""MCP stdio server for the Whale-chan TV assistant.

Exposes the host-side voice daemon to DSH:
  whale_health   - is the daemon up (and where)
  whale_ask      - send text through the same persistent DSH voice session
  whale_start    - start the daemon if it is not running

The daemon is started on demand, so installing this plugin is enough; no
launchd job is required (a LaunchAgent is still recommended for reliability).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "whale-chan", "version": "1.0.0"}
ROOT = Path(os.environ.get("WHALE_REPO") or Path(__file__).resolve().parents[2]).resolve()
DAEMON = ROOT / "host" / "whale_voice.py"
TOKEN_FILE = ROOT / ".auth" / "whale.token"
PORT = int(os.environ.get("WHALE_PORT") or 8766)
BASE = os.environ.get("WHALE_DAEMON_URL") or f"http://127.0.0.1:{PORT}"


def eprint(*a: object) -> None:
    print(*a, file=sys.stderr, flush=True)


def token() -> str:
    t = os.environ.get("WHALE_TOKEN", "").strip()
    if t:
        return t
    try:
        return TOKEN_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def call(path: str, payload: dict | None = None, timeout: float = 300.0) -> dict:
    url = BASE + path
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json", "X-Whale-Token": token()},
        method="POST" if payload is not None else "GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def healthy() -> bool:
    try:
        call("/health", timeout=3)
        return True
    except Exception:
        return False


def ensure_daemon() -> dict:
    if healthy():
        return {"ok": True, "started": False, "url": BASE}
    if not DAEMON.exists():
        return {"ok": False, "error": f"daemon not found: {DAEMON}"}
    env = dict(os.environ)
    env.setdefault("WHALE_REPO", str(ROOT))
    logs = ROOT / "logs"
    logs.mkdir(exist_ok=True)
    log = open(logs / "whale-voice.log", "ab")
    subprocess.Popen(
        [sys.executable, str(DAEMON), "--serve", "--port", str(PORT)],
        cwd=str(ROOT), env=env, stdout=log, stderr=log,
        start_new_session=True,
    )
    for _ in range(30):
        time.sleep(0.5)
        if healthy():
            return {"ok": True, "started": True, "url": BASE}
    return {"ok": False, "error": "daemon did not become healthy"}


TOOLS = [
    {
        "name": "whale_health",
        "description": "Check whether the Whale-chan voice daemon on the Mac is running.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "whale_ask",
        "description": ("Send text to the same persistent DSH voice session the TV uses. "
                        "Useful to pre-load context or to try the voice brain without a remote."),
        "inputSchema": {
            "type": "object",
            "properties": {"text": {"type": "string", "description": "What to say to the assistant"}},
            "required": ["text"],
        },
    },
    {
        "name": "whale_start",
        "description": "Start the Whale-chan voice daemon if it is not already listening.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def tool_result(text: str, is_error: bool = False) -> dict:
    return {"content": [{"type": "text", "text": text}], "isError": is_error}


def dispatch(method: str, params: dict) -> dict:
    if method == "initialize":
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": SERVER_INFO,
        }
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        try:
            if name == "whale_health":
                return tool_result(json.dumps({"daemon": healthy(), "url": BASE}))
            if name == "whale_ask":
                text = str(args.get("text") or "").strip()
                if not text:
                    return tool_result("text is required", True)
                start = ensure_daemon()
                if not start.get("ok"):
                    return tool_result(json.dumps(start), True)
                answer = call("/ask", {"text": text})
                return tool_result(json.dumps(answer, ensure_ascii=False))
            if name == "whale_start":
                return tool_result(json.dumps(ensure_daemon()))
            return tool_result(f"unknown tool: {name}", True)
        except Exception as exc:  # noqa: BLE001 - map every failure into MCP
            return tool_result(f"{name} failed: {exc}", True)
    raise KeyError(method)


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except ValueError:
            continue
        if "id" not in req:  # notification
            continue
        try:
            result = dispatch(req.get("method", ""), req.get("params") or {})
            reply = {"jsonrpc": "2.0", "id": req["id"], "result": result}
        except KeyError as exc:
            reply = {"jsonrpc": "2.0", "id": req["id"],
                     "error": {"code": -32601, "message": f"method not found: {exc.args[0]}"}}
        except Exception as exc:  # noqa: BLE001
            reply = {"jsonrpc": "2.0", "id": req["id"],
                     "error": {"code": -32603, "message": str(exc)}}
        print(json.dumps(reply), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
