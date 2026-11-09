# OwnTV — playbook

Package `tv.own.owntv` · component `tv.own.owntv/.MainActivityCobalt`
Role: Cobalt-based web IPTV front-end (provider login, live channels).

## Navigation
- Cobalt web app: D-pad moves focus on the page; OK activates; BACK goes back in
  the web history.
- Use `ui` to read page text/fields; `text` for login/URL fields.
- Long-press/INFO may open a browser-style menu.

## Notes
- Playlists/EPG are managed by the provider, not addable as M3U here.
- If the page is blank, wait (Cobalt boot) and `ui` again; BACK then relaunch.
- For M3U playlists use TiviMate instead.
