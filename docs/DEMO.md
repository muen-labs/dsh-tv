# Demo: “I’m in the mood for a K-drama”

Target narrative:

1. User: “I’m in the mood for K-drama.”
2. Assistant researches r/kdrama, MyDramaList, 2026 rankings → answers with **top 3**
   → recommends one with a reason and notes the user's installed Stremio addons
   → asks **“Want to watch it here?”**
3. User: “Yes.”
4. Assistant opens Stremio, looks in the **catalog rows first**, then searches the
   title, opens it, picks the best stream from the user’s addons and plays it.

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
`192.168.1.51`, different subnet, so it needs its own target — point
`DSHTV_CONFIG` at a config for it; the reveal intent follows the same config:

```bash
cat > /tmp/plus-tv.json <<'JSON'
{"host":"192.168.1.51","port":8765,"token":"","serial":"192.168.1.51:5555"}
JSON
DSHTV_CONFIG=/tmp/plus-tv.json python3 host/demo_kdrama.py --recommend --reveal
```

`DSHTV_ADB` / `DSHTV_ADB_SERIAL` override the adb binary and serial if the TV is
not discoverable from the config. The TV has to be paired with the Mac (Settings
→ Whale-chan TV in DSH, or the phone approval page) and its bridge running
(green **Start service** on Bridge home) before key injection works.

Latest run on the 4K Plus: recommendation + “FOR YOU” overlay worked; the `--play` leg still stops
at the known search/catalog matcher gap (below) — recording:
`docs/media/plus-demo.mp4`.

## Current status

| Leg | Status |
| --- | --- |
| Research top 3 + reason | ✅ working (`host/demo_kdrama.py`) |
| Recommendation overlay (“FOR YOU”, addons, watch question) | ✅ working |
| Catalog-first scan of Stremio Home/Discover | ✅ rows visible via `ui`; matcher being hardened |
| Search fallback | ⚠️ addon rows can show “Search unavailable”; the search picker depends on addon health. On the 4K Plus run, “The Remarried Empress” was not matched and Stremio ended up on another title’s stream list |
| Open title + list streams | ✅ the installed addons’ sources appear (verified on the 4K Plus) |
| Playback | ❌ first sources exit the player with “Ow! That stings!” — likely VPN/P2P/debrid or codec; needs stream-health selection |

The next milestone is the playback leg: filter stream cards by addon + seeders,
skip failing sources, verify playback with `state`/`ui`, then record the demo.

## Recording a public demo

The earlier published demo was withdrawn: it showed third-party stream addons and a commercial
episode. Record new demos against content you are allowed to show, such as a free channel
from the public [iptv-org](https://github.com/iptv-org/iptv) lists or a public-domain film,
on a plain launcher wallpaper and with an empty watch history.

Capture notes: on these boxes hardware-decoded HEVC does not appear in
`screencap`/`screenrecord` (black video), so pick an H.264 stream, and `screenrecord`
stops when a video player takes the display, so the UI and the playback may need
separate takes.
