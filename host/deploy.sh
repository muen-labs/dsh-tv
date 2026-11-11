#!/usr/bin/env bash
# deploy.sh — install the bespoke-catalog addon on this Mac and keep it alive.
#
# Two rules this exists to enforce:
#
#  1. The code runs from the INTERNAL disk. launchd cannot read /Volumes/* without
#     Removable Volumes / Full Disk Access — it fails with "Operation not permitted", which
#     is exactly how the old jp-iptv serve agent died silently. So the live copy lives in
#     ~/Library/Application Support, and nothing here needs an external SSD.
#
#  2. The repo is the single source of truth for CODE; the live directory is the single
#     source of truth for DATA. The repo never carries catalogs.json, so there is no second
#     writable copy to drift from the one the server reads.
set -euo pipefail

REPO_HOST="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIVE_DIR="${DSHTV_ADDON_DATA:-$HOME/Library/Application Support/dsh-tv-addon}"
LABEL="com.muen.dshtv-addon"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG="$HOME/Library/Logs/dshtv-addon.log"
PORT="${DSHTV_ADDON_PORT:-8890}"
ENV_FILE="$LIVE_DIR/config.env"
UID_NUM="$(id -u)"

say() { printf '  %s\n' "$*"; }

# ---------------------------------------------------------------- configuration
mkdir -p "$LIVE_DIR" "$HOME/Library/Logs" "$HOME/Library/LaunchAgents"

# Reuse what is already installed so a redeploy never changes the URL under the player.
if [ -f "$ENV_FILE" ]; then
  # shellcheck disable=SC1090
  . "$ENV_FILE"
fi
TOKEN="${DSHTV_ADDON_TOKEN:-${TOKEN:-}}"
AIO="${DSHTV_AIO_METADATA:-${AIO:-}}"
[ -n "$TOKEN" ] || TOKEN="$(openssl rand -hex 16)"

if [ -z "$AIO" ]; then
  say "no AIOmetadata instance configured."
  say "  set DSHTV_AIO_METADATA='https://aiometadata.elfhosted.com/stremio/<your-uuid>'"
  say "  (the addon falls back to Cinemeta; metadata will be plainer but it still works)"
fi

cat > "$ENV_FILE" <<ENV
TOKEN=$TOKEN
AIO=$AIO
PORT=$PORT
ENV
chmod 600 "$ENV_FILE"

# ------------------------------------------------------------------ code
say "code  → $LIVE_DIR"
for f in addon_server.py catalog_add.py picks_research.py; do
  [ -f "$REPO_HOST/$f" ] || { echo "missing $f in $REPO_HOST" >&2; exit 1; }
  cp "$REPO_HOST/$f" "$LIVE_DIR/$f"
  say "  $f"
done

# ------------------------------------------------------------------ data
if [ ! -f "$LIVE_DIR/catalogs.json" ]; then
  if [ -f "$REPO_HOST/catalogs.example.json" ]; then
    cp "$REPO_HOST/catalogs.example.json" "$LIVE_DIR/catalogs.json"
    say "catalogs.json seeded from the example (empty until the agent builds a row)"
  else
    echo '[]' > "$LIVE_DIR/catalogs.json"
    say "catalogs.json created empty"
  fi
else
  say "catalogs.json kept as-is ($(python3 -c 'import json,sys;print(len(json.load(open(sys.argv[1]))))' "$LIVE_DIR/catalogs.json" 2>/dev/null || echo '?') catalog(s))"
fi
[ -f "$LIVE_DIR/picks.json" ] || echo '{"movie": [], "series": []}' > "$LIVE_DIR/picks.json"

# ------------------------------------------------------------------ agent
say "agent → $PLIST"
cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>$LIVE_DIR/addon_server.py</string>
    <string>--port</string><string>$PORT</string>
    <string>--token</string><string>$TOKEN</string>
    <string>--catalogs</string><string>$LIVE_DIR/catalogs.json</string>
    <string>--picks</string><string>$LIVE_DIR/picks.json</string>
    $( [ -n "$AIO" ] && printf '<string>--aiometadata</string><string>%s</string>' "$AIO" )
  </array>
  <key>WorkingDirectory</key><string>$LIVE_DIR</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$LOG</string>
  <key>StandardErrorPath</key><string>$LOG</string>
</dict>
</plist>
PLIST
plutil -lint "$PLIST" >/dev/null

launchctl bootout "gui/$UID_NUM/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$UID_NUM" "$PLIST"
launchctl kickstart -k "gui/$UID_NUM/$LABEL" >/dev/null 2>&1 || true
sleep 3

# ------------------------------------------------------------------ verify
IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo 127.0.0.1)"
URL="http://$IP:$PORT/$TOKEN/manifest.json"
printf '\n'
if curl -fsS --max-time 10 "$URL" -o /tmp/dshtv-manifest.json 2>/dev/null; then
  say "running — $URL"
  python3 - <<'PY'
import json
d = json.load(open('/tmp/dshtv-manifest.json'))
rows = d.get('catalogs') or []
print(f"  manifest: {d.get('name')} v{d.get('version')} · resources={d.get('resources')}")
print(f"  rows: {[r['name'] for r in rows] or 'none yet — the agent builds them'}")
PY
  printf '\n  install in Stremio: Addons → Add addon → paste that URL\n'
  printf '  add a row:  %s/catalog_add.py --catalog-id my-row --catalog-name "My Row" --items items.json\n' "$LIVE_DIR"
else
  echo "addon did not answer — check $LOG" >&2
  tail -5 "$LOG" >&2 || true
  exit 1
fi
