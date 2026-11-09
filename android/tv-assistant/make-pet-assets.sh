#!/bin/bash
# Rebuild res/raw/whale_*.webp (transparent animated WebP) from the WebM
# animations of 1tryout/dsh-whale-pixel-pet (MIT).
#
# The native ffmpeg vp9 decoder throws away the alpha plane; libvpx-vp9 keeps
# it, which is the whole trick. Pillow then assembles the PNG sequence into one
# animated WebP with alpha, which Android plays via AnimatedImageDrawable.
set -euo pipefail
APP="$(cd "$(dirname "$0")" && pwd)"
WORK="${1:-/tmp/pixel-pet-src}"
PY="${PYTHON:-python3}"
RAW="https://raw.githubusercontent.com/1tryout/dsh-whale-pixel-pet/main/dsh-pet/assets/webm"

NAMES=(idle wave think busy wilt celebrate)
FILES=("待机呼吸休闲" "点击回应-元气挥手" "工作状态-思考冒泡" "工作状态-忙碌点按" "工作状态-垂头叹气冒汗" "工作状态-雀跃庆祝")
SECS=(8 5 6 6 5 6)

mkdir -p "$WORK"/src "$WORK"/frames "$WORK"/out
for i in "${!NAMES[@]}"; do
  n=${NAMES[$i]}; src=${FILES[$i]}; t=${SECS[$i]}
  [ -f "$WORK/src/$n.webm" ] || curl -sL --max-time 120 "$RAW/$src.webm" -o "$WORK/src/$n.webm"
  mkdir -p "$WORK/frames/$n"
  ffmpeg -hide_banner -y -loglevel error -c:v libvpx-vp9 -t "$t" -i "$WORK/src/$n.webm" \
    -vf "crop=360:360:140:0,scale=440:440:flags=lanczos,fps=12" -pix_fmt rgba \
    "$WORK/frames/$n/%04d.png"
done

"$PY" - "$WORK" <<'PYEOF'
import glob, os, sys
from PIL import Image
work = sys.argv[1]
for name in ("idle", "wave", "think", "busy", "wilt", "celebrate"):
    frames = [Image.open(p).convert("RGBA") for p in sorted(glob.glob(f"{work}/frames/{name}/*.png"))]
    out = f"{work}/out/whale_{name}.webp"
    frames[0].save(out, save_all=True, append_images=frames[1:],
                   duration=int(1000 / 12), loop=0, quality=58, method=4)
    print(f"{name:10} {len(frames):3}f {os.path.getsize(out)/1024:6.0f}KB")
PYEOF

cp "$WORK"/out/whale_*.webp "$APP/res/raw/"
echo "installed into $APP/res/raw:"
ls -lh "$APP"/res/raw/whale_*.webp
