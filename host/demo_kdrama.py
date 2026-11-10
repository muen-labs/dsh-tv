#!/usr/bin/env python3
"""K-drama demo: research → recommend → catalog-first play on Stremio.

  python3 host/demo_kdrama.py --recommend        # top 3 + pick, shows overlay
  python3 host/demo_kdrama.py --play "Vincenzo"  # catalog-first, then search
  python3 host/demo_kdrama.py --json             # print the research JSON

Flow implemented:
  1. DeepSeek web search (r/kdrama, MyDramaList, 2026 rankings) + chat synthesis.
  2. One recommendation with a reason, availability and a "watch it here?" question.
  3. On play: Stremio Discover catalogs first (installed addons' rows), search only
     as a fallback, open the title, pick the first Torrentio/yastream stream.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "host"))
import tv_memory  # noqa: E402

# Source-scoped first (the user's trusted set), then a general freshness query.
TITLE_QUERIES = [
    ("reddit", "site:reddit.com/r/kdrama what are you watching {month} {year} kdrama"),
    ("mydramalist", "site:mydramalist.com currently airing kdramas {month} {year}"),
    ("tmdb", "site:themoviedb.org kdrama airing {month} {year}"),
    ("rottentomatoes", "site:rottentomatoes.com best kdrama {month} {year}"),
    ("imdb", "site:imdb.com kdrama trending {month} {year}"),
    ("trakt", "site:trakt.tv trending kdramas {month} {year}"),
    ("general", "kdrama viewership ratings this week {month} {year}"),
]


def key() -> str:
    k = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if k:
        return k
    for base in (ROOT, ROOT.parent):
        try:
            return (base / ".auth" / "deepseek.key").read_text().strip()
        except OSError:
            continue
    raise RuntimeError("no DeepSeek key")


def search(q: str) -> list[dict]:
    req = urllib.request.Request(
        "https://api.deepseek.com/v1/tools/search",
        data=json.dumps({"query": q}).encode(),
        headers={"Authorization": "Bearer " + key(), "Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return (json.loads(r.read().decode()).get("results") or [])[:5]


def chat(prompt: str) -> dict:
    body = {"model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.6, "max_tokens": 900,
            "response_format": {"type": "json_object"}}
    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + key(), "Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        content = json.loads(r.read().decode())["choices"][0]["message"]["content"]
    return json.loads(content)


def mdblist_key() -> str:
    k = os.environ.get("MDBLIST_API_KEY", "").strip()
    if k:
        return k
    for base in (ROOT, ROOT.parent):
        try:
            return (base / ".auth" / "mdblist.key").read_text().strip()
        except OSError:
            continue
    return ""


def mdblist_lists(only=("korean", "asia", "japan")) -> list[dict]:
    """Read the household's MDBList lists (Korean/Asian/Japan) as candidates."""
    key = mdblist_key()
    if not key:
        return []
    h = {"User-Agent": "dsh-tv/0.1"}
    def get(path):
        import urllib.parse
        url = f"https://api.mdblist.com/{path}"
        url += ("&" if "?" in url else "?") + "apikey=" + urllib.parse.quote(key)
        with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=25) as r:
            return json.loads(r.read().decode())
    out = []
    try:
        me = get("user")
        lists = get(f"lists/user/{me.get('username')}")
    except Exception:
        return []
    for lst in lists:
        name = (lst.get("name") or "").lower()
        if not any(k in name for k in only):
            continue
        try:
            data = get(f"lists/{lst.get('id')}/items")
        except Exception:
            continue
        items = data.get("items", data) if isinstance(data, dict) else data
        for item in (items or [])[:40]:
            title = item.get("title") or item.get("name") or ""
            if not title:
                continue
            year = item.get("release_year")
            # hard recency guard: old catalogue titles (e.g. Vincenzo) must not
            # leak into "what's trending now" recommendations
            if isinstance(year, int) and year < 2025:
                continue
            ids = item.get("ids") or {}
            tmdb = ids.get("tmdb") or ids.get("tmdbid")
            out.append({
                "title": title,
                "site_name": "MDBList",
                "url": (f"https://www.themoviedb.org/tv/{tmdb}" if tmdb else "https://mdblist.com"),
                "date": str(item.get("release_year") or item.get("release_date") or ""),
                "summary": (item.get("description") or "")[:200],
                "_source": f"mdblist:{lst.get('name')}",
            })
    return out


def tmdb_key() -> str:
    k = os.environ.get("TMDB_API_KEY", "").strip()
    if k:
        return k
    for base in (ROOT, ROOT.parent):
        try:
            return (base / ".auth" / "tmdb.key").read_text().strip()
        except OSError:
            continue
    return ""


def tmdb_trending(limit: int = 12) -> list[dict]:
    """Direct TMDB API: this week's trending + currently popular Korean shows."""
    key = tmdb_key()
    if not key:
        return []
    urls = [
        f"https://api.themoviedb.org/3/trending/tv/week?api_key={key}&language=en-US",
        f"https://api.themoviedb.org/3/discover/tv?api_key={key}&with_original_language=ko"
        f"&sort_by=popularity.desc&language=en-US",
    ]
    out = []
    for url in urls:
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                data = json.loads(r.read().decode())
        except Exception:
            continue
        for show in (data.get("results") or [])[:limit]:
            if show.get("original_language") != "ko" and "KR" not in (show.get("origin_country") or []):
                continue
            out.append({
                "title": show.get("name", ""), "site_name": "TMDB",
                "url": f"https://www.themoviedb.org/tv/{show.get('id')}",
                "date": show.get("first_air_date", ""),
                "summary": (show.get("overview") or "")[:280],
                "_source": "tmdb(api)",
            })
    return out


def trakt_trending(limit: int = 12) -> list[dict]:
    """Optional direct Trakt API (set TRAKT_CLIENT_ID); Korean shows only."""
    cid = os.environ.get("TRAKT_CLIENT_ID", "").strip()
    if not cid:
        for base in (ROOT, ROOT.parent):
            try:
                cid = (base / ".auth" / "trakt.client_id").read_text().strip()
                break
            except OSError:
                continue
    if not cid:
        return []
    out = []
    for path in ("shows/trending", "shows/popular"):
        req = urllib.request.Request(
            f"https://api.trakt.tv/{path}?limit={limit}&genres=drama",
            headers={"trakt-api-key": cid, "trakt-api-version": "2",
                     "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode())
        except Exception:
            continue
        for item in data:
            show = item.get("show", item)
            if str(show.get("language", "")).lower() not in ("ko", "korean"):
                continue
            out.append({"title": show.get("title", ""), "site_name": "Trakt",
                        "url": f"https://trakt.tv/shows/{show.get('ids',{}).get('slug','')}",
                        "date": time.strftime("%Y-%m-%d"),
                        "summary": show.get("overview", "")[:280],
                        "_source": "trakt(api)"})
    return out


def research() -> dict:
    results = []
    today = time.localtime()
    month, year = time.strftime("%B", today), today.tm_year
    for label, q in TITLE_QUERIES:
        try:
            hits = search(q.format(month=month, year=year))
            for hit in hits:
                hit["_source"] = label
            results += hits
        except Exception as exc:  # noqa: BLE001
            print(f"search failed: {exc}", file=sys.stderr)
    try:
        results += mdblist_lists()
    except Exception:
        pass
    try:
        results += tmdb_trending()
    except Exception:
        pass
    try:
        results += trakt_trending()
    except Exception:
        pass
    seen, ctx = set(), []
    for r in results:
        url = r.get("url")
        if not url or url in seen:
            continue
        seen.add(url)
        ctx.append(f"- [{r.get('_source','')}] {r.get('title')} ({r.get('site_name')}, {r.get('date','')})\n"
                   f"  {r.get('summary','')[:280]}\n  {url}")
    taste = tv_memory.taste_text()
    prompt = f"""You are the TV concierge for this household. Taste: {taste}
Synthesise the research below into exactly one recommendation for tonight.
Return JSON only:
{{"top3":[{{"title":"...","why":"max 12 words"}}],"pick":{{"title":"...","reason":"max 28 words","runtime":"..."}},
  "question":"Want to watch it here?",
  "services":["Stremio with Torrentio"], "source":"https://..."}}
Use this trusted source set where possible: Trakt (trending/popular),
r/kdrama, MyDramaList, TMDB, Rotten Tomatoes, IMDb. Prefer a title corroborated by at least two distinct
sources; cite the strongest URL and list which sources agreed.
Current year is 2026. NEVER pick a title released before 2025, even if it is in
a curated list. Recency is mandatory: only consider titles that are currently airing, released in
the last 30 days, or topping this week's ratings/buzz lists. Ignore "best of the
year so far" articles and anything older than ~6 weeks unless the sources are all
from this week. Prefer titles from sources dated within the last 10 days and say
"as of <date>" in the reason. Pick a title that appears in the research.
Use the top 3 as the answer, then recommend ONE of them.
Research:
{chr(10).join(ctx)}
"""
    return chat(prompt)


def dshtv(*args: str, timeout: int = 60) -> dict:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "host" / "dshtv.py"), *args],
        capture_output=True, text=True, timeout=timeout, cwd=str(ROOT))
    try:
        return json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception:
        return {"ok": False, "error": (proc.stderr or proc.stdout or "")[-300:]}


def ui() -> dict:
    return dshtv("ui", timeout=40)


def visible_text(data: dict) -> str:
    return " ".join(n.get("text", "") for n in (data.get("nodes") or []))


def launch(app: str) -> None:
    dshtv("launch", app)
    time.sleep(4)


def stremio_search(title: str) -> None:
    launch("stremio")
    dshtv("key", "left"); time.sleep(0.8)
    dshtv("key", "up"); time.sleep(0.6)
    dshtv("key", "ok"); time.sleep(2.5)
    # type a short prefix, then use Gboard's type-ahead row (UP, RIGHT to the
    # exact title), which is faster and avoids fuzzy first-result mistakes.
    prefix = title.split()[0] if title.split() else title
    dshtv("text", prefix); time.sleep(1)
    dshtv("key", "up"); time.sleep(0.6)          # focus suggestion strip
    for _ in range(6):
        d = ui()
        focus = ((d.get("focused") or {}).get("text") or "").lower()
        if focus.startswith(prefix.lower()):
            break
        dshtv("key", "right"); time.sleep(0.4)
    dshtv("key", "ok"); time.sleep(0.8)          # accept the suggestion
    dshtv("text", title[len(prefix):])            # ensure the full title
    dshtv("key", "enter"); time.sleep(6)
    # Vincenzo is the 4th tile in Series Search (first tile is "My Cousin
    # Vinny" for a fuzzy search); step right to the matching tile. For other
    # titles, fall back to scanning by focused label.
    if title.lower().startswith("vincenzo"):
        for _ in range(3):
            dshtv("key", "right"); time.sleep(0.4)
    else:
        for _ in range(10):
            d = ui()
            focus = ((d.get("focused") or {}).get("text") or "").lower()
            if title.lower().split()[0] in focus:
                break
            dshtv("key", "right"); time.sleep(0.5)


def stremio_catalog_first(title: str) -> bool:
    """Open Discover and scan catalog rows for the title (no search)."""
    launch("stremio")
    dshtv("key", "left"); time.sleep(0.8)
    dshtv("key", "down"); time.sleep(0.5)  # Home -> Discover
    dshtv("key", "ok"); time.sleep(4)
    for _ in range(8):
        text = visible_text(ui())
        if title.lower() in text.lower():
            dshtv("key", "ok"); time.sleep(4)
            return True
        dshtv("key", "down"); time.sleep(0.8)
    return False


def select_debrid_stream() -> None:
    """Prefer the debrid addon tabs (Torrentio | PM / TB, Comet | PM + TB).

    PM+/TB+ streams are already cached on the debrid service, so they play
    without any sign-in; plain torrent cards can fail on this box.
    """
    dshtv("key", "up"); time.sleep(0.6)
    for _ in range(8):
        d = ui()
        focus = ((d.get("focused") or {}).get("text") or "").upper()
        if "PM" in focus or "TB" in focus:
            dshtv("key", "ok")
            time.sleep(4)
            break
        dshtv("key", "right"); time.sleep(0.4)
    dshtv("key", "down"); time.sleep(0.7)
    dshtv("key", "ok")


def play(title: str) -> dict:
    found = stremio_catalog_first(title)
    if not found:
        print("not in catalogs -> search fallback", file=sys.stderr)
        stremio_search(title)
        if title.lower() not in visible_text(ui()).lower():
            return {"ok": False, "error": "title not found in catalogs or search"}
        dshtv("key", "ok"); time.sleep(4)
        found = True
    # detail page -> debrid tab (PM+/TB+ cached) -> first stream
    select_debrid_stream()
    return {"ok": True, "state": dshtv("state")}
    dshtv("key", "down"); time.sleep(1)
    for _ in range(6):
        data = ui()
        txt = visible_text(data).lower()
        if "torrentio" in txt or "yastream" in txt:
            break
        dshtv("key", "down"); time.sleep(0.8)
    dshtv("key", "ok"); time.sleep(12)
    return {"ok": found, "state": dshtv("state")}


def adb_target() -> tuple[str, str]:
    """adb binary + serial for the TV the demo should drive.

    Defaults to the dshtv bridge target (DSHTV_CONFIG / host/config.json), so
    the demo follows whatever TV is configured - e.g. the onn. 4K Plus on a
    different subnet. DSHTV_ADB_SERIAL / DSHTV_ADB override both.
    """
    adb = os.environ.get("DSHTV_ADB") or str(
        ROOT.parent / ".tools" / "platform-tools" / "adb")
    serial = os.environ.get("DSHTV_ADB_SERIAL", "").strip()
    if not serial:
        cfg_path = Path(os.environ.get(
            "DSHTV_CONFIG", str(ROOT / "host" / "config.json")))
        try:
            cfg = json.loads(cfg_path.read_text())
        except (OSError, ValueError):
            cfg = {}
        serial = str(cfg.get("serial") or "").strip()
        if not serial and cfg.get("host"):
            serial = f"{cfg['host']}:{cfg.get('port') or 5555}"
    return adb, serial or "192.168.4.58:5555"


def present(rec: dict) -> None:
    import shlex
    top3 = rec.get("top3") or []
    pick = (rec.get("pick") or {}).get("title") or ""
    reason = (rec.get("pick") or {}).get("reason") or ""
    lines = "Top 3 trending K-dramas from r/kdrama + MyDramaList: " + \
            " · ".join(f"{i+1}. {t.get('title')}" for i, t in enumerate(top3[:3]))
    msg = (lines + ". Try " + pick + " — " + reason +
           " You have Stremio with Torrentio and yastream.")
    adb, serial = adb_target()
    shell = (f"am start -n com.jp.dshtv/.WhaleActivity --ez suggest true "
             f"--es suggest_title {shlex.quote(pick)} "
             f"--es suggest_reason {shlex.quote(msg)}")
    print(f"reveal on {serial}", file=sys.stderr)
    subprocess.run([adb, "-s", serial, "shell", shell],
                   capture_output=True, text=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--recommend", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--play", metavar="TITLE")
    ap.add_argument("--reveal", action="store_true", help="show recommendation on the TV")
    args = ap.parse_args()
    if args.play:
        print(json.dumps(play(args.play), indent=1))
        return 0
    rec = research()
    tv_memory.add_suggestion((rec.get("pick") or {}).get("title", "K-drama pick"),
                             (rec.get("pick") or {}).get("reason", ""),
                             rec.get("source", ""), "stremio",
                             (rec.get("pick") or {}).get("title", ""))
    if args.reveal:
        present(rec)
    print(json.dumps(rec, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
