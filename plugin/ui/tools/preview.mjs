// Render every pane phase from the REAL component (react-dom/server) into a
// static page, at the two widths the Settings shell can give it (340px pane,
// 760px modal content) in both themes. Then optionally screenshot it.
//
//   node tools/preview.mjs          # docs/screenshots/pane-preview.html
//   node tools/preview.mjs --png    # + pane-preview.png (headless Chrome)
//
// The token blocks come from the installed DSH theme bundle when it is found,
// so the preview paints with the same --dsw-* values the app uses; the fallback
// map keeps the tool usable on a machine without that runtime.
import { build } from 'esbuild'
import { execFileSync } from 'node:child_process'
import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import { homedir } from 'node:os'
import path from 'node:path'
import * as React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'

await build({
  entryPoints: ['src/client.tsx'],
  outfile: 'tools/.preview-client.cjs',
  bundle: true,
  platform: 'node',
  format: 'cjs',
  jsx: 'automatic',
  external: ['react', 'react-dom'],
})
const require = createRequire(import.meta.url)
const { WhaleTvSection, en, zh } = require('./.preview-client.cjs')

const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
const OUT_HTML = path.resolve('docs/screenshots/pane-preview.html')
const OUT_PNG = path.resolve('docs/screenshots/pane-preview.png')

const status = {
  ok: true,
  daemon: { reachable: true, url: 'http://127.0.0.1:8766', status: 200, sessionId: 'session-a180288b', tv: { ok: true, host: '192.168.4.58', port: 8765 } },
  token: { present: true },
  target: { host: '192.168.4.58', port: 8765 },
  bridge: { alive: true, host: '192.168.4.58', port: 8765, ok: true, app: 'dshtv', version: 1, ms: 8 },
}
const statusDown = {
  ...status,
  daemon: { reachable: false, url: 'http://127.0.0.1:8766', status: 0, error: 'connect ECONNREFUSED 127.0.0.1:8766' },
}
const statusNoTarget = { ...status, target: null, bridge: null }
const devices = [
  { host: '192.168.4.58', port: 8765, alive: true, model: null, app: 'dshtv', version: 1 },
]
const scanned = { mode: 'configured+sweep', candidates: 253, answered: 0, tookMs: 264, cached: false }
const pending = [
  { id: '91231a1c98c93927', code: 'BM7U23', createdAt: Date.now(), ageSeconds: 12, host: '192.168.4.58' },
]

const cases = [
  ['loading', 'light', 340, { phase: 'loading' }],
  ['route error', 'light', 340, { phase: 'error', status: null, error: 'Failed to fetch' }],
  ['daemon down', 'light', 340, { phase: 'down', status: statusDown, error: 'connect ECONNREFUSED' }],
  ['empty (no TVs)', 'light', 340, { phase: 'empty', status, devices: [], scanned }],
  ['ready', 'light', 340, { phase: 'ready', status, devices, scanned }],
  ['pairing request', 'light', 340, { phase: 'ready', status, devices, scanned, pending }],
  ['approving', 'light', 340, { phase: 'ready', status, devices, scanned, pending, busyId: pending[0].id }],
  ['approved', 'light', 340, { phase: 'ready', status, devices, scanned, pending: [], approval: { id: pending[0].id, kind: 'approved' } }],
  ['no bridge target', 'light', 340, { phase: 'empty', status: statusNoTarget, devices: [] }],
  ['ready (zh)', 'light', 340, { phase: 'ready', status, devices, scanned, pending }, zh],
  ['ready', 'dark', 340, { phase: 'ready', status, devices, scanned }],
  ['pairing request', 'dark', 340, { phase: 'ready', status, devices, scanned, pending }],
]

const fallback = {
  statics:
    ':root{--dsw-static-neutral-bluish-00:#fff;--dsw-static-neutral-bluish-50:#f9fafb;--dsw-static-neutral-bluish-60:#f9fafb;--dsw-static-neutral-bluish-75:#f1f3f5;--dsw-static-neutral-bluish-100:#ebeef2;--dsw-static-neutral-bluish-150:#e9ecf2;--dsw-static-neutral-bluish-200:#e1e5ee;--dsw-static-neutral-bluish-300:#cfd3d6;--dsw-static-neutral-bluish-400:#adb2b8;--dsw-static-neutral-bluish-500:#979da6;--dsw-static-neutral-bluish-600:#81858c;--dsw-static-neutral-bluish-700:#61666b;--dsw-static-neutral-bluish-750:#43454a;--dsw-static-neutral-bluish-800:#353638;--dsw-static-neutral-bluish-850:#2c2c2e;--dsw-static-neutral-bluish-875:#232324;--dsw-static-neutral-bluish-950:#151517;--dsw-static-neutral-bluish-1000:#0f1115;--dsw-static-green-500:#22c55e;--dsw-static-red-400:#f25a5a;--dsw-static-red-600:#ec1313;--dsw-static-amber-500:#f59e0b;--dsw-static-neutral-bluish-500:#979da6;--ds-font-family-code:"SF Mono", "JetBrains Mono", Consolas, Menlo, monospace;--dsw-font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",sans-serif;--dsw-font-m-18:500 16px/28px var(--dsw-font-family);--dsw-font-s-14:14px/22px var(--dsw-font-family);--dsw-font-s-strong-14:500 14px/22px var(--dsw-font-family);--dsw-font-xs-13:13px/20px var(--dsw-font-family);--dsw-font-xxs-12:12px/18px var(--dsw-font-family)}',
  light:
    '.theme-light{--dsw-alias-bg-base:var(--dsw-static-neutral-bluish-00);--dsw-alias-bg-layer-1:var(--dsw-static-neutral-bluish-00);--dsw-alias-bg-layer-2:var(--dsw-static-neutral-bluish-00);--dsw-alias-bg-layer-3:var(--dsw-static-neutral-bluish-00);--dsw-alias-bg-module-platform:var(--dsw-static-neutral-bluish-60);--dsw-alias-border-l1:#0000000a;--dsw-alias-border-l2:#0000001a;--dsw-alias-border-l3:#0000001f;--dsw-alias-brand-primary:var(--dsw-static-neutral-bluish-1000);--dsw-alias-label-primary:var(--dsw-static-neutral-bluish-1000);--dsw-alias-label-secondary:var(--dsw-static-neutral-bluish-700);--dsw-alias-label-tertiary:var(--dsw-static-neutral-bluish-600);--dsw-alias-label-dimmed:var(--dsw-static-neutral-bluish-200);--dsw-alias-interactive-bg-hover:#2631480f;--dsw-alias-state-success-primary:var(--dsw-static-green-500);--dsw-alias-state-error-primary:var(--dsw-static-red-600);--dsw-alias-state-warn-primary:var(--dsw-static-amber-500);--dsw-alias-state-business-primary:#4176e6}',
  dark:
    '.theme-dark{--dsw-alias-bg-base:var(--dsw-static-neutral-bluish-950);--dsw-alias-bg-layer-1:var(--dsw-static-neutral-bluish-875);--dsw-alias-bg-layer-2:var(--dsw-static-neutral-bluish-850);--dsw-alias-bg-layer-3:var(--dsw-static-neutral-bluish-800);--dsw-alias-bg-module-platform:var(--dsw-static-neutral-bluish-750);--dsw-alias-border-l1:#ffffff0f;--dsw-alias-border-l2:#ffffff1f;--dsw-alias-border-l3:#ffffff29;--dsw-alias-brand-primary:var(--dsw-static-neutral-bluish-50);--dsw-alias-label-primary:var(--dsw-static-neutral-bluish-50);--dsw-alias-label-secondary:var(--dsw-static-neutral-bluish-300);--dsw-alias-label-tertiary:var(--dsw-static-neutral-bluish-400);--dsw-alias-label-dimmed:var(--dsw-static-neutral-bluish-750);--dsw-alias-interactive-bg-hover:#ffffff14;--dsw-alias-state-success-primary:var(--dsw-static-green-500);--dsw-alias-state-error-primary:var(--dsw-static-red-400);--dsw-alias-state-warn-primary:var(--dsw-static-amber-500);--dsw-alias-state-business-primary:#679efe}',
}

/** Pull the real theme token blocks out of the installed runtime, if present. */
function themeTokens() {
  const roots = []
  if (process.env.DSH_RUNTIME_ROOT) roots.push(process.env.DSH_RUNTIME_ROOT)
  const hub = path.join(homedir(), '.dsh', '.hub', 'runtimes')
  if (existsSync(hub)) {
    for (const version of readdirSync(hub)) roots.push(path.join(hub, version, 'node_modules', '@deepseek-ai'))
  }
  for (const root of roots) {
    const file = path.join(root, 'dsh-client-ui-theme', 'lib', 'client.js')
    if (!existsSync(file)) continue
    const source = readFileSync(file, 'utf8')
    const aliasLight = source.match(/body\s*\{([^{}]*--dsw-alias-bg-base[^{}]*)\}/)
    const aliasDark = source.match(/body\[data-ds-dark-theme\]\s*\{([^{}]*--dsw-alias-bg-base[^{}]*)\}/)
    const statics = source.match(/body\s*\{([^{}]*--dsw-static-neutral-bluish-00[^{}]*)\}/)
    const staticsDark = source.match(/body\[data-ds-dark-theme\]\s*\{([^{}]*--dsw-static-neutral-bluish-00[^{}]*)\}/)
    const base = source.match(/:root\s*\{([^{}]*--dsw-font-family[^{}]*)\}/)
    if (!aliasLight || !aliasDark) continue
    return {
      used: file,
      statics: `:root{${base ? base[1] : ''}}\n:root{${statics ? statics[1] : ''}}`,
      light: `.theme-light{${aliasLight[1]}}`,
      dark: `.theme-dark{${staticsDark ? staticsDark[1] : ''}}\n.theme-dark{${aliasDark[1]}}`,
    }
  }
  return { used: null, ...fallback }
}

const tokens = themeTokens()

function card(name, theme, width, preview, translator) {
  const t = translator ?? ((key) => en[key] ?? key)
  const markup = renderToStaticMarkup(React.createElement(WhaleTvSection, { t, preview }))
  const wide = width > 340 ? ' wide' : ''
  return `
  <figure class="case${wide}">
    <figcaption><b>${name}</b><span>${theme} · ${width}px</span></figcaption>
    <div class="pane theme-${theme}${wide}" style="width:${width}px">${markup}</div>
  </figure>`
}

const mainCases = cases
const modalCases = [
  ['modal width (760px) · pairing request', 'light', 760, { phase: 'ready', status, devices, scanned, pending }],
  ['modal width (760px) · pairing request', 'dark', 760, { phase: 'ready', status, devices, scanned, pending }],
]

const head = `<!doctype html>
<html><head><meta charset="utf-8"><title>Whale-chan TV pane preview</title>
<style>
${tokens.statics}
${tokens.light}
${tokens.dark}
* { box-sizing: border-box; }
body { margin: 0; padding: 20px; background: #e9ecf2; color: #0f1115;
       font-family: var(--dsw-font-family); -webkit-font-smoothing: antialiased; }
h1 { margin: 0 0 4px; font-size: 15px; font-weight: 600; }
.lede { margin: 0 0 18px; font-size: 12px; color: #61666b; }
.grid { display: flex; flex-wrap: wrap; gap: 18px; align-items: flex-start; }
.case { margin: 0; }
.case.wide { flex-basis: 100%; }
figcaption { display: flex; align-items: baseline; gap: 8px; margin: 0 2px 6px; font-size: 11px; color: #61666b; }
figcaption b { font-weight: 600; color: #0f1115; }
.pane { border-radius: 18px; padding: 16px; background: var(--dsw-alias-bg-layer-2); border: 1px solid var(--dsw-alias-border-l1); }
.pane.wide { border-radius: 24px; padding: 24px; }
</style></head>
<body>
<h1>Whale-chan TV — Settings section preview</h1>
<p class="lede">Rendered from the real component with react-dom/server · tokens ${tokens.used ? 'the installed dsh-client-ui-theme runtime' : 'fallback map'}</p>
<div class="grid">`

function page(list) {
  return head + list.map(([name, theme, width, preview, translator]) => card(name, theme, width, preview, translator)).join('') + '</div></body></html>'
}

function screenshot(out, windowSize) {
  if (!process.argv.includes('--png')) return
  if (!existsSync(CHROME)) {
    console.error(`no Chrome at ${CHROME}; skipped ${path.basename(out)}`)
    return
  }
  try {
    execFileSync(
      CHROME,
      [
        '--headless=new',
        '--disable-gpu',
        '--hide-scrollbars',
        '--force-device-scale-factor=2',
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--virtual-time-budget=3000',
        '--user-data-dir=/tmp/whale-pane-preview-chrome',
        `--window-size=${windowSize}`,
        `--screenshot=${out}`,
        'file://' + out.replace(/\.png$/, '.html'),
      ],
      { stdio: 'ignore' },
    )
  } catch (error) {
    if (!existsSync(out)) throw error
    // Headless Chrome on macOS can exit non-zero after writing the file.
  }
  console.log(`wrote ${path.relative(process.cwd(), out)}`)
}

mkdirSync(path.dirname(OUT_HTML), { recursive: true })
writeFileSync(OUT_HTML, page(mainCases))
console.log(`wrote ${path.relative(process.cwd(), OUT_HTML)} (${mainCases.length} phases)`)
screenshot(OUT_PNG, '1180,3140')

const MODAL_HTML = path.resolve('docs/screenshots/pane-preview-modal.html')
const MODAL_PNG = path.resolve('docs/screenshots/pane-preview-modal.png')
writeFileSync(MODAL_HTML, page(modalCases))
console.log(`wrote ${path.relative(process.cwd(), MODAL_HTML)} (${modalCases.length} phases at 760px)`)
screenshot(MODAL_PNG, '810,1560')
