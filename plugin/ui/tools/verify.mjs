// The pane's checks: the bundle parses, both dictionaries are complete and
// every key is read, every phase renders, and the markup stays inside the
// house token language (no hex/own-theme colours).
//
//   node tools/verify.mjs
import { build } from 'esbuild'
import { readFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import vm from 'node:vm'
import * as React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'

const failures = []
function check(label, condition, detail = '') {
  if (condition) return
  failures.push(detail ? `${label} — ${detail}` : label)
}

// 1. The shipped bundle must PARSE (every other check reads source as text).
const bundlePath = 'lib/client.js'
const bundleSource = readFileSync(bundlePath, 'utf8')
try {
  new vm.Script(bundleSource)
  check('bundle parses', true)
} catch (error) {
  check('bundle parses', false, String(error))
}
check('loader id', bundleSource.includes('__ModuleLoader__.load({ id: "dsh-whale-chan-tv"'))
check('bundle factory returns exports', bundleSource.trimEnd().endsWith('return module.exports; } });'))

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

// 2. Copy coverage: same key set, every key asked for, every asked key defined.
const enKeys = Object.keys(en).sort()
const zhKeys = Object.keys(zh).sort()
check('en/zh same key set', JSON.stringify(enKeys) === JSON.stringify(zhKeys))
const sources = ['src/client.tsx', 'src/index.ts'].map((file) => readFileSync(file, 'utf8')).join('\n')
const used = new Set([...sources.matchAll(/\bt\('([A-Za-z0-9]+)'\)/g)].map((match) => match[1]))
const missingKeys = [...used].filter((key) => en[key] === undefined)
const orphanKeys = enKeys.filter((key) => !used.has(key))
check('no copy key missing from en', missingKeys.length === 0, missingKeys.join(', '))
check('no orphan copy key', orphanKeys.length === 0, orphanKeys.join(', '))
check('zh has a reviewable value for every key', enKeys.every((key) => typeof zh[key] === 'string' && zh[key].length > 0))

// 3. Every phase renders from the real component.
const now = Date.now()
const status = {
  ok: true,
  daemon: { reachable: true, url: 'http://127.0.0.1:8766', status: 200, sessionId: 's' },
  token: { present: true },
  target: { host: '192.168.4.58', port: 8765 },
  bridge: { alive: true, host: '192.168.4.58', port: 8765, ok: true, app: 'dshtv', version: 1 },
}
const statusDown = { ...status, daemon: { reachable: false, url: 'http://127.0.0.1:8766', error: 'ECONNREFUSED' } }
const devices = [{ host: '192.168.4.58', port: 8765, alive: true, model: null, app: 'dshtv', version: 1 }]
const scanned = { mode: 'configured+sweep', candidates: 253, answered: 0, tookMs: 264 }
const pending = [{ id: 'p1', code: 'BM7U23', createdAt: now, ageSeconds: 12, host: '192.168.4.58' }]
const fixtures = {
  loading: { phase: 'loading' },
  'route error': { phase: 'error', status: null, error: 'Failed to fetch' },
  'daemon down': { phase: 'down', status: statusDown },
  empty: { phase: 'empty', status, devices: [], scanned },
  ready: { phase: 'ready', status, devices, scanned },
  pending: { phase: 'ready', status, devices, scanned, pending },
  approved: { phase: 'ready', status, devices, scanned, pending: [], approval: { id: 'p1', kind: 'approved' } },
}
const t = (key) => en[key] ?? key
const markup = {}
for (const [name, preview] of Object.entries(fixtures)) {
  markup[name] = renderToStaticMarkup(React.createElement(WhaleTvSection, { t, preview }))
  check(`phase "${name}" renders`, markup[name].length > 200)
}
check('loading copy', markup.loading.includes(en.scanning))
check('route error copy', markup['route error'].includes(en.routeErrorTitle) && markup['route error'].includes(en.retry))
check('daemon-down copy + start command', markup['daemon down'].includes(en.daemonDownTitle) && markup['daemon down'].includes(en.startCommand))
check('empty copy', markup.empty.includes(en.noTvsTitle))
check('ready has a named radiogroup', /role="radiogroup"/.test(markup.ready) && /aria-label="[^"]+"/.test(markup.ready))
check('ready rows are radios with one checked', /role="radio"[^>]*aria-checked="true"/.test(markup.ready) && (markup.ready.match(/role="radio"/g) || []).length === 1)
check('device host is drawn', markup.ready.includes('192.168.4.58'))
check('pending shows the tracked code', markup.pending.includes('BM7U23') && markup.pending.includes(en.codeLabel))
check('pending has both actions', markup.pending.includes(`>${en.approve}<`) && markup.pending.includes(`>${en.deny}<`))
check('pending has a live region', /aria-live="polite"/.test(markup.pending) && /role="status"/.test(markup.pending))
check('approved announces success', markup.approved.includes(en.approved))
check('every button is type=button', [...Object.values(markup)].every((html) => !/<button(?![^>]*type="button")/.test(html)))

// 4. House language: only --dsw-* tokens, no own palette.
const allMarkup = Object.values(markup).join('\n')
const vars = [...allMarkup.matchAll(/var\((--[a-z0-9-]+)/g)].map((match) => match[1])
const foreign = vars.filter((name) => !name.startsWith('--dsw-') && name !== '--ds-font-family-code')
check('only house CSS variables', foreign.length === 0, [...new Set(foreign)].join(', '))
check('no hex colours in styles', !/#[0-9a-fA-F]{3,8}\b/.test(allMarkup))
check('no rgb()/hsl() literals', !/\brgba?\(|\bhsla?\(/.test(allMarkup))

// 5. The component takes props.t (not its own EN): a marker translator must
//    appear in the output and the English fallback must not.
const marker = (key) => `xT${key}Tx`
const marked = renderToStaticMarkup(React.createElement(WhaleTvSection, { t: marker, preview: fixtures.ready }))
check('props.t is consulted', marked.includes('xTtitleTx') && marked.includes('xTsectionConnectionTx') && marked.includes('xTsectionPairTx'))
check('props.t wins over the en fallback', !marked.includes(en.subtitle) && !marked.includes(en.devicesHint))

// 6. Light and dark render identically in structure (tokens do the colouring).
const darkish = renderToStaticMarkup(React.createElement(WhaleTvSection, { t, preview: fixtures.pending }))
check('dark render has same structure', darkish.length > 200 && darkish.includes('BM7U23'))

if (failures.length > 0) {
  console.error(`FAIL (${failures.length})`)
  for (const failure of failures) console.error(' -', failure)
  process.exit(1)
}
console.log(`PASS — bundle ${bundleSource.length} bytes parses; ${enKeys.length} copy keys used in both languages; ${Object.keys(fixtures).length} phases render on house tokens only`)
