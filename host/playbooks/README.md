# TV app playbooks

Operational knowledge for the apps installed on the onn. 4K Pro. The assistant
must read the relevant playbook **before** driving an app it has not used in
this turn, and must verify layout with `python3 host/dshtv.py ui` instead of
assuming a fixed key count.

| App | Package | Playbook |
| --- | --- | --- |
| Stremio | com.stremio.one | stremio.md |
| TiviMate | ar.tvplayer.tv | tivimate.md |
| Nuvio | com.nuvio.tv | nuvio.md |
| CloudStream | com.lagradost.cloudstream3 | cloudstream.md |
| OwnTV | tv.own.owntv | owntv.md |
| JapanTV | app.japantv | japantv.md |
| Downloader | com.esaba.downloader | downloader.md |
| Projectivy | com.spocky.projengmenu | projectivy.md |
| YouTube | com.google.android.youtube.tv | youtube.md |
| Netflix | com.netflix.ninja | netflix.md |
| Prime Video | com.amazon.amazonvideo.livingroom | prime.md |

Machine-readable index + launch components + search recipes: `host/tv-apps.json`.

## Rules
- Launch → wait → `ui` → navigate → `ui` → act; never blind-key long sequences.
- Never invent playlist/addon URLs. Ask the user (or read
  `.auth/tivimate-sources.json`) before entering credentials/URLs.
- Long URLs: prefer the app's community catalog or a QR/web flow; if typing is
  unavoidable, confirm the field is focused with `ui` first.
- DRM apps (Netflix/Prime) black out screenshots; verify with `ui`/`state`.
- If an app is not in this index, use the generic loop: launch → ui → find
  Search/Settings by label → D-pad + OK.
