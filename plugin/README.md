# DSH plugin: DeepSeek TV

Two halves, installed separately:

| Half | What it adds | Install |
| --- | --- | --- |
| MCP tools (`plugin/`) | `whale_health`, `whale_ask`, `whale_discover`, `whale_start` as `mcp__whale__*` | `./plugin/install.sh desktop` |
| Settings pane (`plugin/ui/`) | a **DeepSeek TV** Settings section: daemon/TV-bridge state, LAN TV discovery, and approving TV pairing requests from inside DSH | `./plugin/install-ui.sh desktop` |

Both scripts back up the profile patch and are safe to re-run. Restart DSH after
installing either half.

## MCP tools

| Tool | Use |
| --- | --- |
| `whale_health` | is the host daemon running, and where |
| `whale_ask` | send text to the same persistent voice session the TV uses |
| `whale_discover` | scan the LAN for Android TVs running the bridge |
| `whale_start` | start the daemon if it is not listening |

`cordis.patch.yml` in this folder is the template `install.sh` resolves.

## Settings pane

`plugin/ui` is a dual-face DSH package: `lib/index.js` is the host half (seven
same-origin `/whale-chan/*` JSON routes registered on the `webServer` service)
and `lib/client.js` is the browser module-loader bundle that draws the Settings
section in the host's own `--dsw-*` tokens (light and dark).

```bash
cd plugin/ui && npm install && node build.mjs   # build the client bundle
./plugin/install-ui.sh desktop                  # link + patch row (idempotent)
./plugin/install-ui.sh desktop --copy           # frozen copy + repo-path.txt marker
```

Restart DSH, then **Settings → DeepSeek TV**. The daemon
(`python3 host/whale_voice.py --serve --port 8766`) must be running for the pane
to be useful; it says so and prints the command when it is not.

A link install finds `.auth/whale.token` / `host/config.json` through the
symlink; a `--copy` install has no path back to the repo, so the installer writes
`repo-path.txt` inside the copy and the host half reads it (env `WHALE_REPO` wins,
then the marker, then the derived path; `GET /whale-chan/status` reports
`repo.found` when none resolve, instead of silently losing the token).

See [plugin/ui/README.md](ui/README.md) for routes, screenshots, the phases and
the full verification notes.
