# Stremio — playbook

Package `com.stremio.one` · component `com.stremio.one/com.stremio.tv.MainActivity`
Role: main movie/series player (Cinemeta, Torrentio, Ratings Aggregator installed).

## Navigation map
Left sidebar (top → bottom): **Search, Home, Discover, Library, Calendar, Addons, Settings**.
- From the home screen press **LEFT** to open the sidebar (focus lands on Home).
- **UP/DOWN** move through the sidebar; **OK** opens the page; **BACK** closes it.
- Content rows are reached with RIGHT; cards with OK; BACK returns.

## Search (verified)
```
launch stremio
key left          # sidebar, focus Home
key up            # Search
key ok            # opens search + keyboard
text "k-drama"
key enter         # results: Series Search / AI Search
```
Then use **ui** to read result titles; **RIGHT/OK** to open a title, **DOWN**
into the stream list, OK to play. Addons can take a few seconds to deliver
streams — wait, then `ui` again.

## Addons
Open **Addons** in the sidebar. The screen has:
- **+ Add addon** — install from a manifest URL.
- **Community Addons** — browse/search the community catalog; OK installs.
- **Installed / All** tabs; each card shows version + Installed check.

Install from URL (best for pre-configured addons, e.g. Torrentio with Debrid):
1. On the Mac, open the addon's configure page and copy the **install/manifest URL**
   (Torrentio: `https://torrentio.strem.fun/configure` → configure → copy link).
2. On TV: Addons → **+ Add addon** → paste/type the URL → confirm.
3. Wait for "Installed"; BACK to Discover and refresh the title.
Long URLs are painful with the on-screen keyboard — prefer Community Addons
when possible, or use the web configure flow and a `stremio://` deep link.

Remove/disable: Addons → focus the addon card → OK/MENU → Uninstall.

## Library / continue watching
- On a title, OK → **Add to library**; Library sidebar shows it.
- Home rows: Continue Watching, Featured, etc. Resume is automatic.
- Ratings Aggregator adds IMDb/TMDb/Metacritic scores to detail pages.

## Troubleshooting
- Streams empty → addon still loading ("… addon is still loading") → wait, BACK, reopen.
- Addon installed but not in Discover → force-stop Stremio, relaunch.
- Buffering/language → open the stream card; pick a different source/debrid line.
