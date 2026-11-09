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

## Current status

| Leg | Status |
| --- | --- |
| Research top 3 + reason | ✅ working (`host/demo_kdrama.py`) |
| Recommendation overlay (“FOR YOU”, addons, watch question) | ✅ working |
| Catalog-first scan of Stremio Home/Discover | ✅ rows visible via `ui`; matcher being hardened |
| Search fallback | ⚠️ addon rows can show “Search unavailable”; the search picker depends on addon health |
| Open title + list streams | ✅ Torrentio 1080p sources appear |
| Playback | ❌ first sources exit the player with “Ow! That stings!” — likely VPN/P2P/debrid or codec; needs stream-health selection |

The next milestone is the playback leg: filter stream cards by addon + seeders,
skip failing sources, verify playback with `state`/`ui`, then record the demo.
