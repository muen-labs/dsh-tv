#!/bin/bash
# Build the combined APK: DSH TV Bridge + Whale-chan assistant.
set -euo pipefail
APP="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$APP/../.." && pwd)"
if [ -n "${WHALE_TOOLS:-}" ]; then
  TOOLS="$WHALE_TOOLS"
elif [ -d "$ROOT/.tools/android-sdk" ]; then
  TOOLS="$ROOT/.tools"
elif [ -d "$ROOT/../.tools/android-sdk" ]; then
  TOOLS="$ROOT/../.tools"
else
  TOOLS="$ROOT/.tools"
fi
export JAVA_HOME="${JAVA_HOME:-$TOOLS/jdk/Contents/Home}"
export PATH="$JAVA_HOME/bin:/usr/bin:/bin:/usr/sbin:/sbin"
SDK="${ANDROID_SDK_ROOT:-$TOOLS/android-sdk}"
BT="$(ls -d "$SDK"/build-tools/* | head -1)"
PLAT="$(ls -d "$SDK"/platforms/* | head -1)"
AJ="$PLAT/android.jar"
cd "$APP"

HOST="${WHALE_HOST:-192.168.4.57}"
PORT="${WHALE_PORT:-8766}"
TOKEN="${WHALE_TOKEN:-}"
if [ -z "$TOKEN" ] && [ -f "$ROOT/.auth/whale.token" ]; then TOKEN="$(cat "$ROOT/.auth/whale.token")"; fi
[ -n "$TOKEN" ] || { echo "set WHALE_TOKEN or create .auth/whale.token" >&2; exit 1; }
cat > res/values/config.xml <<XML
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="whale_host">$HOST</string>
    <string name="whale_port">$PORT</string>
    <string name="whale_token">$TOKEN</string>
</resources>
XML

rm -rf gen obj dex compiled unsigned.apk aligned.apk TVAssistant.apk
mkdir -p gen obj dex compiled
"$BT/aapt2" compile --dir res -o compiled
"$BT/aapt2" link -o unsigned.apk --manifest AndroidManifest.xml -I "$AJ" --java gen compiled/*.flat
find src gen -name '*.java' > sources.txt
javac --release 8 -Xlint:-options -classpath "$AJ" -d obj @sources.txt
find obj -name '*.class' > classes.txt
"$BT/d8" --lib "$AJ" --min-api 26 --output dex $(cat classes.txt)
(cd dex && zip -q ../unsigned.apk classes.dex)
"$BT/zipalign" -f 4 unsigned.apk aligned.apk
[ -f debug.keystore ] || cp "$TOOLS/dshtv-app/debug.keystore" . 2>/dev/null || true
if [ ! -f debug.keystore ]; then
  keytool -genkeypair -keystore debug.keystore -storepass android \
    -alias androiddebugkey -keypass android -keyalg RSA -keysize 2048 \
    -validity 10000 -dname "CN=Android Debug,O=Android,C=US" >/dev/null 2>&1
fi
"$BT/apksigner" sign --ks debug.keystore --ks-pass pass:android --key-pass pass:android --out TVAssistant.apk aligned.apk
"$BT/apksigner" verify --print-certs TVAssistant.apk | head -2
# keep the CLI's setup path working (CI has no .tools directory)
mkdir -p "$TOOLS/dshtv-app"
cp TVAssistant.apk "$TOOLS/dshtv-app/DSHTVBridge.apk"
ls -lh TVAssistant.apk
