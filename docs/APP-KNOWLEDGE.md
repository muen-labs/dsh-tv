# TV app knowledge (how DSH drives the box)

The box has ~30 launchable apps with very different navigation. Fixed key
sequences are brittle, so DSH gets two layers of knowledge plus a way to see the
screen.

## 1. Machine-readable catalog

`host/tv-apps.json`

```json
{"device": {...}, "navigation": {...},
 "apps": [{"package": "...", "label": "...", "component": "...", "category": "...",
           "search": {"verified": true, "steps": ["launch stremio", "key left", ...]},
           "playbook": "host/playbooks/stremio.md", "notes": "..."}]}
```

Generated from the device with `pm list packages` + `cmd package
resolve-activity --brief -c android.intent.category.LEANBACK_LAUNCHER <pkg>`.

## 2. Operational playbooks

`host/playbooks/` — one markdown per app (index in `README.md`): navigation map,
verified flows, M3U/addon/EPG procedures, troubleshooting. The daemon prompt tells
DSH to read the relevant playbook before driving an app it has not used this turn.

Covered: Stremio (addons, search), TiviMate (M3U + EPG + Xtream + favourites),
Nuvio (addons/collections), CloudStream (repos/providers), OwnTV, JapanTV,
Downloader, Projectivy, YouTube, Netflix, Prime Video.

## 3. Eyes: `ui`

```bash
python3 host/dshtv.py ui
# {"ok": true, "nodes": [{"text": "Search", "focused": true, "bounds": "[..]"}],
#  "focused": {...}}
```

`uiautomator dump` gives text, focus and bounds. The rule is
**launch → wait → ui → navigate → ui → act**, never blind-key long sequences.
Screenshots are still useful, but DRM playback (Netflix/Prime) captures black;
`ui`/`state` are the fallback.

## Driving rules

- Read the playbook, then `ui`; app layouts differ by build/version.
- Launch by label (`launch stremio`) or exact package/component.
- Verify fields are focused before typing; long URLs are error-prone on TV
  keyboards — prefer community catalogs, QR/web flows, or ask the user.
- Never invent playlist/addon/EPG URLs or credentials; read
  `.auth/tivimate-sources.json` only when the user asks, and never commit it.
- Record habits/actions in `host/tv_memory.py` so repeated flows get faster.
- If an app is unknown: launch → `ui` → find Search/Settings by label → D-pad +
  OK, then write a new playbook.

## Adding an app

1. `pm list packages -3`; resolve the LEANBACK launcher component.
2. Explore with `launch`, `ui`, keys; capture screenshots for the flow.
3. Add the catalog entry (package/label/component/category + optional search
   recipe) and a `host/playbooks/<app>.md`.
4. Verify once end-to-end; mark `search.verified` only after it works.

## Example plans

- *"Add a K-drama M3U"* → read `tivimate.md`; Settings → Playlists → Add
  playlist → M3U; ask for name/URL/EPG first; verify import via `ui`.
- *"Install the AniAddon"* → read `stremio.md`; Addons → + Add addon (or
  Community Addons); configure on Mac if needed; verify Installed.
- *"Search anime in Stremio"* → verified recipe: launch, LEFT, UP, OK, type,
  ENTER, `ui` results.
