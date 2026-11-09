#!/bin/bash
# Build the single TV APK: DSH TV Bridge + Whale-chan assistant.
# Needs JDK 8+ and an Android SDK (build-tools + platform API 33).
set -euo pipefail
APP="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$APP/../.." && pwd)"
SDK="${ANDROID_SDK_ROOT:-${REPO}/../.tools/android-sdk}"
export JAVA_HOME="${JAVA_HOME:-${REPO}/../.tools/jdk/Contents/Home}"
export PATH="$JAVA_HOME/bin:$PATH"
BT="$(ls -d "$SDK"/build-tools/* | head -1)"
PLAT="$(ls -d "$SDK"/platforms/* | head -1)"
AJ="$PLAT/android.jar"
cd "$APP"

HOST="${WHALE_HOST:-192.168.4.57}"
PORT="${WHALE_PORT:-8766}"
TOKEN="${WHALE_TOKEN:-}"
if [ -z "$TOKEN" ] && [ -f "$REPO/.auth/whale.token" ]; then TOKEN="$(cat "$REPO/.auth/whale.token")"; fi
[ -n "$TOKEN" ] || TOKEN="pair-me"   # real token arrives via QR pairing
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
if [ ! -f debug.keystore ]; then
  keytool -genkeypair -keystore debug.keystore -storepass android \
    -alias androiddebugkey -keypass android -keyalg RSA -keysize 2048 \
    -validity 10000 -dname "CN=Android Debug,O=Android,C=US" >/dev/null 2>&1
fi
"$BT/apksigner" sign --ks debug.keystore --ks-pass pass:android --key-pass pass:android --out TVAssistant.apk aligned.apk
ls -lh TVAssistant.apk
