#!/usr/bin/env python3
"""install_catalog.py — merge a catalog file into the live store, then verify it is live.

The assistant kept doing the hard part right (researching titles, resolving ids) and then
failing on the easy part: writing to a path of its own invention and announcing success it had
not checked. So this exists to remove both degrees of freedom.

    ./install_catalog.py catalog.json

`catalog.json` is store-shaped — a list of
`{"id", "type", "name", "picks": ["tt…"]}` entries — exactly what the agent naturally produces.
Entries are merged by id, invalid ids are dropped and reported, and then the manifest is
fetched from the running addon to CONFIRM each row is really there.

It prints one machine-readable line, which is the only thing worth telling the household:

    OK row=japanese-slow name="Japanese Slow Cinema" picks=18 verified=yes
    FAIL row=japanese-slow reason=not-in-manifest

If the last line does not start with OK, the row is not live — whatever anyone believes.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

LIVE_DIR = Path(os.environ.get("DSHTV_ADDON_DATA")
                or (Path.home() / "Library" / "Application Support" / "dsh-tv-addon"))
STORE = LIVE_DIR / "catalogs.json"
SLOT_COUNT = 6      # must match addon_server.SLOT_COUNT: the manifest's fixed row set


def live_config() -> dict:
    """PORT/TOKEN as the running addon was started with."""
    cfg = {}
    try:
        for line in (LIVE_DIR / "config.env").read_text().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
    except FileNotFoundError:
        pass
    return cfg


def id_resolves(imdb_id: str, kind: str) -> bool:
    """An id that starts with tt is not a film. Ask the metadata source whether it exists —
    an agent writing ids from memory is exactly the case that needs checking."""
    base = live_config().get("AIO", "").rstrip("/")
    if not base:
        return True  # nothing to check against; the manifest check still runs
    try:
        with urllib.request.urlopen(f"{base}/meta/{kind}/{imdb_id}.json", timeout=12) as res:
            meta = json.loads(res.read().decode() or "{}").get("meta")
        return bool(meta)
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError):
        return False


def verify(entry: dict) -> tuple[bool, str]:
    """Confirm the slot actually serves this catalog's titles.

    The manifest always lists every slot, so "the row exists" proves nothing. What matters is
    that asking for the slot returns this catalog's ids, which is the only thing that shows the
    agent's row reached the player.
    """
    cfg = live_config()
    port, token = cfg.get("PORT", "8890"), cfg.get("TOKEN", "")
    if not token:
        return False, "no-token-in-config.env"
    if not entry.get("slot"):
        return False, "no-free-slot"
    try:
        url = f"http://127.0.0.1:{port}/{token}/catalog/movie/slot-{entry['slot']}.json"
        with urllib.request.urlopen(url, timeout=25) as res:
            metas = json.loads(res.read().decode() or "{}").get("metas") or []
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError) as exc:
        return False, f"addon-unreachable({exc.__class__.__name__})"
    if not metas:
        return False, f"slot-{entry['slot']}-served-nothing"
    ids = {m.get("id") for m in metas}
    if not ids & set(entry["picks"]):
        return False, f"slot-{entry['slot']}-served-other-content"
    return True, "yes"


def free_slot(store: list[dict]) -> int | None:
    used = {e.get("slot") for e in store if isinstance(e, dict)}
    for n in range(1, SLOT_COUNT + 1):
        if n not in used:
            return n
    return None


def main(argv) -> int:
    ap = argparse.ArgumentParser(description="Install a catalog file and verify it is live.")
    ap.add_argument("file")
    ap.add_argument("--catalogs", default=str(STORE))
    args = ap.parse_args(argv)

    try:
        incoming = json.loads(Path(args.file).read_text())
    except FileNotFoundError:
        print(f"FAIL file=missing path={args.file}")
        return 1
    except json.JSONDecodeError as exc:
        print(f"FAIL file=invalid-json error={exc}")
        return 1
    entries = incoming if isinstance(incoming, list) else [incoming]

    store_path = Path(args.catalogs).expanduser()
    try:
        store = json.loads(store_path.read_text())
        store = store if isinstance(store, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        store = []

    installed = []
    for raw in entries:
        if not isinstance(raw, dict) or not raw.get("id") or not raw.get("type"):
            print(f"FAIL row=? reason=needs-id-and-type")
            return 1
        picks = [p for p in (raw.get("picks") or []) if isinstance(p, str) and p.startswith("tt")]
        dropped = len(raw.get("picks") or []) - len(picks)
        if not picks:
            print(f"FAIL row={raw['id']} reason=no-valid-imdb-ids")
            return 1
        if dropped:
            print(f"  dropped {dropped} non-imdb id(s) from {raw['id']}")
        with ThreadPoolExecutor(max_workers=10) as pool:
            checks = list(pool.map(lambda i: id_resolves(i, str(raw["type"])), picks))
        bad = [i for i, ok in zip(picks, checks) if not ok]
        if bad:
            print(f"  dropped {len(bad)} id(s) that do not resolve: {bad[:6]}")
            picks = [i for i, ok in zip(picks, checks) if ok]
        if not picks:
            print(f"FAIL row={raw['id']} reason=no-id-resolves")
            return 1
        # Keep the slot this catalog already had; otherwise take the first free one.
        existing = next((e for e in store if isinstance(e, dict) and e.get("id") == raw["id"]), {})
        slot = raw.get("slot") or existing.get("slot") or free_slot(store)
        entry = {
            "id": str(raw["id"]),
            "type": str(raw["type"]),
            "slot": int(slot) if slot else None,
            "name": str(raw.get("name") or raw["id"]),
            "seed": raw.get("seed", ""),
            "theme": raw.get("theme", ""),
            "picks": picks,
        }
        store = [e for e in store if not (isinstance(e, dict) and e.get("id") == entry["id"])]
        store.append(entry)
        installed.append(entry)

    store_path.parent.mkdir(parents=True, exist_ok=True)
    store_path.write_text(json.dumps(store, indent=1) + "\n")

    ok = True
    for entry in installed:
        live, detail = verify(entry)
        ok = ok and live
        if live:
            print(f'OK slot={entry["slot"]} name="{entry["name"]}" picks={len(entry["picks"])} verified=yes')
        else:
            print(f'FAIL row={entry["id"]} reason={detail}')
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
