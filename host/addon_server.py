#!/usr/bin/env python3
"""addon_server.py — a Stremio/Nuvio catalog addon whose rows are built on the fly.

The concept: the agent decides *what* to put in a row, the catalog is generated at
request time, and the streams come from whatever stream addon the player already has
installed (Torrentio, Comet, AIOStreams). One addon, both players.

The load-bearing detail: stream addons key their results by **IMDB id**. A catalog row
is only useful if every item carries a real `tt…` id, so picks are ids + an optional
reason, and the name/poster are enriched from Cinemeta at request time rather than
guessed.

    GET /<token>/manifest.json
    GET /<token>/catalog/<type>/<catalogId>.json[?skip=N&search=...]
    GET /<token>/meta/<type>/<id>.json

Picks file:

    { "movie":  ["tt0111161", "tt1375666"],
      "series": ["tt0903747"] }

Nothing here decides taste yet — it serves whatever the picks file says, so the agent
that writes that file is the part that thinks.
"""
from __future__ import annotations

import argparse
import json
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

CINEMETA = "https://v3-cinemeta.strem.io"
ADDON_ID = "com.muen.deepseek.tv"

# Metadata source. Cinemeta is what Stremio ships, but most people hide it and use TMDB
# through AIOmetadata instead — so the enrichment should come from the same place their
# player does, or every row is styled and described by an addon they turned off.
# Set AIO_META_BASE to "https://aiometadata.elfhosted.com/stremio/<your-uuid>".
AIO_META_BASE = ""
STORE_PATH = Path(__file__).with_name("catalogs.json")
VERSION = "0.1.0"
PAGE = 24
CACHE_TTL = 900

_cache: dict[str, tuple[float, dict]] = {}
_lock = threading.Lock()


def _get_meta(url: str) -> dict | None:
    try:
        with urllib.request.urlopen(url, timeout=12) as res:
            return json.loads(res.read().decode("utf-8") or "{}").get("meta")
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError):
        return None


def _fetch_meta(kind: str, imdb_id: str) -> dict | None:
    """Real name/poster for an id, from the source the player's users actually run.

    AIOmetadata first (TMDB, the metadata most people keep), Cinemeta only as a fallback so
    the addon still works on a box with nothing else installed. Nothing is invented either
    way: an id that resolves nowhere is dropped rather than styled from a guess.
    """
    key = f"{kind}:{imdb_id}"
    now = time.time()
    with _lock:
        hit = _cache.get(key)
        if hit and now - hit[0] < CACHE_TTL:
            return hit[1]

    quoted = urllib.parse.quote(imdb_id)
    meta = None
    if AIO_META_BASE:
        meta = _get_meta(f"{AIO_META_BASE.rstrip('/')}/meta/{kind}/{quoted}.json")
        if meta:
            meta["_source"] = "aiometadata"
    if not meta:
        meta = _get_meta(f"{CINEMETA}/meta/{kind}/{quoted}.json")
        if meta:
            meta["_source"] = "cinemeta"
    if not meta:
        return None

    with _lock:
        _cache[key] = (now, meta)
    return meta


def load_store(path: Path) -> list[dict]:
    """The agent's catalog store: one entry per bespoke row it has been asked to make."""
    try:
        data = json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    out = []
    for entry in data if isinstance(data, list) else []:
        if not isinstance(entry, dict):
            continue
        if not entry.get("id") or not entry.get("type"):
            continue
        out.append({
            "id": str(entry["id"]),
            "type": str(entry["type"]),
            "name": entry.get("name") or entry["id"],
            "picks": [i for i in (entry.get("picks") or []) if str(i).startswith("tt")],
        })
    return out


def build_manifest(token: str) -> dict:
    return {
        "id": ADDON_ID,
        "version": VERSION,
        "name": "DeepSeek Picks",
        "description": "Rows built on the fly. The picks come from DeepSeek TV; the streams "
                       "come from whichever stream addon you already installed.",
        "types": ["movie", "series"],
        "resources": ["catalog"],
        "catalogs": _manifest_catalogs(),
        # Only ids that stream addons already index are useful here.
        "idPrefixes": ["tt"],
        "behaviorHints": {"configurable": False},
    }


def _manifest_catalogs() -> list[dict]:
    """Each bespoke catalog the agent has built becomes its own row in the player."""
    rows = []
    for entry in load_store(STORE_PATH):
        rows.append({
            "type": entry["type"],
            "id": entry["id"],
            "name": entry["name"],
            "extra": [{"name": "skip", "isRequired": False}],
        })
    if rows:
        return rows
    # Back-compat: a single picks.json served as one movie and one series row.
    return [
        {"type": "movie", "id": "deepseek", "name": "DeepSeek · Movies",
         "extra": [{"name": "skip", "isRequired": False}]},
        {"type": "series", "id": "deepseek", "name": "DeepSeek · Series",
         "extra": [{"name": "skip", "isRequired": False}]},
    ]


def build_catalog(ids: list[str], kind: str, skip: int = 0) -> dict:
    window = ids[skip:skip + PAGE]
    # One metadata lookup per title, and they are independent — so they go out together.
    # Sequentially this was 5-6s for a 17-title row, which on a TV's already-laggy UI is the
    # difference between a row appearing and the app feeling broken.
    with ThreadPoolExecutor(max_workers=min(12, max(1, len(window)))) as pool:
        fetched = list(pool.map(lambda i: _fetch_meta(kind, i), window))
    metas = []
    for imdb_id, meta in zip(window, fetched):
        if not meta:
            continue
        metas.append({
            "id": imdb_id,
            "type": kind,
            "name": meta.get("name"),
            "poster": meta.get("poster"),
            "background": meta.get("background"),
            "description": meta.get("description"),
            "releaseInfo": meta.get("releaseInfo"),
            "imdbRating": meta.get("imdbRating"),
            "genres": meta.get("genres"),
            # Whether the player can resolve streams for this id is the whole question,
            # so say where the id came from instead of implying it was resolved here.
            "behaviorHints": {"defaultVideoId": None},
        })
    return {"metas": metas}


class Handler(BaseHTTPRequestHandler):
    picks_path: Path
    token: str
    picks_mtime: float = 0.0
    picks: dict = {}

    def log_message(self, fmt, *args):  # quieter than the default
        print(f'[{time.strftime("%H:%M:%S")}] {self.address_string()} {fmt % args}', flush=True)

    # ---- helpers -------------------------------------------------------
    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("access-control-allow-origin", "*")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _load_picks(self) -> dict:
        try:
            mtime = self.picks_path.stat().st_mtime
        except FileNotFoundError:
            return {}
        if mtime != Handler.picks_mtime:
            try:
                Handler.picks = json.loads(self.picks_path.read_text())
                Handler.picks_mtime = mtime
                print(f"picks reloaded: {self.picks_path}", flush=True)
            except json.JSONDecodeError as err:
                print(f"picks file is not JSON: {err}", flush=True)
        return Handler.picks or {}

    def _route(self) -> list[str]:
        parsed = urllib.parse.urlparse(self.path)
        self.query = urllib.parse.parse_qs(parsed.query)
        return [p for p in parsed.path.split("/") if p]

    # ---- routes --------------------------------------------------------
    def do_GET(self):  # noqa: N802
        parts = self._route()
        if not parts or parts[0] != self.token:
            # A bare /manifest.json is convenient while testing locally.
            if parts and parts[0] == "manifest.json":
                return self._send(200, build_manifest(self.token))
            return self._send(404, {"error": "not found", "hint": "path must start with the token"})

        rest = parts[1:]
        if rest == ["manifest.json"]:
            return self._send(200, build_manifest(self.token))

        # Stremio/Nuvio path shapes:
        #   /catalog/<type>/<id>.json
        #   /catalog/<type>/<id>/skip=4.json          <- pagination, a whole extra segment
        #   /catalog/<type>/<id>/search=foo.json      <- search, if the catalog declares it
        #   /meta/<type>/<id>.json
        if rest and rest[0] == "catalog" and len(rest) >= 3:
            kind = rest[1]
            tail = rest[2:]
            tail[-1] = tail[-1][:-5] if tail[-1].endswith(".json") else tail[-1]
            # Segments carrying "=" are extras; the one that does not is the catalog id.
            extras = [seg for seg in tail if "=" in seg]
            ids = [seg for seg in tail if "=" not in seg]
            if not ids:
                return self._send(404, {"error": "not found"})
            skip = 0
            search = None
            for seg in extras:
                if seg.startswith("skip="):
                    skip = int(seg[5:] or 0)
                elif seg.startswith("search="):
                    search = urllib.parse.unquote(seg[7:])
            query_skip = (self.query.get("skip") or [None])[0]
            if query_skip:
                skip = int(query_skip or 0)
            cid = ids[0]
            entry = next((e for e in load_store(STORE_PATH)
                          if e["id"] == cid and e["type"] == kind), None)
            if entry:
                return self._send(200, build_catalog(entry["picks"], kind, skip))
            if cid == "deepseek":       # back-compat single row
                return self._send(200, build_catalog(self._load_picks().get(kind) or [], kind, skip))
            return self._send(404, {"error": "unknown catalog", "id": cid, "type": kind})

        if len(rest) == 3 and rest[0] == "meta":
            _, kind, filename = rest
            if not filename.endswith(".json"):
                return self._send(404, {"error": "not found"})
            meta = _fetch_meta(kind, filename[:-5])
            return self._send(200, {"meta": meta} if meta else {"meta": None})

        return self._send(404, {"error": "not found", "path": self.path})


def main() -> int:
    ap = argparse.ArgumentParser(description="Serve a DeepSeek Picks catalog addon.")
    ap.add_argument("--port", type=int, default=8890)
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--token", required=True, help="path segment that acts as the credential")
    ap.add_argument("--picks", default=str(Path(__file__).with_name("picks.json")))
    ap.add_argument("--catalogs", default=str(Path(__file__).with_name("catalogs.json")),
                    help="store of bespoke catalogs the agent has built")
    ap.add_argument("--aiometadata", default="",
                    help="metadata source, e.g. https://aiometadata.elfhosted.com/stremio/<uuid> "
                         "(TMDB via your own AIOmetadata). Falls back to Cinemeta when empty.")
    args = ap.parse_args()

    picks = Path(args.picks).expanduser()
    if not picks.exists():
        picks.write_text(json.dumps({"movie": [], "series": []}, indent=1))
        print(f"created an empty picks file at {picks}", flush=True)

    global AIO_META_BASE
    AIO_META_BASE = (args.aiometadata or "").strip()
    if AIO_META_BASE:
        print(f"metadata: AIOmetadata/TMDB via {AIO_META_BASE}", flush=True)
    else:
        print("metadata: Cinemeta (pass --aiometadata <url> to use TMDB instead)", flush=True)

    global STORE_PATH
    STORE_PATH = Path(args.catalogs).expanduser()

    Handler.picks_path = picks
    Handler.token = args.token
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"addon serving on http://{args.host}:{args.port}/{args.token}/manifest.json", flush=True)
    store = load_store(STORE_PATH)
    if store:
        print(f"catalogs: {len(store)} bespoke row(s) from {STORE_PATH}", flush=True)
        for e in store:
            print(f"  {e['type']:6} {e['id']:16} {e['name'][:36]:36} {len(e['picks'])} titles", flush=True)
    else:
        print(f"catalogs: none yet in {STORE_PATH} — falling back to {picks}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
