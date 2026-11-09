// Mount the host half with a stub cordis context and exercise every route over
// real HTTP against the live whale daemon. Run: node tools/verify-host.mjs
//
// WHALE_PLUGIN_ENTRY=<abs path to another lib/index.js> mounts an installed
// copy instead of the repo's own file (used to test install-ui.sh --copy).
import { createServer } from 'node:http'
import { readFileSync } from 'node:fs'
import { pathToFileURL } from 'node:url'

const ENTRY = process.env.WHALE_PLUGIN_ENTRY
  ? pathToFileURL(process.env.WHALE_PLUGIN_ENTRY).href
  : new URL('../lib/index.js', import.meta.url).href
const { apply } = await import(ENTRY)
console.log(`entry: ${ENTRY}`)

const TOKEN = readFileSync(new URL('../../../.auth/whale.token', import.meta.url), 'utf8').trim()
const requested = []
const routes = new Map()
const disposers = []

const ctx = {
  effect(fn, label) {
    const dispose = fn()
    disposers.push({ label, dispose })
    return dispose
  },
  webServer: {
    register(route) {
      if (routes.has(route.path)) throw new Error(`duplicate route ${route.path}`)
      if (route.path.endsWith('/')) throw new Error(`trailing slash route ${route.path}`)
      routes.set(route.path, route)
      return () => routes.delete(route.path)
    },
  },
}

apply(ctx)
console.log(`registered ${routes.size} routes: ${[...routes.keys()].join(', ')}`)

const server = createServer(async (req, res) => {
  const path = new URL(req.url || '/', 'http://x').pathname
  requested.push(`${req.method} ${path}`)
  const route = routes.get(path)
  if (route === undefined) {
    res.statusCode = 404
    return res.end('not found')
  }
  await route.handler(req, res)
})

await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve))
const base = `http://127.0.0.1:${server.address().port}`
console.log(`mounted on ${base}\n`)

const bodies = []
async function call(method, pathname, init = {}) {
  const res = await fetch(base + pathname, { method, ...init })
  const text = await res.text()
  bodies.push(text)
  let body
  try {
    body = JSON.parse(text)
  } catch {
    body = text
  }
  console.log(`${method} ${pathname} -> ${res.status}`)
  console.log(JSON.stringify(body, null, 2).slice(0, 1400))
  console.log('')
  return { status: res.status, body }
}

const status = await call('GET', '/whale-chan/status')
const devices = await call('GET', '/whale-chan/devices?fresh=1')
const created = await call('POST', '/whale-chan/pair/new')
const pending = await call('GET', '/whale-chan/pending')
const approved = await call('POST', '/whale-chan/pair/approve', {
  headers: { 'content-type': 'application/json' },
  body: JSON.stringify({ id: created.body.id }),
})
const pendingAfter = await call('GET', '/whale-chan/pending')
const pairStatus = await call('GET', `/whale-chan/pair/status?id=${encodeURIComponent(created.body.id)}`)
const second = await call('POST', '/whale-chan/pair/new')
const denied = await call('POST', '/whale-chan/pair/deny', {
  headers: { 'content-type': 'application/json' },
  body: JSON.stringify({ id: second.body.id }),
})
const missingId = await call('POST', '/whale-chan/pair/approve', {
  headers: { 'content-type': 'application/json' },
  body: '{}',
})
const wrongMethod = await call('POST', '/whale-chan/status')

// disposed plugin must stop answering
for (const entry of disposers) entry.dispose()
const afterDispose = await fetch(base + '/whale-chan/status')
console.log(`after dispose, GET /whale-chan/status -> ${afterDispose.status} (expect 404)`)

const failures = []
function check(label, condition, detail = '') {
  if (!condition) failures.push(`${label}${detail ? `: ${detail}` : ''}`)
}
check('status 200', status.status === 200)
check('status repo resolved', status.body.repo?.found === true, JSON.stringify(status.body.repo))
check('status daemon reachable', status.body.daemon?.reachable === true, JSON.stringify(status.body.daemon))
check('status bridge shape', status.body.bridge === null || typeof status.body.bridge.alive === 'boolean', JSON.stringify(status.body.bridge))
if (status.body.bridge?.alive !== true) console.log('note: TV bridge unreachable — device/bridge liveness checks are skipped, shape is still asserted')
check('status token present', status.body.token?.present === true)
check('status target host', status.body.target?.host === '192.168.4.58', JSON.stringify(status.body.target))
check('devices 200', devices.status === 200)
check('devices found the TV', status.body.bridge?.alive !== true || (Array.isArray(devices.body.devices) && devices.body.devices.some((d) => d.host === '192.168.4.58' && d.alive)))
check('device contract keys', devices.body.devices.every((d) => ['host', 'port', 'alive', 'model', 'app', 'version'].every((k) => k in d)))
check('pair/new ok', created.status === 200 && created.body.ok === true && typeof created.body.id === 'string')
check('pair/new QR is a PNG data URL', typeof created.body.qr === 'string' && Buffer.from(created.body.qr, 'base64').subarray(0, 8).equals(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])))
check('pending lists the new id', pending.body.pending?.some((p) => p.id === created.body.id))
check('pending row contract', pending.body.pending?.every((p) => ['id', 'code', 'createdAt', 'ageSeconds'].every((k) => k in p)))
check('approve ok', approved.status === 200 && approved.body.approved === true)
check('approved id leaves the pending list', !pendingAfter.body.pending?.some((row) => row.id === created.body.id))
check('daemon status approved + token stripped', pairStatus.body.approved === true && pairStatus.body.config?.hasToken === true && !('token' in (pairStatus.body.config || {})))
check('deny ok', denied.status === 200 && denied.body.denied === true)
check('missing id 400', missingId.status === 400 && missingId.body.ok === false)
check('wrong method 405', wrongMethod.status === 405)
check('dispose removes route', afterDispose.status === 404)
check('token never leaked to browser', bodies.every((text) => !text.includes(TOKEN)))

console.log('---')
if (failures.length > 0) {
  console.error(`FAIL (${failures.length})`)
  for (const failure of failures) console.error(' -', failure)
  server.close()
  process.exit(1)
}
console.log(`PASS — ${bodies.length} responses, ${requested.length} requests, token absent from every body`)
server.close()
