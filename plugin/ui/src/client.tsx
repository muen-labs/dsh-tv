import * as React from 'react'
import {
  Alert, AlertDescription, AlertTitle, Badge, Button, Card, CardContent, CardDescription,
  CardHeader, CardTitle, Input, Separator, evaTheme,
} from './ui'

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
type Preview = { phase?: 'loading' | 'error' | 'empty' | 'ready'; devices?: Device[]; pair?: PairInfo | null; pairState?: 'idle' | 'pending' | 'approved'; error?: string }

function translatorOf(props: { t?: (key: Key) => string }) {
  return (key: Key) => (props && typeof props.t === 'function' ? props.t(key) : en[key] ?? key)
}

function DeviceRow(props: { device: Device; active: boolean; label: string; onSelect: () => void }) {
  const { device, active, label, onSelect } = props
  return (
    <button
      role="radio"
      aria-checked={active}
      onClick={onSelect}
      style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12,
        width: '100%', textAlign: 'left', cursor: 'pointer', font: 'inherit',
        background: active ? 'var(--secondary)' : 'transparent',
        border: '1px solid ' + (active ? 'var(--ring)' : 'var(--border)'),
        borderRadius: 'var(--radius)', padding: '10px 12px', color: 'var(--foreground)',
      }}
    >
      <span style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <strong style={{ fontSize: 13 }}>{device.label || device.model || label}</strong>
        <span style={{ color: 'var(--muted-foreground)', fontSize: 12 }}>
          {device.host}:{device.port}
        </span>
      </span>
      {active && <span aria-hidden="true" style={{ width: 8, height: 8, borderRadius: 999, background: 'var(--ring)' }} />}
    </button>
  )
}

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
        /* keep waiting */
      }
    }, 1500)
    return () => clearInterval(timer)
  }, [pair, pairState, preview])

  return (
    <section style={{ ...evaTheme, display: 'flex', flexDirection: 'column', gap: 12, padding: 4, background: 'transparent', color: 'var(--foreground)' }}>
      <header style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <h2 style={{ margin: 0, fontSize: 16, fontWeight: 600, letterSpacing: '-.01em' }}>{t('title')}</h2>
        <p style={{ margin: 0, color: 'var(--muted-foreground)', fontSize: 12.5 }}>{t('subtitle')}</p>
        <div style={{ marginTop: 2 }}>
          <Badge variant={phase === 'error' ? 'destructive' : 'success'}>{phase === 'error' ? t('stopped') : t('running')}</Badge>
        </div>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>{t('sectionTvs')}</CardTitle>
          <CardDescription>{phase === 'ready' ? `${devices.length} found` : ''}</CardDescription>
        </CardHeader>
        <CardContent style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {phase === 'loading' && (
            <p style={{ margin: 0, color: 'var(--muted-foreground)', fontSize: 13 }} aria-live="polite">{t('scanning')}</p>
          )}

          {phase === 'error' && (
            <Alert variant="destructive">
              <AlertTitle>{t('daemonDown')}</AlertTitle>
              <AlertDescription>
                {error ? error + ' — ' : ''}{t('daemonDownHint')}
              </AlertDescription>
            </Alert>
          )}

          {phase === 'empty' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <p style={{ margin: 0, fontSize: 13 }}>{t('noTvs')}</p>
              <p style={{ margin: 0, color: 'var(--muted-foreground)', fontSize: 12.5 }}>{t('noTvsHint')}</p>
            </div>
          )}

          {phase === 'ready' && (
            <div role="radiogroup" aria-label={t('sectionTvs')} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {devices.map((device) => (
                <DeviceRow
                  key={device.host}
                  device={device}
                  active={selected === device.host}
                  label={t('tvUnknown')}
                  onSelect={() => setSelected(device.host)}
                />
              ))}
            </div>
          )}

          {(phase === 'ready' || phase === 'empty') && (
            <Button variant="outline" size="sm" onClick={() => void scan()}>{t('scanAgain')}</Button>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t('sectionPair')}</CardTitle>
          <CardDescription>{t('qrHint')}</CardDescription>
        </CardHeader>
        <CardContent style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <Button onClick={() => void generate()} disabled={!selected}>{t('generateQr')}</Button>

          {pair && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 14, alignItems: 'flex-start' }}>
              {pair.qr ? (
                <img
                  src={'data:image/png;base64,' + pair.qr}
                  alt={t('generateQr')}
                  width={190}
                  height={190}
                  style={{ background: '#fff', borderRadius: 8, padding: 8 }}
                />
              ) : (
                <code style={{ fontSize: 12, wordBreak: 'break-all', color: 'var(--muted-foreground)' }}>{pair.url}</code>
              )}
              <div style={{ flex: '1 1 180px', minWidth: 160, display: 'flex', flexDirection: 'column', gap: 8 }}>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                  <span style={{ fontSize: 11, letterSpacing: '.12em', textTransform: 'uppercase', color: 'var(--muted-foreground)' }}>{t('codeLabel')}</span>
                  <strong style={{ fontFamily: 'ui-monospace, monospace', fontSize: 22, letterSpacing: '.22em' }}>{pair.code}</strong>
                </div>
                <a href={pair.url} style={{ fontSize: 12, color: 'var(--ring)', wordBreak: 'break-all' }}>{pair.url}</a>
                <Separator />
                <p style={{ margin: 0, fontSize: 12.5 }} aria-live="polite">
                  {pairState === 'approved' ? t('approved') : t('waiting')}
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </section>
  )
}

export default WhaleTvSection
