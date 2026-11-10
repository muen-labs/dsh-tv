#!/usr/bin/env bash
# Enable the DSH TV bridge accessibility service on a TV box WITHOUT clobbering
# the other enabled services (Projectivy, tvQuickActions, ...).
#
# Why: Android stores the enabled services as ONE ':'-separated setting:
#     settings get secure enabled_accessibility_services
#     com.spocky.projengmenu/....ProjectivyAccessibilityService:dev.vodik7.tvquickactions/....KeyAccessibilityService
# `settings put secure enabled_accessibility_services <one-component>` REPLACES
# that list, so a hard-coded put silently disables the user's Projectivy /
# tvQuickActions services. This helper READS the list, appends our component if
# it is missing, and writes the merged list back.
#
# Usage:
#   host/tv-accessibility.sh [<serial-or-ip>] [--prune]
#
#   <serial-or-ip>  adb serial, e.g. 192.168.4.58:5555 (optional if exactly one
#                   device is connected)
#   --prune         also drop entries whose package is no longer installed
#                   (only such stale entries are ever removed)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [ -z "${ADB:-}" ]; then
  if [ -x "$ROOT/.tools/platform-tools/adb" ]; then
    ADB="$ROOT/.tools/platform-tools/adb"
  elif [ -x "$ROOT/../.tools/platform-tools/adb" ]; then
    ADB="$ROOT/../.tools/platform-tools/adb"
  else
    ADB="$ROOT/.tools/platform-tools/adb"   # report a useful path below
  fi
fi
COMPONENT="com.jp.dshtv/com.jp.dshtv.KeyService"
SERIAL=""
PRUNE=0

for arg in "$@"; do
  case "$arg" in
    --prune) PRUNE=1 ;;
    -h|--help)
      sed -n '2,24p' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    -*)
      echo "unknown option: $arg (try --help)" >&2
      exit 2 ;;
    *)
      SERIAL="$arg" ;;
  esac
done

if [ ! -x "$ADB" ]; then
  echo "adb not found at $ADB (set ADB=/path/to/adb to override)" >&2
  exit 1
fi

ADB_ARGS=()
[ -n "$SERIAL" ] && ADB_ARGS=(-s "$SERIAL")

if ! "$ADB" "${ADB_ARGS[@]}" get-state >/dev/null 2>&1; then
  echo "no adb device${SERIAL:+ $SERIAL} — connect first: adb connect <tv-ip>:5555" >&2
  exit 1
fi

shell() { "$ADB" "${ADB_ARGS[@]}" shell "$@"; }

# --- read the current list (null == nothing enabled) -------------------------
BEFORE="$(shell settings get secure enabled_accessibility_services | tr -d '\r')"
[ "$BEFORE" = "null" ] && BEFORE=""
echo "before: ${BEFORE:-<empty>}"

LIST="$BEFORE"
if [ "$PRUNE" -eq 1 ] && [ -n "$LIST" ]; then
  INSTALLED="$(shell pm list packages | tr -d '\r' | sed 's/^package://')"
  PRUNED=""
  IFS=':' read -ra ENTRIES <<< "$LIST"
  for entry in "${ENTRIES[@]}"; do
    [ -z "$entry" ] && continue
    pkg="${entry%%/*}"
    if grep -qxF "$pkg" <<< "$INSTALLED"; then
      PRUNED="${PRUNED:+$PRUNED:}$entry"
    else
      echo "prune: package '$pkg' is not installed — dropping '$entry'"
    fi
  done
  LIST="$PRUNED"
fi

# --- append our service if it is missing (never remove/replace others) -------
case ":$LIST:" in
  *":$COMPONENT:"*) ;;
  *) LIST="${LIST:+$LIST:}$COMPONENT" ;;
esac

# --- write back only when the merged list changed ----------------------------
if [ "$LIST" != "$BEFORE" ]; then
  shell settings put secure enabled_accessibility_services "$LIST"
fi
shell settings put secure accessibility_enabled 1

AFTER="$(shell settings get secure enabled_accessibility_services | tr -d '\r')"
[ "$AFTER" = "null" ] && AFTER=""
echo "after:  ${AFTER:-<empty>}"

case ":$AFTER:" in
  *":$COMPONENT:"*) echo "ok: $COMPONENT is enabled; other services preserved" ;;
  *) echo "WARNING: $COMPONENT is still missing from the list" >&2; exit 1 ;;
esac
