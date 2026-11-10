# Demo: “I’m in the mood for a K-drama”

Target narrative:

1. User: “I’m in the mood for K-drama.”
2. Assistant researches r/kdrama, MyDramaList, 2026 rankings → answers with **top 3**
   → recommends one with a reason and notes the available Stremio addons
   (Torrentio/yastream) → asks **“Want to watch it here?”**
3. User: “Yes.”
4. Assistant opens Stremio, looks in the **catalog rows first**, then searches the
   title, opens it, picks the best Torrentio/yastream stream and plays it.

## How to run

```bash
python3 host/demo_kdrama.py --recommend --reveal   # research + FOR YOU overlay
python3 host/demo_kdrama.py --play "Doctor X: Age of the White Mafia"      # catalog-first -> search -> streams
```

Screen record the TV while running:

```bash
adb shell screenrecord --size 1280x720 --bit-rate 4000000 --time-limit 180 /sdcard/dsh-demo.mp4
adb pull /sdcard/dsh-demo.mp4 docs/media/dsh-demo.mp4
```

## Running the demo on the other TV (onn. 4K Plus)

The bridge CLI follows `host/config.json` by default (the onn. 4K Pro, “Living
Room TV”). To drive the second box — the **onn. 4K Plus Streaming** on
`192.168.5.205`, different subnet, so it needs its own target — point
`DSHTV_CONFIG` at a config for it; the reveal intent follows the same config:

```bash
cat > /tmp/plus-tv.json <<'JSON'
{"host":"192.168.5.205","port":8765,"token":"","serial":"192.168.5.205:5555"}
JSON
DSHTV_CONFIG=/tmp/plus-tv.json python3 host/demo_kdrama.py --recommend --reveal
```

`DSHTV_ADB` / `DSHTV_ADB_SERIAL` override the adb binary and serial if the TV is
not discoverable from the config. The TV has to be paired with the Mac (Settings
→ Whale-chan TV in DSH, or the phone approval page) and its bridge running
(green **Start service** on Bridge home) before key injection works.

Latest run on the 4K Plus: recommendation + “FOR YOU” overlay worked
([screenshot](screenshots/tv-demo-plus-reveal.png)); the `--play` leg still stops
at the known search/catalog matcher gap (below) — recording:
`docs/media/plus-demo.mp4`.

## Current status

| Leg | Status |
| --- | --- |
| Research top 3 + reason | ✅ working (`host/demo_kdrama.py`) |
| Recommendation overlay (“FOR YOU”, addons, watch question) | ✅ working |
| Catalog-first scan of Stremio Home/Discover | ✅ rows visible via `ui`; matcher being hardened |
| Search fallback | ⚠️ addon rows can show “Search unavailable”; the search picker depends on addon health. On the 4K Plus run, “The Remarried Empress” was not matched and Stremio ended up on another title’s stream list |
| Open title + list streams | ✅ Torrentio/Comet sources appear (verified on the 4K Plus) |
| Playback | ❌ first sources exit the player with “Ow! That stings!” — likely VPN/P2P/debrid or codec; needs stream-health selection |

The next milestone is the playback leg: filter stream cards by addon + seeders,
skip failing sources, verify playback with `state`/`ui`, then record the demo.

## Trending-anime demo (recorded 2026-11)

Ask: *"Suggest an anime that is trending."*

1. **Research** — `host/demo_anime.py --recommend` asks AniList for currently
   airing anime sorted by `TRENDING_DESC` (a legit anime database, same data
   MAL-style sites show). The pick is #5 on that list on the recording day:
   *The Apothecary Diaries Season 3* (score 85, 111,488 followers).
2. **Recommend** — the assistant's FOR YOU card shows the title and the reason
   (rank, score, episode count, genres), then closes.
3. **Drive Stremio** — launch → Search → type the title → open the series → the
   currently-airing season (S03) → episode E01 → wait for addons → pick the
   H.264 Torrentio source → play.
4. **Playback** — the episode plays on the box (the player controls show
   `The Apothecary Diaries – S03E01 – Locusts`, 00:10/24:00).

The published video ([`docs/demo.mp4`](demo.mp4), [`docs/demo.gif`](demo.gif))
is a real capture from the onn. 4K Plus, edited from three takes: this box's
`screenrecord` stops when the video player takes the display, so the overlay,
the Stremio UI and the playback were captured separately and cut together.
Everything else on screen (search, seasons, sources, playback) is the actual
device.

**Capture notes for anyone redoing it:** the first Torrentio source is HEVC —
it plays, but hardware overlay planes do not appear in `screencap`/`screenrecord`
(black video), so pick the H.264 release. The source row also contains a
"support the project" card that opens a donation page in the TV browser; clamp
left before stepping right or you will open it by accident.
