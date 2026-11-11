#!/usr/bin/env python3
"""catalog_add.py — publish a bespoke catalog of items the addon plays itself.

For sources that are not keyed by IMDB id (a personal account, a private folder, an archive
you host), a catalog-only row is not enough: no stream addon can resolve those items, so the
addon has to serve the URL. This writes such a row into the catalog store and the addon
answers meta and stream for it.

    ./catalog_add.py --catalog-id private-archive --catalog-name "My Archive" \\
        --items items.json [--catalogs catalogs.json]

items.json:

    [{ "name": "Episode 1", "url": "https://host/file.mp4",
       "poster": "https://…/p.jpg", "description": "…", "releaseInfo": "2026" }]

Nothing here logs or echoes a URL beyond what you passed in.
"""
from __future__ import annotations

import argparse
import json
import sys
import os
from pathlib import Path


LIVE_DIR = Path(os.environ.get("DSHTV_ADDON_DATA")
                or (Path.home() / "Library" / "Application Support" / "dsh-tv-addon"))
DEFAULT_CATALOGS = str(LIVE_DIR / "catalogs.json")


def main(argv) -> int:
    ap = argparse.ArgumentParser(description="Publish a direct-item catalog (no IMDB ids).")
    ap.add_argument("--catalogs", default=DEFAULT_CATALOGS)
    ap.add_argument("--catalog-id", required=True)
    ap.add_argument("--catalog-name", required=True)
    ap.add_argument("--type", default="movie", choices=["movie", "series", "other"])
    ap.add_argument("--items", required=True, help="JSON array of {name, url, ...}")
    ap.add_argument("--seed", default="", help="optional note: what this row came from")
    args = ap.parse_args(argv)

    try:
        items = json.loads(Path(args.items).read_text())
    except FileNotFoundError:
        raise SystemExit(f"no such items file: {args.items}")
    except json.JSONDecodeError as err:
        raise SystemExit(f"{args.items} is not valid JSON: {err}")
    if not isinstance(items, list) or not items:
        raise SystemExit("items file must be a non-empty JSON array")

    clean, rejected = [], []
    for raw in items:
        if isinstance(raw, dict) and raw.get("url") and raw.get("name"):
            clean.append({k: raw[k] for k in ("name", "url", "poster", "description", "releaseInfo")
                          if raw.get(k)})
        else:
            rejected.append(raw)
    if not clean:
        raise SystemExit("no usable items: each needs at least name and url")

    store_path = Path(args.catalogs).expanduser()
    try:
        store = json.loads(store_path.read_text())
        store = store if isinstance(store, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        store = []

    store = [e for e in store if not (isinstance(e, dict) and e.get("id") == args.catalog_id)]
    store.append({
        "id": args.catalog_id,
        "type": args.type,
        "name": args.catalog_name,
        "seed": args.seed,
        "direct": True,
        "items": clean,
    })
    store_path.write_text(json.dumps(store, indent=1) + "\n")

    print(json.dumps({
        "ok": True,
        "catalog": args.catalog_id,
        "name": args.catalog_name,
        "items": len(clean),
        "rejected": len(rejected),
        "wrote": str(store_path),
        "live": "the running addon reads the store per request — no restart needed",
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
