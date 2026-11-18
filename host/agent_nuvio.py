#!/usr/bin/env python3
"""One-call VOD control for Nuvio Agent (the agent-first fork).

The voice assistant runs this instead of a five-tool dance: search, pick a sane
stream, play it, verify the player opened, print JSON with a sentence to speak.

    python3 dshtv/agent_nuvio.py ensure "the matrix"
    python3 dshtv/agent_nuvio.py ensure "inception" --year 2010
    python3 dshtv/agent_nuvio.py search "dune"

Exit code 0 = playing (or found for `search`), 1 = could not.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

# Where the Nuvio Agent app listens and its token (AGENT_API_PORT / AGENT_API_TOKEN from the
# app's local.properties). Both come from the environment; nothing is hardcoded.
BASE = os.environ.get("NUVIO_AGENT_API", "").rstrip("/")  # e.g. http://<tv-ip>:8899
TOKEN = os.environ.get("NUVIO_AGENT_TOKEN", "")
HERE = os.path.dirname(os.path.abspath(__file__))
DSHTV = os.path.join(HERE, "dshtv.py")
PACKAGE = "com.nuvio.tv.agent"

BAD_STREAM = re.compile(r"\b(dv|dolby\s*vision|remux)\b", re.IGNORECASE)
BAD_CACHE = re.compile(r"\[tb download\]", re.IGNORECASE)
SIZE = re.compile(r"(\d+(?:\.\d+)?)\s*(GB|MB)", re.IGNORECASE)


def call(method: str, path: str, payload=None, params=None, timeout: float = 70):
    if not BASE or not TOKEN:
        sys.exit("agent_nuvio: set NUVIO_AGENT_API (http://<tv-ip>:<port>) and NUVIO_AGENT_TOKEN")
    url = BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = None
    headers = {"Authorization": f"Bearer {TOKEN}"}
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        try:
            return {"error": json.loads(body)}
        except json.JSONDecodeError:
            return {"error": {"message": body}}
    except Exception as exc:  # noqa: BLE001 - report, never crash the voice turn
        return {"error": {"message": str(exc)}}


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = re.sub(r"\(\d{4}\)", "", text)
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def app_running() -> bool:
    return "error" not in call("GET", "/v1/health", timeout=4)


def launch_app() -> None:
    subprocess.run(
        ["python3", DSHTV, "launch", "--package", PACKAGE],
        capture_output=True, text=True, timeout=60,
    )
    for _ in range(15):
        if app_running():
            return
        time.sleep(1)


def pick_item(items, query: str, year: int | None = None):
    wanted = norm(query)
    best, best_score = None, -1.0
    for item in items or []:
        name = item.get("name") or ""
        score = 0.0
        if norm(name) == wanted:
            score += 5
        elif wanted and wanted in norm(name):
            score += 2
        if year and str(year) in str(item.get("year") or ""):
            score += 1.5
        if (item.get("id") or "").startswith("tt"):
            score += 0.5
        if score > best_score:
            best, best_score = item, score
    return best


def size_gb(stream) -> float | None:
    match = SIZE.search(stream.get("title") or "")
    if not match:
        return None
    value = float(match.group(1))
    return value / 1024 if match.group(2).upper() == "MB" else value


def pick_streams(streams, limit: int = 4):
    """Best-first, sized for a 2 GB box with a ~400 MB app heap."""
    candidates = [s for s in streams or [] if s.get("url") and not BAD_CACHE.search(s.get("name") or "")]
    candidates = [s for s in candidates if not BAD_STREAM.search(f"{s.get('name')} {s.get('title')}")]
    if not candidates:
        return []

    def quality(s):
        text = f"{s.get('name')} {s.get('title')}"
        text_l = text.lower()
        score = 0.0
        if "1080p" in text_l:
            score += 6
        elif "720p" in text_l:
            score += 4
        elif "2160p" in text_l or "4k" in text_l:
            score -= 2
        if "x264" in text_l or "avc" in text_l or "h.264" in text_l:
            score += 5
        if "x265" in text_l or "hevc" in text_l:
            score -= 3
        if "10bit" in text_l or "10 bit" in text_l:
            score -= 2
        gb = size_gb(s)
        if gb is not None:
            if gb <= 4:
                score += 5
            elif gb <= 8:
                score += 3
            elif gb <= 12:
                score += 0
            else:
                score -= 5
        if "[tb+]" in (s.get("name") or "").lower():
            score += 3
        return score

    return sorted(candidates, key=quality, reverse=True)[:limit]


def say_play(stream, title: str) -> str:
    name = (stream.get("name") or "").replace("\n", " ").lower()
    quality = "1080p" if "1080p" in name else ("720p" if "720p" in name else ("4K" if "4k" in name else ""))
    return f"{title} is playing on Nuvio Agent" + (f" in {quality}" if quality else "") + "."


def ensure(query: str, year: int | None, content_type: str):
    started = time.time()
    if not app_running():
        launch_app()
    if not app_running():
        return {"ok": False, "action": "launch_failed", "say": "Nuvio Agent did not start."}

    found = call("GET", "/v1/search", params={"q": query, "type": content_type})
    items = found.get("items") or []
    item = pick_item(items, query, year)
    if not item:
        return {"ok": False, "action": "not_found", "say": f"I could not find {query}."}

    resolved = call(
        "GET", "/v1/streams",
        params={"type": item.get("type") or content_type, "id": item["id"]},
    )
    if resolved.get("error"):
        return {"ok": False, "action": "no_streams", "say": f"I found {item['name']} but no streams."}
    candidates = pick_streams(resolved.get("streams"))
    if not candidates:
        return {"ok": False, "action": "no_streams", "say": f"I found {item['name']} but no playable stream."}

    last_failure = "player_not_open"
    for stream in candidates:
        played = call("POST", "/v1/play", {
            "url": stream["url"],
            "title": item["name"],
            "content_type": item.get("type") or content_type,
            "content_id": item.get("id"),
            "poster": item.get("poster"),
        })
        if played.get("error"):
            last_failure = "play_rejected"
            continue

        deadline = time.time() + 25
        restarted = False
        while time.time() < deadline:
            state = call("GET", "/v1/state", timeout=8)
            now = state.get("now_playing") or {}
            play = state.get("playback") or {}
            playing = (
                int(play.get("position_ms") or 0) > 1500
                and (play.get("video_id") == item.get("id") or norm(play.get("title") or "") == norm(item.get("name") or ""))
            )
            if state.get("player_open") and playing:
                return {
                    "ok": True,
                    "action": "played",
                    "title": item["name"],
                    "id": item.get("id"),
                    "stream": (stream.get("title") or "")[:160],
                    "size_gb": size_gb(stream),
                    "seconds": round(time.time() - started, 1),
                    "say": say_play(stream, item["name"]),
                }
            if state.get("state_rev", 0) <= 2 and not now:
                restarted = True  # the app died and restored an older player
            time.sleep(1)
        last_failure = "app_restarted_or_stream_failed" if restarted else "player_not_open"

    return {
        "ok": False,
        "action": last_failure,
        "say": f"I found {item['name']} but the player could not hold the stream.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("ensure")
    p.add_argument("query")
    p.add_argument("--year", type=int)
    p.add_argument("--type", default="movie", choices=["movie", "series"])
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--type", default="movie")
    args = parser.parse_args()

    if args.cmd == "search":
        found = call("GET", "/v1/search", params={"q": args.query, "type": args.type})
        items = found.get("items") or []
        print(json.dumps({"ok": bool(items), "items": [
            {"id": i.get("id"), "name": i.get("name"), "year": i.get("year"), "type": i.get("type")}
            for i in items[:10]
        ]}, ensure_ascii=False, indent=1))
        return 0 if items else 1

    result = ensure(args.query, args.year, args.type)
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
