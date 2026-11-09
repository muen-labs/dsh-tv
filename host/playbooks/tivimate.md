# TiviMate — playbook

Package `ar.tvplayer.tv` · component `ar.tvplayer.tv/.ui.MainActivity`
Role: live TV / IPTV with M3U playlists, EPG, favourites, recording.

## Navigation map
- Live TV screen: channel list in the middle, preview at top-right.
- **LEFT** opens the group/playlist panel (All playlists, then groups like
  `japan`, `korea`, Favorites, All channels, …); **LEFT again** walks further
  into the menu rail.
- **BACK** from a channel exits playback/menu; **MENU** may be ignored.
- **Settings** is a gear in the main menu rail (leftmost). If it is not visible,
  press LEFT until the rail appears, then UP/DOWN to the gear.
- Use `python3 host/dshtv.py ui` to read the current panel before acting —
  TiviMate changes focus state a lot between player/list/menu.

## Add an M3U playlist (canonical flow)
1. Settings (gear) → **Playlists** → **Add playlist**.
2. Choose **M3U playlist**.
3. Enter a **name** (e.g. `japan`) and the playlist **URL** (http/https, ends in
   `.m3u` or `.m3u8`; Xtream servers may need the `get.php?...` URL).
4. Next → optionally provide an **EPG (XMLTV) URL** → Done.
5. Wait for the import (large lists take a while). Channels appear under the
   playlist name in the LEFT group panel.
> Xtream Codes alternative: Add playlist → **Xtream Codes API** → server URL +
> username + password (no M3U URL needed; EPG usually comes with it).

## EPG
Settings → **EPG** → add XMLTV URL (or per-playlist URL at add time) → assign
to the playlist → refresh. If guide is empty, check URL + timezone.

## Favorites / search / playback
- Favorites: focus a channel → **OK (long-press)** → Add to favorites, or open
  channel info with **INFO** and toggle favourite. Favorites group is pinned in
  the LEFT panel.
- Search: main menu → **Search** → type → OK.
- Playback: OK plays; OK again opens the channel list; BACK exits; INFO toggles
  channel info; MENU/OK options for audio/subtitles where available.
- Recording needs a writable storage location (SMB/USB) in Settings → Recording.

## Notes for the assistant
- Users often add playlists from a provider URL — never invent or modify URLs;
  ask for the playlist URL (or read it from `.auth/tivimate-sources.json`).
- Large playlists can freeze focus for seconds; wait and re-`ui`.
- `text` into TiviMate fields works, but long URLs are easier pasted with the
  on-screen keyboard/remote app. Confirm the field is focused first via `ui`.
