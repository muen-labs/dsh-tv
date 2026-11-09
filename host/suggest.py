#!/usr/bin/env python3
"""Generate one personalised TV suggestion with DSH (web search + local taste).

    python3 host/suggest.py --topic "new K-drama everyone is talking about"
    python3 host/suggest.py --latest

The result is stored in host/tv-memory.db and can be pushed to the TV overlay.
Uses the DeepSeek API directly (search + chat) so it works from a sandboxed
agent; falls back to DSH only if the API key is missing.
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

KEY_FILE = ROOT / ".auth" / "deepseek.key"
DSH_HOME = Path(os.environ.get("DSH_HOME") or Path.home() / ".dsh")

PROMPT = """You are the TV concierge for this household. You are NOT a scripted assistant:
use the web_search tool to find something genuinely worth watching, then answer.

Local taste memory:
{taste}

Installed TV services: Netflix, Prime Video, Stremio, YouTube, TiviMate, CloudStream, Nuvio, OwnTV.
Today is {today}.

Topic/angle: {topic}

Pick exactly ONE title that fits the taste above and is new/trending now.
Rules:
- Prefer something available on an installed service; say where it is available.
- Do not pick anything in the avoid list. Do not repeat a recent request.
- One title, with a short human reason (max 28 words) that mentions why it fits them.
- Use a real source URL from your search.

Reply with ONLY this JSON object, no markdown:
{{"title": "...", "reason": "...", "source": "https://...", "app": "netflix|prime|stremio|youtube|other", "query": "short search phrase"}}
"""


def api_key() -> str:
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if key:
        return key
    for base in (ROOT, ROOT.parent):
        try:
            return (base / ".auth" / "deepseek.key").read_text(encoding="utf-8").strip()
        except OSError:
            continue
    return ""


def web_search(query: str, limit: int = 6) -> list[dict]:
    key = api_key()
    if not key:
        return []
    req = urllib.request.Request(
        "https://api.deepseek.com/v1/tools/search",
        data=json.dumps({"query": query}).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return (data.get("results") or [])[:limit]


def chat_json(prompt: str) -> dict | None:
    key = api_key()
    if not key:
        return None
    body = {
        "model": os.environ.get("WHALE_SUGGEST_MODEL", "deepseek-chat"),
        "messages": [
            {"role": "system", "content": "You are a TV concierge. Reply with JSON only."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 400,
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
    return parse_json(content or "")


def dsh(prompt: str, timeout: int = 240) -> tuple[str, str]:
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not key:
        try:
            key = KEY_FILE.read_text(encoding="utf-8").strip()
        except OSError:
            pass
    cmd = ["dsh", "--profile", "headless", "--json", prompt]
    env = dict(os.environ)
    env.update({"DSH_HOME": str(DSH_HOME), "DEEPSEEK_API_KEY": key})
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT),
                          env=env, timeout=timeout)
    final, error = "", ""
    for line in (proc.stdout or "").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") == "final" and event.get("text"):
            final = event["text"]
        if event.get("type") == "status" and event.get("phase") == "turn_end":
            error = event.get("error") or ""
    return final.strip(), error


def parse_json(text: str) -> dict | None:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        obj = json.loads(text[start:end + 1])
    except ValueError:
        return None
    if not obj.get("title"):
        return None
    return obj


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", default="something new and talked about this week")
    ap.add_argument("--latest", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.latest:
        print(json.dumps(tv_memory.latest_suggestion(), ensure_ascii=False, indent=1))
        return 0

    taste = tv_memory.taste_text()
    today = time.strftime("%A, %d %B %Y")
    data = None
    try:
        results = web_search(f"{args.topic} — what to watch this week {time.strftime('%Y')}", 6)
        context = "\n".join(
            f'- {r.get("title")} | {r.get("site_name")} | {r.get("date","")} | {r.get("url")}\n'
            f'  {r.get("summary","")[:320]}' for r in results)
        prompt = PROMPT.format(taste=taste, topic=args.topic, today=today)
        prompt += f"\n\nWeb results to choose from:\n{context}"
        data = chat_json(prompt)
    except Exception as exc:  # noqa: BLE001
        data = None
        err = f"{type(exc).__name__}: {exc}"
    if not data:
        final, error = dsh(prompt if 'prompt' in dir() else
                           PROMPT.format(taste=taste, topic=args.topic, today=today))
        if not error:
            data = parse_json(final)
        else:
            print(json.dumps({"ok": False, "error": error}, ensure_ascii=False))
            return 1
    if not data:
        print(json.dumps({"ok": False, "error": "no JSON suggestion"}, ensure_ascii=False))
        return 1
    if not args.dry_run:
        sid = tv_memory.add_suggestion(
            data["title"], data.get("reason", ""), data.get("source", ""),
            data.get("app", ""), data.get("query", data["title"]))
        data["id"] = sid
    data["ok"] = True
    print(json.dumps(data, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
