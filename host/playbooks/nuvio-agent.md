# Nuvio Agent — playbook

Package `com.nuvio.tv.agent` · label **Nuvio Agent**
Component `com.nuvio.tv.agent/com.nuvio.tv.MainActivity`
Role: Stremio-style movies/series player with an agent API. Use it for
**"play a movie / episode"** — not for live TV.

## Preferred path: the API, not the D-pad

The app runs an HTTP control plane on the port set by `AGENT_API_PORT` when the app
was built (default 8899), and only if `AGENT_API_TOKEN` was set. Export both first:

```bash
export NUVIO_AGENT_API="http://<tv-ip>:8899"
export NUVIO_AGENT_TOKEN="<your-agent-token>"

python3 dshtv/dshtv.py launch --package com.nuvio.tv.agent
sleep 4

# search, pick a 1080p stream and play it, in one call
python3 dshtv/agent_nuvio.py ensure "the matrix"

# or step by step
python3 dshtv/agent_nuvio.py search "the matrix"

# confirm
curl -s -H "Authorization: Bearer $NUVIO_AGENT_TOKEN" "$NUVIO_AGENT_API/v1/state"
```

Success is `"player_open": true` and a `route` starting with `player/`.
Series use `--season N --episode N` on `streams`/`play-stream`; the series id is
also a `tt…` id.

## Picking a stream on this box

- Prefer **1080p** H.264 or HEVC. Entries your addon marks as cached or direct
  start in seconds; uncached ones are slow.
- Avoid `4k … DV` / `Dolby Vision` REMUX: on the onn the video is black and only
  audio plays.
- `name` holds the addon's quality badge, `title` the release name.

## If the API is unreachable

Launch the app first — the server starts with the process, the agent port. If it still
fails, fall back to the D-pad playbook for the same app family
(`host/playbooks/nuvio.md`): LEFT for the sidebar, Home → search, then the
title page's source list. Do not blind-key; read `dshtv.py ui` first.

## Limits

- Playback controls are not exposed yet: no pause/seek via the API. Use the
  remote keys (`playpause`, `rewind`, `fastforward`) if asked.
- Addon and Live TV playlist management are exposed
  (`/v1/addons`, `/v1/livetv/playlists`), not catalogs of the whole library.
