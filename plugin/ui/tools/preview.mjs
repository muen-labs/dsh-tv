// Render the pane's phases to a static page so the layout can be looked at
// without booting the whole harness. Uses the real component + react-dom/server.
import { build } from 'esbuild'
import { writeFileSync, mkdirSync } from 'node:fs'
import { createRequire } from 'node:module'
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
const { WhaleTvSection, en } = require('./.preview-client.cjs')

const devices = [{ host: '192.168.4.58', port: 8765, model: 'onn. Streaming Device 4K pro', label: 'onn. 4K pro' }]
const qr = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='
const cases = [
  ['loading', { phase: 'loading' }],
  ['error', { phase: 'error', error: 'connect ECONNREFUSED 127.0.0.1:8766' }],
  ['empty', { phase: 'empty' }],
  ['ready', { phase: 'ready', devices }],
  ['pairing', { phase: 'ready', devices, pair: { id: 'x', code: 'AZP74K', qr, url: 'http://192.168.4.57:8766/pair?id=x' }, pairState: 'pending' }],
]

const t = (key) => en[key] ?? key
const cards = cases.map(([name, preview]) => `
  <figure>
    <figcaption>${name}</figcaption>
    <div class="pane">${renderToStaticMarkup(React.createElement(WhaleTvSection, { t, preview }))}</div>
  </figure>`).join('\n')

const html = `<!doctype html><meta charset="utf-8"><title>Whale-chan pane preview</title>
<style>
  :root { --dsw-alias-bg-layer-2:#171a21; --dsw-alias-bg-layer-3:#232735; --dsw-alias-border-l2:#2c3140;
          --dsw-alias-border-l3:#394052; --dsw-alias-brand-primary:#4fc3f7; --dsw-alias-label-primary:#e8eef7;
          --dsw-alias-label-caption:#8b98ab; --dsw-alias-label-error:#ff7b72; --dsw-alias-label-primary-foreground:#0b1017;
          --dsw-alias-button-primary-fill:#4fc3f7; }
  body { background:#0b0e14; color:#e8eef7; font:14px/1.45 system-ui, sans-serif; margin:0; padding:24px; }
  h1 { font-size:16px; font-weight:600; margin:0 0 16px; color:#8b98ab; }
  .grid { display:flex; flex-wrap:wrap; gap:20px; align-items:flex-start; }
  figure { margin:0; width:380px; }
  figcaption { font-size:12px; color:#8b98ab; margin-bottom:6px; text-transform:uppercase; letter-spacing:.08em; }
  .pane { background:#0f131b; border:1px solid #222836; border-radius:12px; padding:12px; }
</style>
<h1>Whale-chan TV pane — phases at 340px</h1>
<div class="grid">${cards}</div>`
mkdirSync('../../docs/screenshots', { recursive: true })
writeFileSync('../../docs/screenshots/pane-preview.html', html)
console.log('wrote docs/screenshots/pane-preview.html')
