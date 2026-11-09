#!/bin/bash
set -euo pipefail
APP="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$APP/../.." && pwd)"
if [ -z "${JAVA_HOME:-}" ] && [ -d "${REPO}/../.tools/jdk/Contents/Home" ]; then
  JAVA_HOME="${REPO}/../.tools/jdk/Contents/Home"
fi
if [ -z "${JAVA_HOME:-}" ]; then
  JAVA_HOME="$(/usr/libexec/java_home 2>/dev/null || true)"
fi
export JAVA_HOME
export PATH="$JAVA_HOME/bin:/usr/bin:/bin:/usr/sbin:/sbin"
SDK="${ANDROID_SDK_ROOT:-${REPO}/../.tools/android-sdk}"
BT="$(ls -d "$SDK"/build-tools/* | head -1)"
PLAT="$(ls -d "$SDK"/platforms/* | head -1)"
AJ="$PLAT/android.jar"
cd "$APP"
rm -rf gen obj dex compiled unsigned.apk aligned.apk DisneyShim.apk
mkdir -p gen obj dex compiled
"$BT/aapt2" compile --dir res -o compiled
"$BT/aapt2" link -o unsigned.apk --manifest AndroidManifest.xml -I "$AJ" --java gen compiled/*.flat
find src gen -name '*.java' > sources.txt
javac --release 8 -Xlint:-options -classpath "$AJ" -d obj @sources.txt
find obj -name '*.class' > classes.txt
"$BT/d8" --lib "$AJ" --min-api 26 --output dex $(cat classes.txt)
(cd dex && zip -q ../unsigned.apk classes.dex)
"$BT/zipalign" -f 4 unsigned.apk aligned.apk
if [ ! -f debug.keystore ] && [ -f "$REPO/android/tv-assistant/debug.keystore" ]; then
  cp "$REPO/android/tv-assistant/debug.keystore" .
fi
if [ ! -f debug.keystore ]; then
  keytool -genkeypair -keystore debug.keystore -storepass android -alias androiddebugkey \
    -keypass android -keyalg RSA -keysize 2048 -validity 10000 \
    -dname "CN=Android Debug,O=Android,C=US" >/dev/null 2>&1
fi
"$BT/apksigner" sign --ks debug.keystore --ks-pass pass:android --key-pass pass:android --out DisneyShim.apk aligned.apk
ls -lh DisneyShim.apk
