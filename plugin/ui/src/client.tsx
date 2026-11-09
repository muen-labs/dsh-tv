import * as React from 'react'

export const NS = 'whale-tv'

export const en = {
  nav: 'Whale-chan TV',
  title: 'Whale-chan TV',
  subtitle: 'Android TV assistant — press the TV button, talk, and DSH drives the TV.',
  sectionTvs: 'Choose a TV on your network',
  sectionPair: 'Pair this TV',
  scanning: 'Scanning your network for Android TVs…',
  scanAgain: 'Scan again',
  daemonDown: 'The Whale-chan daemon is not answering.',
  daemonDownHint: 'Start it on the Mac: python3 host/whale_voice.py --serve — then scan again.',
  noTvs: 'No TVs found on this network.',
  noTvsHint: 'Turn the TV on, open Whale-chan there, then scan again.',
  running: 'Daemon running',
  stopped: 'Daemon not running',
  generateQr: 'Generate pairing QR code',
  waiting: 'Waiting for approval — scan the QR with your phone and tap Approve.',
  approved: 'Paired. The TV now has this Mac.',
  qrHint: 'On the TV, open “Pair this TV with Whale-chan”, then scan this code.',
  codeLabel: 'Code',
  urlLabel: 'Or open',
  tvUnknown: 'Android TV',
  pairFailed: 'Could not create a pairing code.',
} as const

export const zh = {
  nav: '鲸娘电视',
  title: '鲸娘电视',
  subtitle: '安卓电视助手 — 按下电视按钮说话，DSH 操作电视。',
  sectionTvs: '选择网络上的电视',
  sectionPair: '配对此电视',
  scanning: '正在扫描网络中的安卓电视…',
  scanAgain: '重新扫描',
  daemonDown: '鲸娘后台没有响应。',
  daemonDownHint: '先在 Mac 上启动：python3 host/whale_voice.py --serve，然后重新扫描。',
  noTvs: '此网络未发现电视。',
  noTvsHint: '打开电视并在上面打开鲸娘，然后重新扫描。',
  running: '后台运行中',
  stopped: '后台未运行',
  generateQr: '生成配对二维码',
  waiting: '等待批准 — 用手机扫描二维码并点击批准。',
  approved: '已配对，电视已获得这台 Mac 的地址。',
  qrHint: '在电视上打开“Pair this TV with Whale-chan”，然后扫描此二维码。',
  codeLabel: '验证码',
  urlLabel: '或打开',
  tvUnknown: '安卓电视',
  pairFailed: '无法生成配对码。',
} as const

type Key = keyof typeof en
type Device = { host: string; port: number; model?: string; label?: string }
type PairInfo = { id: string; code: string; qr?: string | null; url: string }

function translatorOf(props: { t?: (key: Key) => string }) {
  return (key: Key) => (props && typeof props.t === 'function' ? props.t(key) : en[key] ?? key)
}

const T = (name: string) => `var(--dsw-alias-${name})`

const card: React.CSSProperties = {
  background: T('bg-layer-2'),
  border: `1px solid ${T('border-l3')}`,
  borderRadius: 12,
  padding: 14,
}

const row = (active: boolean): React.CSSProperties => ({
  display: 'flex',
  flexWrap: 'wrap',
  alignItems: 'center',
  justifyContent: 'space-between',
  gap: 8,
  width: '100%',
  textAlign: 'left',
  cursor: 'pointer',
  background: active ? T('bg-layer-3') : 'transparent',
  border: `1px solid ${active ? T('brand-primary') : T('border-l2')}`,
  borderRadius: 10,
  padding: '10px 12px',
  color: T('label-primary'),
})

const button: React.CSSProperties = {
  background: T('button-primary-fill'),
  color: T('label-primary-foreground'),
  border: 'none',
  borderRadius: 8,
  padding: '8px 14px',
  cursor: 'pointer',
  fontSize: 13,
}

const ghost: React.CSSProperties = {
  ...button,
  background: 'transparent',
  border: `1px solid ${T('border-l2')}`,
  color: T('label-primary'),
}

type Preview = { phase?: 'loading' | 'error' | 'empty' | 'ready'; devices?: Device[]; pair?: PairInfo | null; pairState?: 'idle' | 'pending' | 'approved'; error?: string }

export function WhaleTvSection(props: { t?: (key: Key) => string; preview?: Preview }) {
  const t = translatorOf(props)
  const preview = props.preview
  const [phase, setPhase] = React.useState<'loading' | 'error' | 'empty' | 'ready'>(preview?.phase ?? 'loading')
  const [devices, setDevices] = React.useState<Device[]>(preview?.devices ?? [])
  const [selected, setSelected] = React.useState<string | null>(preview?.devices?.[0]?.host ?? null)
  const [pair, setPair] = React.useState<PairInfo | null>(preview?.pair ?? null)
  const [pairState, setPairState] = React.useState<'idle' | 'pending' | 'approved'>(preview?.pairState ?? 'idle')
  const [error, setError] = React.useState(preview?.error ?? '')

  const scan = React.useCallback(async () => {
    setPhase('loading')
    setError('')
    try {
      const [status, found] = await Promise.all([
        fetch('/whale-chan/status').then((r) => r.json()),
        fetch('/whale-chan/devices').then((r) => r.json()),
      ])
      if (status && status.daemon === false) {
        setError(String(status.error || ''))
        setPhase('error')
        return
      }
      const list: Device[] = Array.isArray(found.devices) ? found.devices : []
      setDevices(list)
      setSelected((prev) => (prev && list.some((d) => d.host === prev) ? prev : list[0]?.host ?? null))
      setPhase(list.length > 0 ? 'ready' : 'empty')
    } catch (err) {
      setError(String((err as Error)?.message || err))
      setPhase('error')
    }
  }, [])

  React.useEffect(() => {
    if (preview) return
    void scan()
  }, [scan, preview])

  const generate = React.useCallback(async () => {
    setPair(null)
    setPairState('idle')
    try {
      const info = await fetch('/whale-chan/pair/new', { method: 'POST' }).then((r) => r.json())
      if (!info || info.ok === false) {
        setError(String(info?.error || t('pairFailed')))
        return
      }
      setPair(info as PairInfo)
      setPairState('pending')
    } catch (err) {
      setError(String((err as Error)?.message || err))
    }
  }, [t])

  React.useEffect(() => {
    if (preview) return
    if (pairState !== 'pending' || !pair) return
    const timer = setInterval(async () => {
      try {
        const state = await fetch('/whale-chan/pair/status?id=' + encodeURIComponent(pair.id)).then((r) => r.json())
        if (state && state.approved) setPairState('approved')
      } catch {
        /* keep waiting; the daemon may be starting */
      }
    }, 1500)
    return () => clearInterval(timer)
  }, [pair, pairState, preview])

  const statusLabel = phase === 'error' ? t('stopped') : t('running')
  const statusColor = phase === 'error' ? T('label-error') : T('brand-primary')

  return (
    <section style={{ display: 'flex', flexDirection: 'column', gap: 14, padding: 4, color: T('label-primary') }}>
      <header>
        <h2 style={{ margin: 0, fontSize: 16 }}>{t('title')}</h2>
        <p style={{ margin: '4px 0 0', color: T('label-caption'), fontSize: 12 }}>{t('subtitle')}</p>
        <p style={{ margin: '6px 0 0', color: statusColor, fontSize: 12 }} aria-live="polite">
          ● {statusLabel}
        </p>
      </header>

      <div style={card}>
        <h3 style={{ margin: '0 0 8px', fontSize: 13, color: T('label-caption') }}>{t('sectionTvs')}</h3>

        {phase === 'loading' && (
          <p style={{ margin: 0, color: T('label-caption'), fontSize: 13 }} aria-live="polite">{t('scanning')}</p>
        )}

        {phase === 'error' && (
          <div role="alert">
            <p style={{ margin: 0, color: T('label-error'), fontSize: 13 }}>{t('daemonDown')}</p>
            <p style={{ margin: '4px 0 10px', color: T('label-caption'), fontSize: 12 }}>
              {error ? error + ' — ' : ''}{t('daemonDownHint')}
            </p>
            <button style={ghost} onClick={() => void scan()}>{t('scanAgain')}</button>
          </div>
        )}

        {phase === 'empty' && (
          <div>
            <p style={{ margin: 0, fontSize: 13 }}>{t('noTvs')}</p>
            <p style={{ margin: '4px 0 10px', color: T('label-caption'), fontSize: 12 }}>{t('noTvsHint')}</p>
            <button style={ghost} onClick={() => void scan()}>{t('scanAgain')}</button>
          </div>
        )}

        {phase === 'ready' && (
          <>
            <div role="radiogroup" aria-label={t('sectionTvs')} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {devices.map((device) => {
                const active = selected === device.host
                return (
                  <button
                    key={device.host}
                    role="radio"
                    aria-checked={active}
                    style={row(active)}
                    onClick={() => setSelected(device.host)}
                  >
                    <span style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      <strong style={{ fontSize: 13 }}>{device.label || device.model || t('tvUnknown')}</strong>
                      <span style={{ color: T('label-caption'), fontSize: 12 }}>{device.host}:{device.port}</span>
                    </span>
                    {active && <span aria-hidden="true" style={{ color: T('brand-primary') }}>●</span>}
                  </button>
                )
              })}
            </div>
            <div style={{ marginTop: 10 }}>
              <button style={ghost} onClick={() => void scan()}>{t('scanAgain')}</button>
            </div>
          </>
        )}
      </div>

      <div style={card}>
        <h3 style={{ margin: '0 0 8px', fontSize: 13, color: T('label-caption') }}>{t('sectionPair')}</h3>
        <button style={button} onClick={() => void generate()} disabled={!selected}>
          {t('generateQr')}
        </button>
        {error && pair === null && <p style={{ margin: '8px 0 0', color: T('label-error'), fontSize: 12 }}>{error}</p>}

        {pair && (
          <div style={{ marginTop: 12, display: 'flex', flexWrap: 'wrap', gap: 14, alignItems: 'flex-start' }}>
            {pair.qr ? (
              <img
                src={'data:image/png;base64,' + pair.qr}
                alt={t('generateQr')}
                width={190}
                height={190}
                style={{ background: '#fff', borderRadius: 8, padding: 8 }}
              />
            ) : (
              <code style={{ fontSize: 12, wordBreak: 'break-all', color: T('label-caption') }}>{pair.url}</code>
            )}
            <div style={{ flex: '1 1 200px', minWidth: 180 }}>
              <p style={{ margin: 0, fontSize: 12, color: T('label-caption') }}>{t('qrHint')}</p>
              <p style={{ margin: '8px 0 0', fontSize: 13 }}>
                {t('codeLabel')}: <strong style={{ letterSpacing: 2 }}>{pair.code}</strong>
              </p>
              <p style={{ margin: '4px 0 0', fontSize: 12, color: T('label-caption'), wordBreak: 'break-all' }}>
                {t('urlLabel')} <a href={pair.url} style={{ color: T('brand-primary') }}>{pair.url}</a>
              </p>
              <p style={{ margin: '8px 0 0', fontSize: 12 }} aria-live="polite">
                {pairState === 'approved' ? t('approved') : t('waiting')}
              </p>
            </div>
          </div>
        )}
      </div>
    </section>
  )
}

export default WhaleTvSection
