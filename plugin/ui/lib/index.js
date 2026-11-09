// Host half: same-origin routes the settings pane can call without CORS or
// exposing the daemon token to the browser. Proxies to host/whale_voice.py.
const DAEMON = process.env.WHALE_DAEMON_URL || 'http://127.0.0.1:8766';
const TIMEOUT_MS = 30000;

export const inject = ['webServer'];

function sendJson(res, status, payload) {
  res.statusCode = status;
  res.setHeader('content-type', 'application/json; charset=utf-8');
  res.setHeader('cache-control', 'no-store');
  res.end(JSON.stringify(payload));
}

async function daemon(path, init = {}) {
  const res = await fetch(DAEMON + path, {
    ...init,
    signal: AbortSignal.timeout(TIMEOUT_MS),
  });
  const text = await res.text();
  let body;
  try { body = JSON.parse(text); } catch { body = { ok: false, error: text.slice(0, 200) }; }
  return { status: res.status, body };
}

export function apply(ctx) {
  const routes = [
    {
      path: '/whale-chan/status',
      run: async (req, res) => {
        try {
          const r = await daemon('/ui/status');
          sendJson(res, 200, r.body);
        } catch (err) {
          sendJson(res, 200, { ok: false, daemon: false, error: String(err && err.message || err) });
        }
      },
    },
    {
      path: '/whale-chan/devices',
      run: async (req, res) => {
        try {
          const r = await daemon('/discover');
          sendJson(res, 200, r.body);
        } catch (err) {
          sendJson(res, 200, { ok: false, devices: [], error: String(err && err.message || err) });
        }
      },
    },
    {
      path: '/whale-chan/pair/new',
      run: async (req, res) => {
        try {
          const r = await daemon('/pair/new', { method: 'POST' });
          sendJson(res, 200, r.body);
        } catch (err) {
          sendJson(res, 200, { ok: false, error: String(err && err.message || err) });
        }
      },
    },
    {
      path: '/whale-chan/pair/status',
      run: async (req, res) => {
        const id = new URL(String(req.url), 'http://localhost').searchParams.get('id') || '';
        try {
          const r = await daemon('/pair/status?id=' + encodeURIComponent(id));
          sendJson(res, 200, r.body);
        } catch (err) {
          sendJson(res, 200, { ok: false, error: String(err && err.message || err) });
        }
      },
    },
  ];
  for (const route of routes) {
    ctx.effect(() => ctx.webServer.register({
      kind: 'exact',
      path: route.path,
      handler: route.run,
    }), `whale-chan: ${route.path}`);
  }
}
