// Host half of the Whale-chan TV settings pane.
//
// Same-origin JSON routes under /whale-chan/* so the browser half never talks
// to the voice daemon directly and never sees its token. Every handler answers
// JSON (with an `ok` field), never throws, and is registered through
// ctx.effect(() => ctx.webServer.register(...)) so unloading removes the route.
//
// Environment overrides (all optional):
//   WHALE_REPO         repository root (default: marker from --copy install, then derived)
//   WHALE_DAEMON_URL   whale daemon base URL (default http://127.0.0.1:8766)
//   WHALE_TOKEN        daemon token (default <repo>/.auth/whale.token)
//   WHALE_TV_CONFIG    TV bridge config (default <repo>/host/config.json)
import { existsSync, readFileSync } from 'node:fs'
import { readFile } from 'node:fs/promises'
import net from 'node:net'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

/** Services this plugin needs before it can register routes. */
export const inject = ['webServer']

/** This package's root (`.../node_modules/dsh-whale-chan-tv`, or the repo's plugin/ui). */
const PACKAGE_DIR = path.dirname(path.dirname(fileURLToPath(import.meta.url)))
/** A --copy install cannot derive the repo from its own path; the installer leaves this marker. */
const REPO_MARKER = path.join(PACKAGE_DIR, 'repo-path.txt')

/** A directory is a usable repo root when it has either the daemon or its token. */
function looksLikeRepo(root) {
  return existsSync(path.join(root, 'host', 'whale_voice.py')) || existsSync(path.join(root, '.auth', 'whale.token'))
}

/**
 * Resolve the repository root: env override, then the installer's marker (a
 * --copy install has no path back to the repo), then this file's position
 * (correct for a symlink install, where Node resolves the realpath).
 * @returns {{root: string | null, source: 'env' | 'marker' | 'derived' | null, lookedIn: string[]}}
 */
function resolveRepo() {
  const lookedIn = []
  const candidates = []
  if (process.env.WHALE_REPO) candidates.push({ source: 'env', root: path.resolve(process.env.WHALE_REPO) })
  try {
    const marker = readFileSync(REPO_MARKER, 'utf8').trim()
    if (marker) candidates.push({ source: 'marker', root: path.resolve(marker) })
  } catch {
    /* no marker: link install or manual copy */
  }
  candidates.push({ source: 'derived', root: path.resolve(PACKAGE_DIR, '..', '..') })
  for (const candidate of candidates) {
    lookedIn.push(candidate.root)
    if (looksLikeRepo(candidate.root)) return { root: candidate.root, source: candidate.source, lookedIn }
  }
  return { root: null, source: null, lookedIn }
}

const REPO_RESOLUTION = resolveRepo()
const REPO = REPO_RESOLUTION.root
const DAEMON = (process.env.WHALE_DAEMON_URL || 'http://127.0.0.1:8766').replace(/\/+$/, '')
const TOKEN_FILE = REPO === null ? null : path.join(REPO, '.auth', 'whale.token')
const TV_CONFIG = process.env.WHALE_TV_CONFIG || (REPO === null ? null : path.join(REPO, 'host', 'config.json'))

const DAEMON_TIMEOUT_MS = 8000
const BRIDGE_TIMEOUT_MS = 2000
const TCP_TIMEOUT_MS = 250
const DEVICE_CACHE_MS = 8000
const TARGET_CACHE_MS = 5000
const MAX_BODY_BYTES = 64 * 1024

function errorText(error) {
  if (error && typeof error === 'object') {
    if (error.name === 'TimeoutError' || error.name === 'AbortError') return 'timed out'
    if (error.cause && error.cause.code) return String(error.cause.code)
    if (error.message) return String(error.message)
  }
  return String(error)
}

function sendJson(res, status, payload) {
  const body = JSON.stringify(payload)
  res.statusCode = status
  res.setHeader('content-type', 'application/json; charset=utf-8')
  res.setHeader('cache-control', 'no-store')
  res.end(body)
}

/** Read the daemon token. Never logged, never returned to the browser. */
async function readToken() {
  if (process.env.WHALE_TOKEN) return process.env.WHALE_TOKEN.trim()
  if (TOKEN_FILE === null) return ''
  try {
    return (await readFile(TOKEN_FILE, 'utf8')).trim()
  } catch {
    return ''
  }
}

/** Bridge target from host/config.json (written by the TV pairing flow). */
async function readTarget() {
  if (TV_CONFIG === null) return null
  try {
    const raw = await readFile(TV_CONFIG, 'utf8')
    const cfg = JSON.parse(raw)
    const host = String(cfg.host || '').trim()
    const port = Number(cfg.port) || 8765
    if (!host) return null
    return { host, port }
  } catch {
    return null
  }
}

/** Honest repo-resolution facts for /whale-chan/status (never the token). */
function repoState() {
  return {
    found: REPO !== null,
    root: REPO,
    source: REPO_RESOLUTION.source,
    lookedIn: REPO_RESOLUTION.lookedIn,
    error: REPO === null
      ? 'repo not found: no .auth/whale.token or host/whale_voice.py in the paths above. ' +
        'Use a link install (install-ui.sh), re-run install-ui.sh --copy, or set WHALE_REPO.'
      : null,
  }
}

/** One JSON request to the whale daemon. Resolves; never rejects. */
async function daemonJson(pathname, init = {}) {
  const headers = { accept: 'application/json', ...(init.headers || {}) }
  let body
  if (init.body !== undefined) {
    headers['content-type'] = 'application/json'
    body = JSON.stringify(init.body)
  }
  try {
    const res = await fetch(DAEMON + pathname, {
      method: init.method || 'GET',
      headers,
      body,
      signal: AbortSignal.timeout(init.timeoutMs || DAEMON_TIMEOUT_MS),
    })
    const text = await res.text()
    let parsed
    try {
      parsed = JSON.parse(text)
    } catch {
      parsed = { ok: false, error: text.slice(0, 200) || `http ${res.status}` }
    }
    return { reachable: true, status: res.status, body: parsed }
  } catch (error) {
    return { reachable: false, status: 0, body: { ok: false, error: errorText(error) } }
  }
}

/** GET /ping on an Android TV bridge. Resolves; never rejects. */
async function bridgePing(host, port) {
  const started = Date.now()
  try {
    const res = await fetch(`http://${host}:${port}/ping`, {
      signal: AbortSignal.timeout(BRIDGE_TIMEOUT_MS),
    })
    let body = {}
    try {
      body = await res.json()
    } catch {
      body = {}
    }
    return {
      alive: true,
      host,
      port,
      ok: body.ok === true || res.ok,
      app: typeof body.app === 'string' ? body.app : null,
      version: typeof body.version === 'number' ? body.version : null,
      ms: Date.now() - started,
    }
  } catch (error) {
    return { alive: false, host, port, ok: false, app: null, version: null, error: errorText(error) }
  }
}

/** Bounded TCP connect probe (the LAN scan's cheap test). Resolves a boolean. */
function tcpProbe(host, port, timeoutMs = TCP_TIMEOUT_MS) {
  return new Promise((resolve) => {
    let settled = false
    const socket = new net.Socket()
    const finish = (alive) => {
      if (settled) return
      settled = true
      socket.destroy()
      resolve(alive)
    }
    socket.setTimeout(timeoutMs)
    socket.once('connect', () => finish(true))
    socket.once('timeout', () => finish(false))
    socket.once('error', () => finish(false))
    try {
      socket.connect(port, host)
    } catch {
      finish(false)
    }
  })
}

/** Probe one candidate; the returned row is the pane's device contract. */
async function probeDevice(host, port) {
  const ping = await bridgePing(host, port)
  return {
    host,
    port,
    alive: ping.alive && ping.ok,
    model: null,
    app: ping.app,
    version: ping.version,
    ms: ping.ms,
    error: ping.alive ? null : ping.error || 'no answer on /ping',
  }
}

/** Configured TV first, then a bounded /24 TCP sweep on the bridge port. */
async function discoverDevices(force, target) {
  const devices = []
  const candidates = []
  if (target) {
    const first = await probeDevice(target.host, target.port)
    if (first.alive) devices.push(first)
    const parts = target.host.split('.')
    if (parts.length === 4 && parts.every((part) => /^\d{1,3}$/.test(part))) {
      const base = `${parts[0]}.${parts[1]}.${parts[2]}`
      for (let last = 1; last <= 254; last += 1) {
        const host = `${base}.${last}`
        if (host !== target.host) candidates.push(host)
      }
    }
  }
  const started = Date.now()
  const probed = await Promise.all(
    candidates.map(async (host) => ({ host, alive: await tcpProbe(host, target.port) })),
  )
  const hits = probed.filter((row) => row.alive).map((row) => row.host)
  const swept = await Promise.all(hits.map((host) => probeDevice(host, target.port)))
  for (const device of swept) {
    if (device.alive) devices.push(device)
  }
  devices.sort((a, b) => {
    if (target && a.host === target.host) return -1
    if (target && b.host === target.host) return 1
    const toInt = (host) => host.split('.').reduce((acc, part) => acc * 256 + (Number(part) || 0), 0)
    return toInt(a.host) - toInt(b.host)
  })
  return {
    devices: devices.map((device) => ({
      host: device.host,
      port: device.port,
      alive: device.alive,
      model: device.model,
      app: device.app,
      version: device.version,
    })),
    scanned: {
      mode: target ? 'configured+sweep' : 'none',
      candidates: candidates.length,
      answered: hits.length,
      tookMs: Date.now() - started,
      cached: !force,
    },
  }
}

/** Small TTL cache so a pane refresh does not re-sweep the LAN every 2 s. */
const cache = { devices: null, devicesAt: 0, target: null, targetAt: 0 }

async function targetCached() {
  if (cache.target && Date.now() - cache.targetAt < TARGET_CACHE_MS) return cache.target
  const target = await readTarget()
  cache.target = target
  cache.targetAt = Date.now()
  return target
}

/** Read a JSON request body; returns null for malformed/oversized input. */
async function readJsonBody(req) {
  let size = 0
  const chunks = []
  try {
    for await (const chunk of req) {
      size += chunk.length
      if (size > MAX_BODY_BYTES) return null
      chunks.push(chunk)
    }
    const text = Buffer.concat(chunks).toString('utf8').trim()
    if (!text) return {}
    const parsed = JSON.parse(text)
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed : null
  } catch {
    return null
  }
}

function routePost(handler) {
  return async (req, res) => {
    if (req.method !== 'POST') {
      res.setHeader('allow', 'POST')
      return sendJson(res, 405, { ok: false, error: 'method not allowed' })
    }
    return handler(req, res)
  }
}

function routeGet(handler) {
  return async (req, res) => {
    if (req.method !== 'GET' && req.method !== 'HEAD') {
      res.setHeader('allow', 'GET')
      return sendJson(res, 405, { ok: false, error: 'method not allowed' })
    }
    return handler(req, res)
  }
}

/** Wrap a handler so a surprise exception still produces JSON. */
function guarded(handler) {
  return async (req, res) => {
    try {
      await handler(req, res)
    } catch (error) {
      if (!res.headersSent) sendJson(res, 500, { ok: false, error: errorText(error) })
      else res.destroy()
    }
  }
}

/**
 * GET /whale-chan/status
 * @returns daemon reachability (never the token), configured bridge target,
 *          live bridge /ping result, and the daemon's own TV snapshot.
 */
async function handleStatus(req, res) {
  const [token, target] = await Promise.all([readToken(), targetCached()])
  const health = await daemonJson('/health', {
    headers: token ? { 'x-whale-token': token } : {},
  })
  const bridge = target ? await bridgePing(target.host, target.port) : null
  sendJson(res, 200, {
    ok: true,
    repo: repoState(),
    daemon: {
      reachable: health.reachable && health.status === 200,
      url: DAEMON,
      status: health.status,
      sessionId: health.body && health.body.sessionId ? String(health.body.sessionId) : null,
      tv: health.body && health.body.tv && typeof health.body.tv === 'object' ? health.body.tv : null,
      error: health.reachable && health.status === 200 ? null : health.body.error || `http ${health.status}`,
    },
    token: { present: token.length > 0 },
    target,
    bridge,
    checkedAt: Date.now(),
  })
}

/**
 * GET /whale-chan/devices
 * @query fresh=1  bypass the 8 s sweep cache
 * @returns { devices: [{host,port,alive,model,app,version}], scanned }
 */
async function handleDevices(req, res) {
  const url = new URL(String(req.url || '/'), 'http://localhost')
  const force = url.searchParams.get('fresh') === '1'
  const target = await targetCached()
  if (!force && cache.devices && Date.now() - cache.devicesAt < DEVICE_CACHE_MS) {
    return sendJson(res, 200, {
      ok: true,
      ...cache.devices,
      scanned: { ...cache.devices.scanned, cached: true },
    })
  }
  const result = await discoverDevices(force, target)
  cache.devices = result
  cache.devicesAt = Date.now()
  sendJson(res, 200, { ok: true, ...result, scanned: { ...result.scanned, cached: false } })
}

/**
 * GET /whale-chan/pending
 * @returns { ok, pending: [{id,code,createdAt,ageSeconds}], daemon }
 *          Empty list (never an error) when the daemon is down.
 */
async function handlePending(req, res) {
  const token = await readToken()
  const result = await daemonJson('/pair/pending', {
    headers: token ? { 'x-whale-token': token } : {},
  })
  if (!result.reachable || result.status !== 200 || !Array.isArray(result.body.pending)) {
    return sendJson(res, 200, {
      ok: true,
      pending: [],
      now: Date.now(),
      daemon: false,
      error: result.body.error || `http ${result.status}`,
    })
  }
  sendJson(res, 200, {
    ok: true,
    pending: result.body.pending,
    now: Number(result.body.now) || Date.now(),
    daemon: true,
  })
}

/** POST /whale-chan/pair/approve {id} — approve a TV-initiated pairing from DSH. */
async function handleApprove(req, res) {
  const body = await readJsonBody(req)
  const id = body && typeof body.id === 'string' ? body.id.trim() : ''
  if (!id) return sendJson(res, 400, { ok: false, error: 'id required' })
  const token = await readToken()
  const result = await daemonJson('/pair/approve', {
    method: 'POST',
    headers: {
      accept: 'application/json',
      ...(token ? { 'x-whale-token': token } : {}),
    },
    body: { id },
  })
  if (result.reachable && result.body && result.body.ok === true) {
    return sendJson(res, 200, { ok: true, approved: true, id })
  }
  const expired = result.status === 404
  sendJson(res, expired ? 404 : 502, {
    ok: false,
    approved: false,
    error: expired ? 'expired' : result.body.error || `http ${result.status}`,
  })
}

/** POST /whale-chan/pair/deny {id} — dismiss a pending request. */
async function handleDeny(req, res) {
  const body = await readJsonBody(req)
  const id = body && typeof body.id === 'string' ? body.id.trim() : ''
  if (!id) return sendJson(res, 400, { ok: false, error: 'id required' })
  const token = await readToken()
  const result = await daemonJson('/pair/deny', {
    method: 'POST',
    headers: {
      accept: 'application/json',
      ...(token ? { 'x-whale-token': token } : {}),
    },
    body: { id },
  })
  if (result.reachable && result.body && result.body.ok === true) {
    return sendJson(res, 200, { ok: true, denied: true, id })
  }
  sendJson(res, result.status === 404 ? 404 : 502, {
    ok: false,
    denied: false,
    error: result.body.error || `http ${result.status}`,
  })
}

/** POST /whale-chan/pair/new — create a pairing session (code + QR for a phone). */
async function handlePairNew(req, res) {
  const result = await daemonJson('/pair/new')
  if (!result.reachable || result.status !== 200) {
    return sendJson(res, 502, { ok: false, error: result.body.error || `http ${result.status}` })
  }
  sendJson(res, 200, { ok: true, daemon: true, ...result.body })
}

/** GET /whale-chan/pair/status?id= — compatibility proxy for the daemon poll. */
async function handlePairStatus(req, res) {
  const url = new URL(String(req.url || '/'), 'http://localhost')
  const id = url.searchParams.get('id') || ''
  if (!id) return sendJson(res, 400, { ok: false, error: 'id required' })
  const result = await daemonJson('/pair/status?id=' + encodeURIComponent(id))
  if (!result.reachable) {
    return sendJson(res, 502, { ok: false, error: result.body.error || 'daemon unreachable' })
  }
  // The daemon's device config carries the LAN token; the browser half must
  // never receive it, so report only that a token was issued.
  const body = { ...result.body }
  if (body.config && typeof body.config === 'object') {
    const { token, ...rest } = body.config
    body.config = { ...rest, hasToken: typeof token === 'string' && token.length > 0 }
  }
  sendJson(res, result.status === 200 ? 200 : result.status, body)
}

/** The route table: path is exact, no trailing slash, every handler guarded. */
const routes = [
  { path: '/whale-chan/status', handler: routeGet(guarded(handleStatus)) },
  { path: '/whale-chan/devices', handler: routeGet(guarded(handleDevices)) },
  { path: '/whale-chan/pending', handler: routeGet(guarded(handlePending)) },
  { path: '/whale-chan/pair/approve', handler: routePost(guarded(handleApprove)) },
  { path: '/whale-chan/pair/deny', handler: routePost(guarded(handleDeny)) },
  { path: '/whale-chan/pair/new', handler: routePost(guarded(handlePairNew)) },
  { path: '/whale-chan/pair/status', handler: routeGet(guarded(handlePairStatus)) },
]

/**
 * Register the pane's same-origin routes.
 * @param ctx - cordis context with the `webServer` service.
 */
export function apply(ctx) {
  for (const route of routes) {
    ctx.effect(
      () => ctx.webServer.register({ kind: 'exact', path: route.path, handler: route.handler }),
      `whale-chan-ui: ${route.path}`,
    )
  }
}
