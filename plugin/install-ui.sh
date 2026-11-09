#!/bin/bash
# Install the Whale-chan TV settings pane (the client/host half) into a DSH
# profile.
#
#   ./plugin/install-ui.sh [profile] [--copy] [--dry-run]
#
#   profile    profile name under $DSH_HOME/profiles (default: desktop)
#   --copy     copy plugin/ui instead of symlinking it (a symlink means a later
#              `node build.mjs` is picked up on the next restart, no reinstall).
#              The copy also gets repo-path.txt, the marker the host half reads
#              to find .auth/whale.token and host/config.json.
#   --dry-run  print what would change, write nothing
#
# What it does:
#   1. links/copies plugin/ui to <profile>/node_modules/dsh-whale-chan-tv
#   2. appends the `- insert:` loader row to <profile>/cordis.patch.yml once
#      (backup alongside; safe to re-run)
#   3. prints the restart and verification steps
#
# It never writes outside the selected profile and never starts or restarts DSH.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
PKG_SRC="$REPO/plugin/ui"
DSH_HOME_DIR="${DSH_HOME:-$HOME/.dsh}"

PROFILE="desktop"
MODE="link"
DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --copy) MODE="copy" ;;
    --dry-run) DRY_RUN=1 ;;
    -h|--help)
      sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    -*)
      echo "unknown option: $arg" >&2
      exit 2
      ;;
    *) PROFILE="$arg" ;;
  esac
done

case "$PROFILE" in
  ""|.*|*/*|*\\*|node_modules)
    echo "invalid profile name: $PROFILE" >&2
    exit 2
    ;;
esac

PROFILE_DIR="$DSH_HOME_DIR/profiles/$PROFILE"
PATCH="$PROFILE_DIR/cordis.patch.yml"
MODULES="$PROFILE_DIR/node_modules"
DEST="$MODULES/dsh-whale-chan-tv"

run() {
  if [ "$DRY_RUN" -eq 1 ]; then
    echo "would: $*"
  else
    "$@"
  fi
}

[ -f "$PATCH" ] || {
  echo "no profile patch at $PATCH" >&2
  echo "create the profile first (dsh --profile $PROFILE), or pass the right profile name." >&2
  exit 1
}

[ -f "$PKG_SRC/lib/client.js" ] || {
  echo "the client bundle is missing: $PKG_SRC/lib/client.js" >&2
  echo "build it first:  cd $PKG_SRC && npm install && node build.mjs" >&2
  exit 1
}

if [ "$MODE" = "copy" ] && [ ! -f "$PKG_SRC/lib/index.js" ]; then
  echo "the host half is missing: $PKG_SRC/lib/index.js" >&2
  exit 1
fi

echo "profile: $PROFILE_DIR"
echo "source:  $PKG_SRC"

# Copy the package and leave the repo-path marker the host half reads: a copy
# under <profile>/node_modules cannot derive the repo from its own location.
copy_package() {
  local dest="$1"
  if [ "$DRY_RUN" -eq 0 ]; then
    mkdir -p "$dest"
    ( cd "$PKG_SRC" && tar -cf - lib package.json cordis.patch.yml README.md docs 2>/dev/null ) | ( cd "$dest" && tar -xf - )
    printf '%s\n' "$REPO" > "$dest/repo-path.txt"
    echo "package: repo marker -> $dest/repo-path.txt"
  else
    echo "would: write repo marker -> $dest/repo-path.txt"
  fi
}

# 1. Make the package resolvable from the profile's BaseUrl.
if [ "$DRY_RUN" -eq 0 ]; then
  mkdir -p "$MODULES"
fi
if [ -L "$DEST" ]; then
  CURRENT_LINK="$(readlink "$DEST")"
  if [ "$MODE" = "copy" ]; then
    echo "package: replacing link with a copy at $DEST"
    run rm "$DEST"
    copy_package "$DEST"
  elif [ "$CURRENT_LINK" = "$PKG_SRC" ]; then
    echo "package: already linked at $DEST"
  else
    echo "package: replacing stale link ($CURRENT_LINK)"
    run rm "$DEST"
    run ln -s "$PKG_SRC" "$DEST"
  fi
elif [ -e "$DEST" ]; then
  if [ -f "$DEST/package.json" ] && grep -q '"name": *"dsh-whale-chan-tv"' "$DEST/package.json"; then
    if [ "$MODE" = "copy" ]; then
      echo "package: refreshing copied install at $DEST"
      if [ "$DRY_RUN" -eq 0 ]; then
        rm -rf "$DEST"
      fi
      copy_package "$DEST"
    else
      echo "package: replacing copied install with a symlink"
      run rm -rf "$DEST"
      run ln -s "$PKG_SRC" "$DEST"
    fi
  else
    echo "$DEST exists but is not dsh-whale-chan-tv; refusing to touch it" >&2
    exit 1
  fi
else
  if [ "$MODE" = "copy" ]; then
    echo "package: copying to $DEST"
    copy_package "$DEST"
  else
    echo "package: linking $DEST -> $PKG_SRC"
    run ln -s "$PKG_SRC" "$DEST"
  fi
fi

# 2. Add the loader row once (idempotent).
if grep -q 'dsh-whale-chan-tv' "$PATCH"; then
  echo "patch:   dsh-whale-chan-tv already present in $PATCH"
else
  STAMP="$(date +%Y%m%dT%H%M%S)"
  echo "patch:   appending the insert row (backup: $(basename "$PATCH").bak-whale-ui-$STAMP)"
  if [ "$DRY_RUN" -eq 0 ]; then
    cp "$PATCH" "$PATCH.bak-whale-ui-$STAMP"
    # A default patch layer is the literal `[]`; a list item cannot follow it.
    if grep -qx '\[\]' "$PATCH"; then
      grep -v -x '\[\]' "$PATCH" > "$PATCH.tmp-whale-ui"
      mv "$PATCH.tmp-whale-ui" "$PATCH"
    fi
    cat >> "$PATCH" <<YML

# Whale-chan TV settings pane (installed $(date +%Y-%m-%d) by plugin/install-ui.sh)
- insert:
    - id: dsh-whale-chan-tv
      name: dsh-whale-chan-tv
YML
  fi
fi

cat <<EOF

Done. Next:
  1. Restart DSH so the profile reloads its patch layer:
       - desktop app: quit DeepSeek Harness and reopen it
       - web profile: stop the 'dsh --profile $PROFILE' host and start it again
  2. Open Settings -> "Whale-chan TV".
  3. Make sure the voice daemon is running (the pane's Connection card says):
       python3 $REPO/host/whale_voice.py --serve --port 8766
  4. Verify the host routes answer from the running host (same origin as the GUI):
       curl -s "<gui-url>/whale-chan/status" | head -c 400

Re-running this script is safe: it keeps one link/copy and one patch row.
EOF
