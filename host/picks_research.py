#!/usr/bin/env python3
"""picks_research.py — turn a researched list of titles into a catalog row.

The agent's job is the research: from a seed the person loved, find the lineage it
belongs to and the films worth watching next. This script does the part that must not be
guessed — resolving each title to a real IMDB id and confirming it exists — and writes
`picks.json`, which the addon server serves as a live row.

    ./picks_research.py --spec research.json [--out picks.json]

Spec:

    { "seed": "The Breaking Ice",
      "theme": "Chinese New Wave — the films it comes out of",
      "movie":  ["A Touch of Sin", "Long Day's Journey Into Night", ...],
      "series": [] }

A title that cannot be resolved is reported, not silently dropped: an id nobody can play is
worse than a gap, and a gap is honest.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
import os
from pathlib import Path

LIVE_DIR = Path(os.environ.get("DSHTV_ADDON_DATA")
                or (Path.home() / "Library" / "Application Support" / "dsh-tv-addon"))
DEFAULT_CATALOGS = str(LIVE_DIR / "catalogs.json")
SLOT_COUNT = 6      # the manifest's fixed row set (see addon_server.SLOT_NAMES)

CINEMETA = "https://v3-cinemeta.strem.io"

# Resolution source. Cinemeta can FIND a current film by name but cannot SURFACE one: its
# eight catalogs are Popular/New/Featured with no release-status or upcoming vocabulary, so
# films in cinemas never appear in a row unless you already know the title. TMDB through the
# player's own AIOmetadata instance has a search catalog and a meta endpoint, so resolution
# goes there first when configured. "https://aiometadata.elfhosted.com/stremio/<uuid>"
AIO_BASE = ""
SEARCH_CATALOG = {"movie": "search.movie", "series": "search.series"}


def search(kind: str, title: str) -> list[dict]:
    # Apostrophes and quotes are the difference between a hit and a miss:
    # "Long Day's Journey Into Night" returns nothing, the same title without the
    # apostrophe returns the film. Strip them from the QUERY, keep them in the report.
    query = " ".join(title.replace("'", "").replace("\u2019", "").replace('"', "").split())
    if AIO_BASE:
        cat = SEARCH_CATALOG.get(kind, "search.movie")
        url = f"{AIO_BASE.rstrip('/')}/catalog/{kind}/{cat}/search={urllib.parse.quote(query)}.json"
    else:
        url = f"{CINEMETA}/catalog/{kind}/top/search={urllib.parse.quote(query)}.json"
    try:
        with urllib.request.urlopen(url, timeout=15) as res:
            return (json.loads(res.read().decode("utf-8") or "{}").get("metas") or [])
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError):
        return []


def meta(kind: str, imdb_id: str) -> dict | None:
    base = AIO_BASE.rstrip("/") if AIO_BASE else CINEMETA
    url = f"{base}/meta/{kind}/{urllib.parse.quote(imdb_id)}.json"
    try:
        with urllib.request.urlopen(url, timeout=15) as res:
            return json.loads(res.read().decode("utf-8") or "{}").get("meta")
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError):
        return None


def normalise(name: str) -> str:
    return "".join(ch for ch in (name or "").lower() if ch.isalnum())


def year_of(hit: dict) -> int | None:
    info = str(hit.get("releaseInfo") or "")
    for token in info.replace("\u2013", "-").split("-"):
        digits = "".join(ch for ch in token if ch.isdigit())
        if len(digits) == 4:
            return int(digits)
    return None


def resolve(kind: str, entry) -> dict | None:
    """Resolve a title to an id, preferring the year the caller asked for.

    Name search alone is not safe: "Perfect Day" returns a 2005 British film, and
    "Balloon" a 2018 German/French co-production, when the films meant are Chinese ones
    from 2023 and 2019. A row with the wrong film in it is worse than a short row, so a
    year, when given, filters hard; when omitted the match is reported as loose.
    """
    if isinstance(entry, dict):
        title = entry.get("title") or ""
        want_year = entry.get("year")
        want_country = (entry.get("country") or "").lower()
    else:
        title, want_year, want_country = entry, None, ""

    hits = search(kind, title)
    if not hits:
        return None

    pool = hits
    if want_year:
        near = [h for h in hits if year_of(h) and abs(year_of(h) - int(want_year)) <= 1]
        if near:
            pool = near

    want = normalise(title)
    exact = [h for h in pool if normalise(h.get("name")) == want]
    pool = exact or pool
    if want_country:
        by_country = [h for h in pool if want_country in str(h.get("releaseInfo") or "").lower()]
        pool = by_country or pool

    pick = pool[0]
    imdb_id = pick.get("id")
    if not imdb_id or not str(imdb_id).startswith("tt"):
        return None
    confirmed = meta(kind, imdb_id)
    if not confirmed:
        return None

    got_year = year_of(confirmed) or year_of(pick)
    return {
        "id": imdb_id,
        "name": confirmed.get("name") or pick.get("name") or title,
        "year": got_year,
        "country": confirmed.get("country"),
        "loose": bool(want_year) and bool(got_year) and abs(got_year - int(want_year)) > 1,
    }


def main(argv) -> int:
    ap = argparse.ArgumentParser(description="Resolve researched titles into a picks.json row.")
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", default=str(Path(__file__).with_name("picks.json")))
    ap.add_argument("--catalogs", default="",
                    help="write this row into the addon's catalog store (default: the live install)")
    ap.set_defaults(catalogs=DEFAULT_CATALOGS)
    ap.add_argument("--catalog-id", default="", help="stable id, e.g. chinese-new-wave")
    ap.add_argument("--catalog-name", default="", help="row title shown in the player")
    ap.add_argument("--catalog-type", default="movie", choices=["movie", "series"])
    ap.add_argument("--aiometadata", default="",
                    help="resolve through TMDB on your AIOmetadata instance, e.g. "
                         "https://aiometadata.elfhosted.com/stremio/<uuid>. Falls back to Cinemeta.")
    args = ap.parse_args(argv)

    global AIO_BASE
    AIO_BASE = (args.aiometadata or "").strip()
    print(f"  source: {'TMDB via AIOmetadata' if AIO_BASE else 'Cinemeta'}")

    spec = json.loads(Path(args.spec).read_text())
    out: dict[str, list[str]] = {"movie": [], "series": []}
    resolved, unresolved = [], []

    for kind in ("movie", "series"):
        for title in spec.get(kind) or []:
            got = resolve(kind, title)
            asked = title.get("title") if isinstance(title, dict) else title
            if got:
                out[kind].append(got["id"])
                resolved.append({"asked": asked, **got, "type": kind})
                flag = "LOOSE" if got["loose"] else "ok   "
                print(f"  {flag} {asked:40} -> {got['id']}  {got['name']} ({got['year']}, {got['country']})")
            else:
                unresolved.append({"asked": asked, "type": kind})
                print(f"  MISS  {asked:40} -> no id resolved")

    Path(args.out).write_text(json.dumps(out, indent=1) + "\n")

    # A bespoke catalog: the agent has been asked for a row, so the row becomes part of the
    # addon's manifest and appears in the player next to any earlier ones.
    if args.catalogs:
        cid = args.catalog_id or (spec.get("id") or "").strip()
        if not cid:
            cid = "".join(ch if ch.isalnum() else "-" for ch in (spec.get("theme") or "row").lower()).strip("-")[:40]
        name = args.catalog_name or spec.get("theme") or cid
        store_path = Path(args.catalogs).expanduser()
        try:
            store = json.loads(store_path.read_text())
            store = store if isinstance(store, list) else []
        except (FileNotFoundError, json.JSONDecodeError):
            store = []
        used = {e.get("slot") for e in store if isinstance(e, dict)}
        existing = next((e for e in store if isinstance(e, dict) and e.get("id") == cid), {})
        slot = existing.get("slot") or next((n for n in range(1, SLOT_COUNT + 1) if n not in used), None)
        store = [e for e in store if not (isinstance(e, dict) and e.get("id") == cid)]
        store.append({
            "id": cid,
            "type": args.catalog_type,
            "slot": slot,
            "name": name,
            "seed": spec.get("seed"),
            "theme": spec.get("theme"),
            "picks": out[args.catalog_type],
        })
        store_path.write_text(json.dumps(store, indent=1) + "\n")
        print(f"  catalog '{cid}' ({name}) -> slot {slot}, {len(out[args.catalog_type])} titles")
    print()
    print(json.dumps({
        "ok": True,
        "theme": spec.get("theme"),
        "seed": spec.get("seed"),
        "wrote": args.out,
        "movie": len(out["movie"]),
        "series": len(out["series"]),
        "unresolved": unresolved,
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
