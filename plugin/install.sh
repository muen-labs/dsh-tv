#!/bin/bash
# Install the Whale-chan MCP tools into a DSH profile patch.
#   ./plugin/install.sh [profile]      (default: desktop)
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
PROFILE="${1:-desktop}"
PATCH="$HOME/.dsh/profiles/$PROFILE/cordis.patch.yml"
[ -f "$PATCH" ] || { echo "no profile patch at $PATCH" >&2; exit 1; }
if grep -q "mcp-whale-chan" "$PATCH"; then
  echo "mcp-whale-chan already installed in $PATCH"; exit 0
fi
cp "$PATCH" "$PATCH.bak-whale-$(date +%Y%m%dT%H%M%S)"
cat >> "$PATCH" <<YML

# Whale-chan TV assistant (installed $(date +%Y-%m-%d))
- insert:
    - id: mcp-whale-chan
      name: "@deepseek-ai/dsh-mcp-client"
      config:
        serverName: whale
        transport: stdio
        command: python3
        args:
          - $REPO/plugin/mcp/whale_voice_mcp.py
        env:
          WHALE_REPO: $REPO
        toolCallTimeoutMs: 300000
        failOnStartupError: false
YML
echo "installed into $PATCH (backup alongside). Restart DSH to load the whale_* tools."
