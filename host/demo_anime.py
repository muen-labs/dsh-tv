#!/usr/bin/env python3
"""Trending-anime demo: AniList trends -> FOR YOU overlay -> Stremio playback.

The narrative this drives:

  1. "Suggest an anime that is trending."  ->  AniList's currently-airing
     TRENDING_DESC top 3 (a legit anime database; MAL/AniList-style score and
     popularity). One title is picked and shown in the assistant's FOR YOU card.
  2. The assistant opens Stremio, searches the title, opens the show, goes to the
     currently-airing season, picks an H.264 source (the boxes capture video in
     screencap/screenrecord only for AVC, not HEVC) and plays a few seconds.

Usage (the TV and daemon are configured through DSHTV_CONFIG as for dshtv.py):

    python3 host/demo_anime.py --recommend            # print top 3 + pick
    python3 host/demo_anime.py --recommend --reveal   # + show the FOR YOU overlay
    python3 host/demo_anime.py --play "The Apothecary Diaries"
    python3 host/demo_anime.py --demo --record /tmp/anime-demo.mp4
        # full run: reveal the pick, drive Stremio, play ~10 s, record the TV

The play leg targets the box used for the demo: it expects Stremio with
Torrentio (PM+ debrid cached sources) and picks the second source card, which is
the H.264 release on that box (the first is HEVC: it plays, but hardware
overlay planes are not captured by screencap/screenrecord, so it looks black).
The source row also contains a "support the project" card; the script clamps
left before moving right so it can never open the donation page by accident.

The published demo video (docs/demo.mp4) is a real capture from the 4K Plus,
edited from three takes — on this box screenrecord stops when a video player
takes the display, so the UI legs and the playback were captured separately.
"""
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "host"))
from demo_kdrama import (  # noqa: E402  (shared TV driver)
    adb_target,
    dshtv,
    launch,
    present,
    ui,
    visible_text,
)

ANILIST = "https://graphql.anilist.co"
TRENDING_QUERY = """
query ($perPage: Int) {
  Page(perPage: $perPage) {
    media(type: ANIME, sort: TRENDING_DESC, status: RELEASING) {
      id
      title { romaji english }
      averageScore
      popularity
      siteUrl
      episodes
      genres
    }
  }
}
"""


def trending(limit: int = 5) -> list[dict]:
    """Currently-airing anime ordered by AniList trending score."""
    body = json.dumps({"query": TRENDING_QUERY, "variables": {"perPage": limit}}).encode()
    req = urllib.request.Request(
        ANILIST, data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "dsh-tv-demo/1.0 (https://github.com/muen-labs/dsh-tv)",
        },
        method="POST")
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.load(response)
    media = data.get("data", {}).get("Page", {}).get("media", [])
    out = []
    for item in media:
        title = (item.get("title") or {})
        out.append({
            "title": title.get("english") or title.get("romaji"),
            "romaji": title.get("romaji"),
            "score": item.get("averageScore"),
            "popularity": item.get("popularity"),
            "episodes": item.get("episodes"),
            "genres": item.get("genres") or [],
            "url": item.get("siteUrl"),
        })
    return out


def recommendation(limit: int = 8, pick_hint: str = "") -> dict:
    top = trending(limit)
    if not top:
        return {"ok": False, "error": "AniList returned no trending anime"}
    top3 = top[:3]
    pick = top[0]
    rank = 1
    if pick_hint:
        needle = pick_hint.lower()
        for i, candidate in enumerate(top):
            if needle in (candidate["title"] or "").lower():
                pick, rank = candidate, i + 1
                break
    reason = (
        f"#{rank} on AniList's currently-airing trending list (as of {time.strftime('%Y-%m-%d')}): "
        f"{pick['title']} — score {pick['score']}, {pick['popularity']:,} followers, "
        f"{pick['episodes'] or '?'} eps" + (f" · {', '.join(pick['genres'][:2])}" if pick["genres"] else "")
    )
    return {
        "ok": True,
        "source": "AniList trending (currently airing)",
        "asOf": time.strftime("%Y-%m-%d"),
        "top3": [{"title": t["title"], "score": t["score"], "url": t["url"]} for t in top3],
        "pick": {"title": pick["title"], "reason": reason, "url": pick["url"]},
        "question": f"Want to watch {pick['title']} here?",
    }


# --------------------------------------------------------------------------- #
# Stremio driving (blind key choreography, verified with screenshots/state)
# --------------------------------------------------------------------------- #

def _key(k: str, wait: float = 0.5) -> None:
    dshtv("key", k)
    time.sleep(wait)


def _key_event(code: int, wait: float = 0.6) -> None:
    """Raw keyevent (for keys dshtv's map does not name, e.g. ENTER)."""
    adb, serial = adb_target()
    subprocess.run([adb, "-s", serial, "shell", "input", "keyevent", str(code)],
                   capture_output=True, text=True)
    time.sleep(wait)


def _reset_stremio() -> None:
    """Make sure Stremio starts at Home, not inside a stale player."""
    adb, serial = adb_target()
    subprocess.run([adb, "-s", serial, "shell", "am", "force-stop", "com.stremio.one"],
                   capture_output=True, text=True)
    time.sleep(1.0)


def open_search() -> None:
    """From the Stremio home: sidebar -> Search (Search is the top row)."""
    _key("left", 0.9)
    _key("up", 0.5)
    _key("up", 0.5)        # clamps on Search at the top of the rail
    _key("ok", 2.0)


def open_show(title: str) -> bool:
    """Search Stremio and open the first matching series card."""
    _reset_stremio()
    launch("stremio")
    time.sleep(2.0)
    open_search()
    dshtv("text", title.split(" Season")[0])   # Stremio search is fuzzy
    time.sleep(2.8)
    _key("up", 0.8)         # IME suggestion strip
    _key_event(66, 3.2)     # ENTER accepts the suggestion / runs the search
    _key("down", 0.8)       # results -> first card
    _key("ok", 4.0)         # open the detail page
    return True


def play_episode(season_tabs_right: int = 2, episode_down: int = 1, source_right: int = 1) -> bool:
    """From a detail page: season tab -> episode -> sources -> H.264 stream -> play.

    The detail page remembers the last season watched, so normalise the tab row
    first: LEFT clamps on Season 1, then RIGHT x2 lands on the currently-airing
    Season 3 regardless of where Stremio left the selection.
    """
    _key("up", 0.8)        # season tab row
    for _ in range(6):
        _key("left", 0.25)  # clamp on Season 1 (no wrap on this tab row)
    for _ in range(season_tabs_right):
        _key("right", 0.35)
    _key("ok", 2.5)        # select the currently-airing season
    for _ in range(episode_down):
        _key("down", 0.5)
    _key("ok", 13.0)       # open sources; addons take ~8-12 s to answer
    # The source row also carries a donation card on the right. Clamp left to
    # the first real source, then step to the H.264 release: the first card is
    # HEVC (plays but captures black), the second is the H.264 release.
    for _ in range(6):
        _key("left", 0.25)
    for _ in range(source_right):
        _key("right", 0.4)
    _key("ok", 8.0)        # start playback
    return True


def playback_state() -> str:
    adb, serial = adb_target()
    proc = subprocess.run([adb, "-s", serial, "shell", "dumpsys", "media_session"],
                          capture_output=True, text=True)
    for line in proc.stdout.splitlines():
        if "state=PlaybackState" in line and "package=com.stremio.one" in line:
            return line.strip()
    for line in proc.stdout.splitlines():
        if "state=PlaybackState" in line:
            return line.strip()
    return ""


def hold_playback(seconds: int) -> None:
    time.sleep(seconds)


def record_demo(output: str, hold: int = 10, pick_hint: str = "") -> int:
    """Full recorded demo: overlay -> Stremio -> play -> hold; returns exit code."""
    adb, serial = adb_target()
    remote = f"/sdcard/anime-demo.mp4"
    duration = 60
    rec = subprocess.Popen(
        [adb, "-s", serial, "shell", "screenrecord",
         "--size", "1920x1080", "--bit-rate", "6000000",
         "--time-limit", str(duration), remote],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        rec_data = recommendation(pick_hint=pick_hint)
        reason = rec_data["pick"]["reason"]
        title = rec_data["pick"]["title"]
        shell = (f"am start -n com.jp.dshtv/.WhaleActivity --ez suggest true "
                 f"--es suggest_title {shlex.quote(title)} "
                 f"--es suggest_reason {shlex.quote(reason + ' Opening Stremio…')}")
        subprocess.run([adb, "-s", serial, "shell", shell], capture_output=True, text=True)
        time.sleep(3.5)
        _key("back", 1.5)                     # close the recommendation modal
        open_show(title)
        play_episode()
        time.sleep(2)
        state = playback_state()
        print("playback:", state or "(no media session)", file=sys.stderr)
        hold_playback(hold)
        _key("ok", 1.0)                        # show the player controls for the take
        time.sleep(2)
    finally:
        try:
            rec.terminate()
        except Exception:
            pass
        rec.wait(timeout=10)
        time.sleep(1)
        local = Path(output)
        subprocess.run([adb, "-s", serial, "pull", remote, str(local)],
                       capture_output=True, text=True)
        print(f"recording: {local}", file=sys.stderr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--recommend", action="store_true")
    ap.add_argument("--reveal", action="store_true", help="show the pick in the TV overlay")
    ap.add_argument("--play", metavar="TITLE")
    ap.add_argument("--demo", action="store_true", help="reveal + drive Stremio + play")
    ap.add_argument("--record", metavar="FILE", help="record the TV screen during --demo")
    ap.add_argument("--hold", type=int, default=8, help="seconds of playback to hold")
    ap.add_argument("--pick", metavar="SUBSTRING", default="",
                    help="prefer a trending title containing this text (e.g. Apothecary)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.demo or args.record:
        return record_demo(args.record or "/tmp/anime-demo.mp4", args.hold, args.pick)

    if args.recommend:
        rec = recommendation(pick_hint=args.pick)
        print(json.dumps(rec, ensure_ascii=False, indent=2))
        if args.reveal:
            present(rec)
        return 0 if rec.get("ok") else 1

    if args.play:
        open_show(args.play)
        play_episode()
        time.sleep(3)
        state = playback_state()
        print(json.dumps({"ok": "PLAYING" in state, "state": state}, ensure_ascii=False))
        return 0 if "PLAYING" in state else 1

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
