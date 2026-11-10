#!/usr/bin/env python3
"""Build docs/ui-gallery.html as a SELF-CONTAINED page.

Copies of this file can be opened from anywhere (Downloads, another machine,
the DSH file preview) because every screenshot is embedded as a data URI. The
screenshots on disk stay the source of truth; re-run this script after
recapturing one.

    python3 tools/make-ui-gallery.py

Images are downscaled to fit 1600x1600 and re-encoded as JPEG (quality ~85) so
the page stays a few MB instead of ~30 MB. Uses ffmpeg when available, else
macOS `sips`; both are optional at runtime because the generated file embeds
everything.
"""
from __future__ import annotations

import base64
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
OUT = DOCS / "ui-gallery.html"
CACHE = Path("/tmp/dsh-ui-gallery-cache")

# One entry per implemented screen. `f` is relative to docs/.
SCREENS = [
    dict(g="Bridge home", t="Bridge home — RUNNING", s="running", f="screenshots/tv-bridge-home.png",
         c="Pro, paired: RUNNING with uptime, Healthy, CONNECTED, address/mic/accessibility/foreground, four-step setup, paired-with rows. Red <b>Stop service</b> action."),
    dict(g="Bridge home", t="Bridge home — STOPPED (green action)", s="stopped", f="screenshots/tv-bridge-home-stopped.png",
         c="Bridge stopped: the service action turns <b>green “Start service”</b> with a power glyph; the status chip reads STOPPED. Tapping it starts the bridge and flips back to red “Stop service”."),
    dict(g="Bridge home", t="Bridge home — 4K Plus", s="running", f="screenshots/tv-bridge-home-4k-plus.png",
         c="Second box (onn. 4K Plus, 192.168.5.205): same UI at its own IP; the “Paired with” row uses the device’s real name."),

    dict(g="Pairing", t="Pairing — waiting for DSH approval", s="waiting", f="screenshots/tv-pairing.png",
         c="STEP 1 hero, real daemon QR, tracked mono code and countdown, device chip, waiting spinner, three-step tracker, exported TV+laptop scene, LAN footer."),
    dict(g="Pairing", t="Pairing — 4K Plus waiting", s="waiting", f="screenshots/tv-pairing-4k-plus.png",
         c="Same flow on the 4K Plus: the chip shows that box’s own identity and IP; approving the request in DSH finishes pairing on the TV."),
    dict(g="Pairing", t="Pairing — idle", s="idle", f="screenshots/tv-pairing-idle.png",
         c="Idle state before a session exists: READY badge, empty QR plate, dash code, the Mac address field and the <b>Pair this TV</b> primary action."),
    dict(g="Pairing", t="Pairing — Mac unreachable", s="error", f="screenshots/tv-pairing-error.png",
         c="Error state when the Mac cannot be reached: “Could not reach the Mac: Failed to connect to …”. The address stays editable and Pair retries; “Use a different Mac” is the escape hatch."),

    dict(g="Assistant modal", t="Assistant — listening", s="listening", f="screenshots/tv-assistant-listening.png",
         c="Modal over Stremio: light black dim + soft blur so the screen below stays readable. Gear at the <b>left end of the control row above the composer</b>; mic and close on the right; pet, remote-hint pill and credit."),
    dict(g="Assistant modal", t="Assistant — thinking", s="thinking", f="screenshots/tv-assistant-thinking.png",
         c="THINKING while DSH works: pulsing dot, “DSH is working on it…” and the think pet. Captured with the QA hook <code>am start -n com.jp.dshtv/.WhaleActivity --ez thinking true</code>."),
    dict(g="Assistant modal", t="Assistant — answered", s="answered", f="screenshots/tv-assistant-answered.png",
         c="Answered state with the heard line and the reply, over Stremio; the app chip names the app behind the modal."),
    dict(g="Assistant modal", t="Assistant — Try again", s="error", f="screenshots/tv-assistant-error.png",
         c="Real mic VAD timeout / nothing heard: TRY AGAIN eyebrow, destructive rule and pet wilt; the gear stays reachable."),
    dict(g="Assistant modal", t="Settings gear — focus", s="focus", f="screenshots/tv-assistant-gear-focus.png",
         c="D-pad LEFT from the composer focuses the Lucide-outlined gear (2dp ring) at the row’s left end; ENTER opens the Bridge/settings screen."),
    dict(g="Assistant modal", t="Modal over a text-heavy app", s="modal", f="screenshots/tv-assistant-modal-stremio.png",
         c="The light modal over Stremio: the page title, description and “Continue Watching” row remain legible behind the dim + light blur."),
    dict(g="Assistant modal", t="Modal over the launcher", s="modal", f="screenshots/tv-assistant-modal.png",
         c="Listening modal over the Projectivy launcher; the bubble, pet and controls stay the crispest elements."),

    dict(g="Suggestions & demo", t="FOR YOU suggestion", s="suggestion", f="screenshots/tv-suggestion.png",
         c="Proactive suggestion overlay: research-backed pick with the “Want to watch it here?” question."),
    dict(g="Suggestions & demo", t="K-drama demo — recommend+reveal (4K Plus)", s="demo", f="screenshots/tv-demo-plus-reveal.png",
         c="The demo run on the onn. 4K Plus: top-3 research from r/kdrama/MyDramaList + the FOR YOU overlay."),
    dict(g="Suggestions & demo", t="K-drama demo — Stremio streams (4K Plus)", s="demo", f="screenshots/tv-demo-plus-stremio.png",
         c="The play leg on the 4K Plus: Stremio stream list. The catalog/search matcher is still the known gap (see docs/DEMO.md)."),

    dict(g="DSH pane", t="Whale-chan TV pane (light)", s="ready", f="screenshots/pane-live.png",
         c="The DSH settings section: daemon + TV bridge state, the TV it found, and live pairing requests with Approve / Deny inside DSH."),
    dict(g="DSH pane", t="Pane — all phases", s="phases", f="screenshots/pane-preview.png",
         c="Every phase rendered from the real component: loading, daemon down, no TVs, ready, pending, approved, error."),
    dict(g="DSH pane", t="Pane — modal width", s="phases", f="screenshots/pane-preview-modal.png",
         c="The same component at the settings-modal width (760px), light and dark."),
    dict(g="DSH pane", t="Pane — dark theme", s="ready", f="../plugin/ui/docs/screenshots/pane-live-dark.png",
         c="The pane in the host’s dark theme — it takes the host’s --dsw tokens, not its own colours."),

    dict(g="Launcher", t="Leanback tile (stock Google TV)", s="icon", f="screenshots/tv-launcher-tile.png",
         c="Adaptive icon on the stock launcher: the whale + “tv” both survive the circle crop."),
    dict(g="Launcher", t="Launcher frame", s="icon", f="screenshots/tv-launcher-stock.png",
         c="Full 1920×1080 launcher frame after install."),
    dict(g="Launcher", t="Projectivy all-apps", s="icon", f="screenshots/tv-app-drawer.png",
         c="DeepSeek TV in Projectivy’s All apps list — the white adaptive tile shows the whale + “tv”, so the row reads exactly like the launcher tile."),

    dict(g="Design reference", t="Design — Bridge home", s="design", f="screenshots/ui-playground-bridge.png",
         c="The target render from docs/ui-mockup.html (interactive design reference)."),
    dict(g="Design reference", t="Design — Pairing", s="design", f="screenshots/ui-playground-pairing.png",
         c="The pairing hero the TV screen was ported from."),
    dict(g="Design reference", t="Design — Assistant", s="design", f="screenshots/ui-playground-assistant.png",
         c="The overlay design; the implementation adds the real blur/scrim backdrop, gear, and live states."),
    dict(g="Design reference", t="Design — Primitives", s="design", f="screenshots/ui-playground-primitives.png",
         c="Buttons, badges, inputs, alerts, colour and type tokens (EVA dark / shadcn names)."),
]

MAX_W = 1600
MAX_H = 1600
JPEG_Q = "3"  # ffmpeg -q:v (≈ 85)


def convert(src: Path) -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(
        f"{src}|{src.stat().st_size}|{src.stat().st_mtime_ns}|{MAX_W}x{MAX_H}|{JPEG_Q}".encode()
    ).hexdigest()[:16]
    out = CACHE / f"{key}.jpg"
    if out.exists():
        return out
    if shutil.which("ffmpeg"):
        subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-y", "-i", str(src),
             "-vf", f"scale=w={MAX_W}:h={MAX_H}:force_original_aspect_ratio=decrease:flags=lanczos",
             "-q:v", JPEG_Q, str(out)],
            check=True,
        )
    elif shutil.which("sips"):
        subprocess.run(
            ["sips", "-Z", str(MAX_W), "-s", "format", "jpeg", "-s", "formatOptions", "80",
             str(src), "--out", str(out)],
            check=True, stdout=subprocess.DEVNULL,
        )
    else:
        raise SystemExit("need ffmpeg or sips to re-encode the screenshots")
    return out


def data_uri(path: Path) -> str:
    raw = path.read_bytes()
    return "data:image/jpeg;base64," + base64.b64encode(raw).decode()


def main() -> int:
    entries = []
    total = 0
    for e in SCREENS:
        src = (DOCS / e["f"]).resolve()
        if not src.exists():
            raise SystemExit(f"missing screenshot: {e['f']} -> {src}")
        jpg = convert(src)
        total += jpg.stat().st_size
        entries.append(dict(g=e["g"], t=e["t"], s=e["s"], c=e["c"], d=data_uri(jpg),
                            f=e["f"]))

    brand_src = DOCS / "screenshots" / "tv-launcher-tile.png"
    brand = data_uri(convert(brand_src)) if brand_src.exists() else ""

    payload = json.dumps(entries, ensure_ascii=False)
    html = TEMPLATE.replace("__BRAND__", brand).replace("__SCREENS__", payload)
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}  ({len(html)/1e6:.1f} MB, {len(entries)} screens, "
          f"{total/1e6:.1f} MB of embedded JPEGs)")
    return 0


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>DeepSeek TV Assistant · UI gallery</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {
    --bg: #080b13; --panel: #0e1420; --panel-2: #121a29; --line: #223049;
    --text: #e8eefb; --muted: #8f9bb3; --primary: #4d6bff; --success: #3dffa8;
    --shadow: 0 24px 60px rgba(0,0,0,.55);
    --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Roboto, sans-serif;
  }
  * { box-sizing: border-box; }
  html, body { height: 100%; }
  body {
    margin: 0; background: radial-gradient(1200px 700px at 78% -10%, rgba(77,107,255,.18), transparent 60%),
                radial-gradient(900px 600px at 5% 110%, rgba(255,79,216,.10), transparent 60%), var(--bg);
    color: var(--text); font-family: var(--font); overflow: hidden;
  }
  .shell { display: flex; height: 100vh; }
  .rail {
    width: 296px; flex: 0 0 296px; background: rgba(10,14,23,.82); border-right: 1px solid var(--line);
    display: flex; flex-direction: column; backdrop-filter: blur(18px); overflow: hidden;
  }
  .brand { display: flex; gap: 11px; align-items: center; padding: 20px 18px 16px; }
  .brand img { width: 34px; height: 34px; border-radius: 8px; object-fit: cover; }
  .brand b { display: block; font-size: 14px; letter-spacing: -.01em; }
  .brand span { display: block; font-size: 11.5px; color: var(--muted); margin-top: 2px; }
  .rail-scroll { overflow-y: auto; padding: 0 10px 20px; }
  .group-label {
    font-size: 10.5px; letter-spacing: .14em; text-transform: uppercase; color: var(--muted);
    font-weight: 700; padding: 14px 8px 6px;
  }
  .nav button {
    display: flex; align-items: center; gap: 9px; width: 100%; text-align: left;
    background: transparent; border: 0; border-radius: 8px; padding: 8px 9px;
    color: var(--text); font: inherit; font-size: 12.5px; cursor: pointer;
  }
  .nav button:hover { background: var(--panel-2); }
  .nav button[aria-current="true"] { background: linear-gradient(180deg, rgba(77,107,255,.22), rgba(77,107,255,.10)); box-shadow: inset 0 0 0 1px rgba(77,107,255,.5); }
  .nav .dot { width: 6px; height: 6px; border-radius: 50%; background: var(--muted); flex: 0 0 auto; }
  .nav button[aria-current="true"] .dot { background: var(--success); }
  .nav .tag { margin-left: auto; font-size: 9.5px; color: var(--muted); letter-spacing: .08em; text-transform: uppercase; }
  .rail-foot { padding: 12px 18px 16px; border-top: 1px solid var(--line); color: var(--muted); font-size: 11px; line-height: 1.5; }
  .rail-foot a { color: #a9bcff; }
  .main { flex: 1; display: flex; flex-direction: column; min-width: 0; }
  .main-head { display: flex; align-items: baseline; gap: 14px; padding: 20px 26px 12px; }
  .main-head h1 { margin: 0; font-size: 19px; letter-spacing: -.02em; }
  .main-head .meta { color: var(--muted); font-size: 12px; }
  .main-head .meta .pill {
    display: inline-block; margin-left: 8px; padding: 3px 9px; border-radius: 999px;
    border: 1px solid var(--line); background: var(--panel); font-size: 10.5px; letter-spacing: .08em; text-transform: uppercase;
  }
  .stage-wrap { flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; padding: 0 26px; }
  .stage {
    position: relative; width: 100%; max-width: 1600px; aspect-ratio: 16 / 9; max-height: 100%;
    background: #05070d; border: 1px solid var(--line); border-radius: 14px; overflow: hidden; box-shadow: var(--shadow);
  }
  .stage img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: contain; display: block; background: #05070d; }
  .caption { padding: 12px 28px 0; color: var(--muted); font-size: 12.5px; line-height: 1.5; min-height: 34px; }
  .caption b { color: var(--text); font-weight: 600; }
  .caption code { font-family: ui-monospace, Menlo, monospace; color: #a9bcff; font-size: 11.5px; }
  .thumbs { display: flex; gap: 10px; overflow-x: auto; padding: 14px 26px 8px; scrollbar-width: thin; }
  .thumb {
    flex: 0 0 auto; width: 150px; border-radius: 8px; border: 1px solid var(--line); overflow: hidden;
    background: #05070d; padding: 0; cursor: pointer; opacity: .68; transition: opacity .12s, transform .12s, border-color .12s;
  }
  .thumb img { width: 100%; aspect-ratio: 16/9; object-fit: cover; display: block; }
  .thumb span { display: block; padding: 5px 7px 6px; font-size: 10.5px; color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .thumb:hover { opacity: .95; transform: translateY(-1px); }
  .thumb[aria-current="true"] { opacity: 1; border-color: rgba(77,107,255,.75); box-shadow: 0 0 0 1px rgba(77,107,255,.45); }
  .bar { display: flex; align-items: center; gap: 10px; padding: 6px 26px 18px; }
  .bar .hint { color: var(--muted); font-size: 11.5px; margin-left: auto; }
  .btn {
    display: inline-flex; align-items: center; gap: 7px; height: 32px; padding: 0 13px; border-radius: 8px;
    border: 1px solid var(--line); background: var(--panel-2); color: var(--text); font: inherit; font-size: 12px; cursor: pointer;
  }
  .btn:hover { border-color: #3a4d72; }
  .btn.small { height: 28px; padding: 0 10px; font-size: 11.5px; }
  .bar .file { color: var(--muted); font-size: 11.5px; font-family: ui-monospace, Menlo, monospace; }
  @media (max-width: 900px) { .rail { width: 220px; flex-basis: 220px; } .main-head h1 { font-size: 16px; } }
</style>
</head>
<body>
<div class="shell">
  <aside class="rail">
    <div class="brand">
      <img src="__BRAND__" alt="">
      <div><b>DeepSeek TV Assistant</b><span>UI gallery · real screens</span></div>
    </div>
    <div class="rail-scroll"><div class="nav" id="nav"></div></div>
    <div class="rail-foot">
      Self-contained page: every shot is embedded, so it opens from anywhere.<br>
      All captures are 1920×1080 from the onn. 4K Pro / onn. 4K Plus.<br>
      Design reference: <a href="ui-mockup.html">ui-mockup.html</a>
    </div>
  </aside>

  <main class="main">
    <div class="main-head">
      <h1 id="title">Bridge home</h1>
      <div class="meta" id="meta"></div>
    </div>
    <div class="stage-wrap">
      <div class="stage" id="stage"><img id="img" alt="" /></div>
    </div>
    <div class="caption" id="caption"></div>
    <div class="thumbs" id="thumbs"></div>
    <div class="bar">
      <button class="btn" id="prev">← Previous</button>
      <button class="btn" id="next">Next →</button>
      <span class="file" id="file"></span>
      <span class="hint">← / → to walk through every screen</span>
    </div>
  </main>
</div>

<script>
  const SCREENS = __SCREENS__;
  const nav = document.getElementById('nav');
  const img = document.getElementById('img');
  const titleEl = document.getElementById('title');
  const metaEl = document.getElementById('meta');
  const captionEl = document.getElementById('caption');
  const thumbsEl = document.getElementById('thumbs');
  const fileEl = document.getElementById('file');
  let index = 0;

  let lastGroup = null;
  SCREENS.forEach((s, i) => {
    if (s.g !== lastGroup) {
      const label = document.createElement('div');
      label.className = 'group-label';
      label.textContent = s.g;
      nav.appendChild(label);
      lastGroup = s.g;
    }
    const b = document.createElement('button');
    b.type = 'button';
    b.dataset.index = String(i);
    b.innerHTML = '<span class="dot"></span><span>' + s.t.replace(/^[^—]*—\s*/, '') + '</span><span class="tag">' + s.s + '</span>';
    b.addEventListener('click', () => show(i));
    nav.appendChild(b);
  });

  function show(i) {
    index = (i + SCREENS.length) % SCREENS.length;
    const s = SCREENS[index];
    img.src = s.d;
    img.alt = s.t;
    titleEl.textContent = s.g + ' · ' + s.t.replace(/^[^—]*—\s*/, '');
    metaEl.innerHTML = '<span class="pill">' + s.s + '</span>';
    captionEl.innerHTML = s.c;
    fileEl.textContent = 'docs/' + s.f;
    [...nav.querySelectorAll('button')].forEach((b) => b.setAttribute('aria-current', String(Number(b.dataset.index) === index)));
    const group = SCREENS.map((x, j) => ({ x, j })).filter(({ x }) => x.g === s.g);
    thumbsEl.innerHTML = '';
    group.forEach(({ x, j }) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'thumb';
      b.setAttribute('aria-current', String(j === index));
      b.title = x.t;
      b.innerHTML = '<img src="' + x.d + '" alt=""><span>' + x.t.replace(/^[^—]*—\s*/, '') + '</span>';
      b.addEventListener('click', () => show(j));
      thumbsEl.appendChild(b);
    });
    const active = [...nav.querySelectorAll('button')].find((b) => b.getAttribute('aria-current') === 'true');
    if (active) active.scrollIntoView({ block: 'nearest' });
    history.replaceState(null, '', '#' + index);
  }

  document.getElementById('prev').addEventListener('click', () => show(index - 1));
  document.getElementById('next').addEventListener('click', () => show(index + 1));
  document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft') { e.preventDefault(); show(index - 1); }
    if (e.key === 'ArrowRight') { e.preventDefault(); show(index + 1); }
  });

  const fromHash = Number((location.hash || '').replace('#', ''));
  show(Number.isFinite(fromHash) && fromHash >= 0 && fromHash < SCREENS.length ? fromHash : 0);
</script>
</body>
</html>
"""

if __name__ == "__main__":
    sys.exit(main())
