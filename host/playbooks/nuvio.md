# Nuvio — playbook

Package `com.nuvio.tv` · component `com.nuvio.tv/.launcher.AppIconDefault`
Role: Stremio-style streaming app (catalog + addons/collections).

## Navigation
- Launch; LEFT opens the sidebar/nav rail (Home, Discover, Library, Search,
  Addons/Collections, Settings — exact order differs by build).
- Use `ui` to read the rail labels; DOWN/UP + OK to open.
- Content rows: RIGHT to move, OK to open, BACK to return.

## Search
```
launch nuvio
ui                       # confirm rail + labels
key left
key up / key down        # until "Search" is focused
key ok
text "k-drama"
key enter
```
Then `ui` results, OK to open, DOWN to sources, OK to play.

## Addons / collections
- Sidebar → **Addons** (or Settings → Addons): add by **manifest URL** or pick
  from a built-in community list; each addon provides catalogs/streams.
- After adding, refresh Discover; catalog rows appear as new collections.
- Remove addons from the same screen; restart if a new addon does not appear.

## Notes
- Nuvio is not an M3U/IPTV player; for live TV use TiviMate/OwnTV.
- Sources may come from addons (torrent/debrid); pick source on the title page.
- Long addon URLs: prefer the community list or install from the app's web flow.
