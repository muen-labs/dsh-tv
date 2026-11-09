#!/usr/bin/env python3
"""Local TV memory for the Whale-chan/DSH assistant.

Everything stays on the Mac. Records commands, app usage, explicit feedback and
generated suggestions, and exposes a compact taste summary that the voice daemon
injects into every DSH prompt.

    python3 host/tv_memory.py summary
    python3 host/tv_memory.py log --kind watch --app stremio --query "k-drama"
    python3 host/tv_memory.py feedback --subject "When the Phone Rings" --verdict like
    python3 host/tv_memory.py suggest-list
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.environ.get("WHALE_MEMORY_DB") or ROOT / "host" / "tv-memory.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts REAL NOT NULL,
  kind TEXT NOT NULL,
  app TEXT,
  query TEXT,
  detail TEXT
);
CREATE TABLE IF NOT EXISTS feedback (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts REAL NOT NULL,
  subject TEXT NOT NULL,
  verdict TEXT NOT NULL,
  detail TEXT
);
CREATE TABLE IF NOT EXISTS suggestions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts REAL NOT NULL,
  title TEXT NOT NULL,
  reason TEXT,
  source TEXT,
  action_app TEXT,
  action_query TEXT,
  status TEXT DEFAULT 'new'
);
CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);
"""

STOP = {"the","a","an","and","or","on","in","to","for","of","with","is","it","this",
        "that","open","launch","search","find","play","watch","put","please","can",
        "you","me","my","i","want","some","new","show","app","tv","on","at","from"}


def connect() -> sqlite3.Connection:
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    return db


def log_event(kind: str, app: str | None = None, query: str | None = None,
              detail: str | None = None, conn: sqlite3.Connection | None = None) -> int:
    db = conn or connect()
    cur = db.execute("INSERT INTO events(ts, kind, app, query, detail) VALUES (?,?,?,?,?)",
                     (time.time(), kind, app, query, detail))
    db.commit()
    return int(cur.lastrowid)


def feedback(subject: str, verdict: str, detail: str | None = None) -> None:
    db = connect()
    db.execute("INSERT INTO feedback(ts, subject, verdict, detail) VALUES (?,?,?,?)",
               (time.time(), subject, verdict, detail))
    db.commit()


def add_suggestion(title: str, reason: str = "", source: str = "",
                   action_app: str = "", action_query: str = "") -> int:
    db = connect()
    # don't repeat an identical suggestion within a week
    row = db.execute(
        "SELECT id FROM suggestions WHERE title = ? AND ts > ?",
        (title, time.time() - 7 * 86400)).fetchone()
    if row:
        return int(row["id"])
    cur = db.execute(
        "INSERT INTO suggestions(ts, title, reason, source, action_app, action_query) VALUES (?,?,?,?,?,?)",
        (time.time(), title, reason, source, action_app, action_query))
    db.commit()
    return int(cur.lastrowid)


def latest_suggestion(status: str | None = None) -> dict | None:
    db = connect()
    sql = "SELECT * FROM suggestions"
    args: tuple = ()
    if status:
        sql += " WHERE status = ?"
        args = (status,)
    sql += " ORDER BY ts DESC LIMIT 1"
    row = db.execute(sql, args).fetchone()
    return dict(row) if row else None


def mark_suggestion(sid: int, status: str) -> None:
    db = connect()
    db.execute("UPDATE suggestions SET status = ? WHERE id = ?", (status, sid))
    db.commit()


def _keywords(rows: list[sqlite3.Row], limit: int = 8) -> list[str]:
    counts: dict[str, int] = {}
    for row in rows:
        text = (row["query"] or "") + " " + (row["detail"] or "")
        for w in re.findall(r"[a-zA-Z][a-zA-Z0-9'-]{2,}", text.lower()):
            if w in STOP:
                continue
            counts[w] = counts.get(w, 0) + 1
    return [w for w, _ in sorted(counts.items(), key=lambda kv: -kv[1])[:limit]]


def summary(days: int = 30) -> dict:
    db = connect()
    cutoff = time.time() - days * 86400
    events = db.execute(
        "SELECT * FROM events WHERE ts > ? ORDER BY ts DESC LIMIT 400", (cutoff,)).fetchall()
    apps = db.execute(
        "SELECT app, COUNT(*) n FROM events WHERE ts > ? AND app IS NOT NULL "
        "GROUP BY app ORDER BY n DESC LIMIT 8", (cutoff,)).fetchall()
    fb = db.execute(
        "SELECT subject, verdict FROM feedback WHERE ts > ? ORDER BY ts DESC LIMIT 30",
        (cutoff,)).fetchall()
    return {
        "window_days": days,
        "events": len(events),
        "top_apps": [{"app": r["app"], "count": r["n"]} for r in apps],
        "recent_queries": [r["query"] for r in events if r["query"]][:10],
        "keywords": _keywords(events),
        "likes": [r["subject"] for r in fb if r["verdict"] == "like"],
        "dislikes": [r["subject"] for r in fb if r["verdict"] in ("dislike", "not_interested")],
        "last_suggestion": latest_suggestion(),
    }


def taste_text(days: int = 30) -> str:
    s = summary(days)
    if s["events"] == 0 and not s["likes"] and not s["dislikes"]:
        return "No viewing history yet; ask before assuming taste."
    parts = []
    if s["top_apps"]:
        parts.append("frequent apps: " + ", ".join(f'{a["app"]} ({a["count"]})' for a in s["top_apps"]))
    if s["keywords"]:
        parts.append("recurring topics: " + ", ".join(s["keywords"]))
    if s["recent_queries"]:
        parts.append("recent requests: " + " | ".join(s["recent_queries"][:5]))
    if s["likes"]:
        parts.append("liked: " + ", ".join(s["likes"]))
    if s["dislikes"]:
        parts.append("avoid: " + ", ".join(s["dislikes"]))
    return "; ".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser(description="Local TV memory")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("summary").add_argument("--days", type=int, default=30)
    p = sub.add_parser("log")
    p.add_argument("--kind", default="command")
    p.add_argument("--app")
    p.add_argument("--query")
    p.add_argument("--detail")
    p = sub.add_parser("feedback")
    p.add_argument("--subject", required=True)
    p.add_argument("--verdict", required=True, choices=["like", "dislike", "not_interested", "watched"])
    p.add_argument("--detail")
    p = sub.add_parser("suggest-add")
    p.add_argument("--title", required=True)
    p.add_argument("--reason", default="")
    p.add_argument("--source", default="")
    p.add_argument("--app", default="")
    p.add_argument("--query", default="")
    p = sub.add_parser("suggest-list")
    p.add_argument("--status", default=None)
    p = sub.add_parser("suggest-mark")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--status", required=True)
    args = ap.parse_args()
    if args.cmd == "summary":
        out = summary(args.days)
    elif args.cmd == "log":
        out = {"ok": True, "id": log_event(args.kind, args.app, args.query, args.detail)}
    elif args.cmd == "feedback":
        feedback(args.subject, args.verdict, args.detail)
        out = {"ok": True}
    elif args.cmd == "suggest-add":
        out = {"ok": True, "id": add_suggestion(args.title, args.reason, args.source,
                                                args.app, args.query)}
    elif args.cmd == "suggest-list":
        out = latest_suggestion(args.status) or {}
    else:
        mark_suggestion(args.id, args.status)
        out = {"ok": True}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
