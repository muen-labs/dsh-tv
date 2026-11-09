# DSH plugin: Whale-chan TV tools

Adds three MCP tools to DSH:

| Tool | Use |
| --- | --- |
| `whale_health` | is the host daemon running, and where |
| `whale_ask` | send text to the same persistent voice session the TV uses |
| `whale_start` | start the daemon if it is not listening |

Install (writes an `mcp-whale-chan` row into your profile patch, with a backup):

```bash
./plugin/install.sh desktop
```

Restart DSH. The tools appear as `mcp__whale__*`.

`cordis.patch.yml` in this folder is the template the installer resolves.
