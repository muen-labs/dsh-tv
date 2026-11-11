#!/usr/bin/env python3
"""addon_config.py — configure an AIOmetadata addon as JSON, not by clicking.

Why this exists: AIOmetadata is a metadata addon that people set up through a web
configurator (`/configure`). The thing under that UI is a JSON document and a small
API, so an agent can author the config, save it, and hand back an install URL —
no configurator, no D-pad, no typing a 200-character URL into a TV.

    POST /api/config/save              {config, password} -> {userUUID, installUrl}
    POST /api/config/load/<uuid>       {password}         -> {config, installUrl}
    PUT  /api/config/update/<uuid>     {config, password} -> {config, installUrl}
    GET  /stremio/<uuid>/manifest.json                    -> the configured addon

Nuvio and Stremio both install this: same addon protocol, same manifest.

Credentials live in ~/.dsh/aiometadata.json (mode 0600, outside any repo) so the
password is never on a command line you have to remember. Nothing here prints it.

    ./addon_config.py new   --config spec.json          # create, print install URL
    ./addon_config.py from   --uuid <uuid>              # dump the JSON (schema + keys)
    ./addon_config.py apply  --uuid <uuid> --config f.json
    ./addon_config.py show                              # what is stored, no secrets
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_BASE = "https://aiometadata.elfhosted.com"
CRED_FILE = Path(os.environ.get("ADDON_CONFIG_CRED", Path.home() / ".dsh" / "aiometadata.json"))
TIMEOUT = 45


# --------------------------------------------------------------------------- http

def _request(method: str, base: str, path: str, payload: dict) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        base.rstrip("/") + path,
        data=data,
        headers={"content-type": "application/json", "accept": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
            return res.status, json.loads(res.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", "replace")
        try:
            return err.code, json.loads(body)
        except json.JSONDecodeError:
            return err.code, {"error": body[:300]}
    except urllib.error.URLError as err:
        return 0, {"error": f"network: {err.reason}"}


def _get_json(url: str) -> tuple[int, dict]:
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as res:
            return res.status, json.loads(res.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as err:
        return err.code, {"error": err.read().decode("utf-8", "replace")[:300]}
    except urllib.error.URLError as err:
        return 0, {"error": f"network: {err.reason}"}


# ---------------------------------------------------------------------- credentials

def load_creds() -> dict:
    try:
        return json.loads(CRED_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_creds(base: str, uuid: str, password: str) -> None:
    CRED_FILE.parent.mkdir(parents=True, exist_ok=True)
    CRED_FILE.write_text(json.dumps({"base": base, "uuid": uuid, "password": password}, indent=1))
    os.chmod(CRED_FILE, 0o600)


def redacted(creds: dict) -> dict:
    if not creds:
        return {}
    return {**creds, "password": f"<{len(creds.get('password') or '')} chars>"}


# --------------------------------------------------------------------------- verify

def describe_manifest(install_url: str) -> dict:
    """Fetch the configured manifest — the only proof the URL actually works."""
    status, body = _get_json(install_url)
    if status != 200:
        return {"ok": False, "status": status, "detail": body.get("error")}
    return {
        "ok": True,
        "name": body.get("name"),
        "version": body.get("version"),
        "catalogs": len(body.get("catalogs") or []),
        "resources": body.get("resources"),
    }


def fail(message: str, extra: dict | None = None) -> int:
    print(json.dumps({"ok": False, "error": message, **(extra or {})}, indent=1))
    return 1


def read_config_file(path: str) -> dict:
    try:
        raw = json.loads(Path(path).read_text())
    except FileNotFoundError:
        raise SystemExit(f"no such config file: {path}")
    except json.JSONDecodeError as err:
        raise SystemExit(f"{path} is not valid JSON: {err}")
    # Accept either a bare config or a wrapper with {"config": {...}}.
    return raw["config"] if isinstance(raw, dict) and isinstance(raw.get("config"), dict) else raw


# --------------------------------------------------------------------------- commands

def cmd_new(args) -> int:
    config = read_config_file(args.config)
    password = args.password or secrets.token_urlsafe(18)
    status, body = _request("POST", args.base, "/api/config/save", {"config": config, "password": password})
    if status != 200 or not body.get("installUrl"):
        return fail("save failed", {"status": status, "response": body})

    save_creds(args.base, body["userUUID"], password)
    return emit_saved(body, describe_manifest(body["installUrl"]))


def cmd_apply(args) -> int:
    config = read_config_file(args.config)
    creds = load_creds()
    uuid = args.uuid or creds.get("uuid")
    password = args.password or creds.get("password")
    base = args.base or creds.get("base") or DEFAULT_BASE
    if not uuid or not password:
        return fail("need --uuid and a password (or run `new` first so they are stored)")

    status, body = _request("PUT", base, f"/api/config/update/{uuid}", {"config": config, "password": password})
    if status != 200:
        return fail("update failed", {"status": status, "response": body})

    install = body.get("installUrl") or f"{base}/stremio/{uuid}/manifest.json"
    return emit_saved({**body, "userUUID": uuid, "installUrl": install}, describe_manifest(install))


def cmd_from(args) -> int:
    creds = load_creds()
    uuid = args.uuid or creds.get("uuid")
    password = args.password or creds.get("password")
    base = args.base or creds.get("base") or DEFAULT_BASE
    if not uuid or not password:
        return fail("need --uuid and a password (or run `new` first)")

    status, body = _request("POST", base, f"/api/config/load/{uuid}", {"password": password})
    if status != 200:
        hint = "wrong password" if status == 401 else "load failed"
        return fail(hint, {"status": status, "response": body})

    config = body.get("config") or {}
    out = Path(args.out) if args.out else None
    if out:
        out.write_text(json.dumps(config, indent=1))
    print(json.dumps({
        "ok": True,
        "uuid": uuid,
        "installUrl": body.get("installUrl") or f"{base}/stremio/{uuid}/manifest.json",
        "configKeys": list(config)[:20],
        "catalogs": len(config.get("catalogs") or []),
        "providers": len(config.get("providers") or {}),
        "wrote": str(out) if out else None,
        "config": None if out else config,
    }, indent=1))
    return 0


def cmd_show(args) -> int:
    creds = load_creds()
    if not creds:
        return fail("nothing stored", {"looked": str(CRED_FILE)})
    print(json.dumps({"ok": True, "stored": str(CRED_FILE), **redacted(creds)}, indent=1))
    return 0


def emit_saved(body: dict, manifest: dict) -> int:
    print(json.dumps({
        "ok": True,
        "uuid": body.get("userUUID"),
        "installUrl": body.get("installUrl"),
        "configVersion": body.get("configVersion"),
        "manifest": manifest,
        "stored": str(CRED_FILE),
        "next": "install installUrl in Nuvio/Stremio, then read the Addons screen to verify",
    }, indent=1))
    return 0


def main(argv) -> int:
    ap = argparse.ArgumentParser(description="Configure an AIOmetadata addon as JSON.")
    ap.add_argument("--base", default=None, help=f"instance base URL (default {DEFAULT_BASE})")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("new", help="save a new config and print its install URL")
    p.add_argument("--config", required=True, help="JSON file (bare config or {config:…})")
    p.add_argument("--password", help="config password; generated and stored if omitted")
    p.set_defaults(fn=cmd_new)

    p = sub.add_parser("apply", help="update an existing config")
    p.add_argument("--config", required=True)
    p.add_argument("--uuid")
    p.add_argument("--password")
    p.set_defaults(fn=cmd_apply)

    p = sub.add_parser("from", help="load an existing config (schema + your keys)")
    p.add_argument("--uuid")
    p.add_argument("--password")
    p.add_argument("--out", help="write the config JSON here instead of printing it")
    p.set_defaults(fn=cmd_from)

    p = sub.add_parser("show", help="what is stored locally (no secrets)")
    p.set_defaults(fn=cmd_show)

    args = ap.parse_args(argv)
    args.base = args.base or (load_creds().get("base") if args.cmd != "new" else None) or DEFAULT_BASE
    try:
        return args.fn(args)
    except SystemExit as err:
        return fail(str(err))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
