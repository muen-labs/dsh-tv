import * as React from 'react'
import { Button, Callout, Card, CardHeader, Chip, Code, Command, Dot, Muted, StateRow, nestedSurface } from './ui'

export const NS = 'whale-tv'

/** English dictionary — the key source of truth. */
export const en = {
  nav: 'DeepSeek TV',
  title: 'DeepSeek TV',
  subtitle: 'Your Android TV, driven by DSH. Pair it once, then press the TV button and talk.',
  chipChecking: 'Checking connection',
  chipRouteError: 'Pane unavailable',
  chipDaemonDown: 'Daemon offline',
  chipBridgeUnset: 'No TV configured',
  chipBridgeDown: 'TV bridge offline',
  chipOk: 'Daemon and TV bridge online',
  sectionConnection: 'Connection',
  daemonLabel: 'Daemon',
  bridgeLabel: 'TV bridge',
  stateRunning: 'Running',
  stateNotRunning: 'Not running',
  stateAnswering: 'Answering',
  stateNoAnswer: 'No answer',
  stateNotConfigured: 'Not configured',
  tokenMissing: 'The daemon token was not found, so pairing cannot be approved from DSH.',
  sectionDevices: 'Android TVs on this network',
  devicesHint: 'The TV runs the DeepSeek TV bridge app. Choose the one DSH should drive.',
  scanning: 'Scanning this network for Android TVs…',
  scanningShort: 'Scanning…',
  scanAgain: 'Scan again',
  routeErrorTitle: 'The pane could not reach its host routes',
  routeErrorBody: 'The plugin host half is not answering. Reinstall it and restart DSH, then retry.',
  retry: 'Retry',
  daemonDownTitle: 'The DeepSeek TV daemon is not answering',
  daemonDownBody: 'Start it on the Mac from the repository, then retry:',
  startCommand: 'python3 host/whale_voice.py --serve --port 8766',
  noTvsTitle: 'No Android TVs answered',
  noTvsBody: 'Turn the TV on, open DeepSeek TV there, and scan again.',
  noTarget: 'No TV is configured yet: host/config.json has no bridge address. Pair the TV once from the TV first.',
  sectionPair: 'Pairing requests',
  pairHint: 'On the TV, open “Pair this TV with your Mac”. When the code appears here, confirm it matches the TV before approving.',
  pairPolling: 'Live · every 2s',
  pairPaused: 'Not live',
  pairEmpty: 'No pairing requests right now.',
  codeLabel: 'Pairing code',
  tvUnknown: 'Android TV',
  ageSuffix: 's ago',
  deviceFoundOne: 'TV found',
  deviceFoundMany: 'TVs found',
  requestWaitingOne: '1 pairing request waiting',
  requestWaitingMany: 'pairing requests waiting',
  approve: 'Approve TV',
  deny: 'Deny',
  approving: 'Approving…',
  approved: 'Approved. The TV has this Mac now and will finish pairing by itself.',
  denied: 'Request dismissed. The TV keeps waiting until its code expires.',
  approvalError: 'Could not approve that request. It may have expired — ask the TV to show a new code.',
} as const

export type Key = keyof typeof en

/** Simplified Chinese dictionary; typed so a missing key is a build error. */
export const zh: Record<Key, string> = {
  nav: 'DeepSeek TV',
  title: 'DeepSeek TV',
  subtitle: '用 DSH 操作的安卓电视。配对一次，之后按下电视按钮说话即可。',
  chipChecking: '正在检查连接',
  chipRouteError: '面板不可用',
  chipDaemonDown: '后台未运行',
  chipBridgeUnset: '未配置电视',
  chipBridgeDown: '电视桥未响应',
  chipOk: '后台与电视桥已连接',
  sectionConnection: '连接状态',
  daemonLabel: '后台',
  bridgeLabel: '电视桥',
  stateRunning: '运行中',
  stateNotRunning: '未运行',
  stateAnswering: '响应中',
  stateNoAnswer: '无响应',
  stateNotConfigured: '未配置',
  tokenMissing: '没有找到后台令牌，因此无法在 DSH 里批准配对。',
  sectionDevices: '此网络上的安卓电视',
  devicesHint: '电视上运行着 DeepSeek TV 桥应用。请选择要由 DSH 控制的电视。',
  scanning: '正在扫描网络中的安卓电视…',
  scanningShort: '扫描中…',
  scanAgain: '重新扫描',
  routeErrorTitle: '面板无法连接自己的后台接口',
  routeErrorBody: '插件的主机端没有响应。请重新安装并重启 DSH，然后重试。',
  retry: '重试',
  daemonDownTitle: 'DeepSeek TV 后台没有响应',
  daemonDownBody: '请在 Mac 上的仓库目录里启动它，然后重试：',
  startCommand: 'python3 host/whale_voice.py --serve --port 8766',
  noTvsTitle: '没有安卓电视响应',
  noTvsBody: '打开电视，并在电视上打开 DeepSeek TV，然后重新扫描。',
  noTarget: '还没有配置电视：host/config.json 里没有电视桥地址。请先在电视上完成一次配对。',
  sectionPair: '配对请求',
  pairHint: '在电视上打开“Pair this TV with your Mac”。这里出现验证码后，先确认与电视上的一致，再批准。',
  pairPolling: '实时 · 每 2 秒',
  pairPaused: '未实时',
  pairEmpty: '当前没有配对请求。',
  codeLabel: '配对码',
  tvUnknown: '安卓电视',
  ageSuffix: '秒前',
  deviceFoundOne: '台电视已找到',
  deviceFoundMany: '台电视已找到',
  requestWaitingOne: '1 个配对请求等待中',
  requestWaitingMany: '个配对请求等待中',
  approve: '批准电视',
  deny: '拒绝',
  approving: '正在批准…',
  approved: '已批准。电视现在已获得这台 Mac 的地址，会自动完成配对。',
  denied: '请求已忽略。电视会继续等待，直到验证码过期。',
  approvalError: '无法批准该请求，可能已经过期。请在电视上重新显示验证码。',
}

type Device = {
  host: string
  port: number
  alive: boolean
  model?: string | null
  app?: string | null
  version?: number | null
}

type PendingRequest = {
  id: string
  code: string
  createdAt: number
  ageSeconds: number
  host?: string | null
}

type DaemonState = {
  reachable: boolean
  url?: string
  status?: number
  sessionId?: string | null
  tv?: unknown
  error?: string | null
}

type BridgeState = {
  alive: boolean
  host: string
  port: number
  ok: boolean
  app?: string | null
  version?: number | null
  ms?: number
  error?: string | null
}

type Status = {
  ok?: boolean
  daemon: DaemonState
  token?: { present: boolean }
  target: { host: string; port: number } | null
  bridge: BridgeState | null
}

type Scanned = { mode?: string; candidates?: number; answered?: number; tookMs?: number; cached?: boolean }
type Phase = 'loading' | 'down' | 'error' | 'empty' | 'ready'
type Approval = { id: string; kind: 'approved' | 'denied' | 'error' }

/** Fixture seam for tools/preview.mjs: a phase the real network may not reach. */
export type Preview = {
  phase?: Phase
  status?: Status | null
  devices?: Device[]
  scanned?: Scanned | null
  pending?: PendingRequest[]
  pendingDaemon?: boolean
  approval?: Approval | null
  busyId?: string | null
  error?: string
}

type Props = { t?: (key: Key) => string; close?: () => void; preview?: Preview }

/** Read the host's bound translator; fall back to English, never to blank. */
function translatorOf(props: Props): (key: Key) => string {
  return (key) => (props && typeof props.t === 'function' ? props.t(key) : en[key] ?? key)
}

function ageText(entry: PendingRequest, t: (key: Key) => string): string {
  const fresh = Number.isFinite(entry.ageSeconds)
    ? entry.ageSeconds
    : Math.max(0, Math.round((Date.now() - entry.createdAt) / 1000))
  return `${Math.max(0, Math.round(fresh))}${t('ageSuffix')}`
}

function chipFor(status: Status | null, phase: Phase, t: (key: Key) => string): { tone: 'ok' | 'warn' | 'error' | 'neutral'; label: string } {
  if (phase === 'error') return { tone: 'error', label: t('chipRouteError') }
  if (status === null) return { tone: 'neutral', label: t('chipChecking') }
  if (!status.daemon || status.daemon.reachable !== true) return { tone: 'error', label: t('chipDaemonDown') }
  if (!status.target) return { tone: 'warn', label: t('chipBridgeUnset') }
  if (!status.bridge || status.bridge.alive !== true) return { tone: 'warn', label: t('chipBridgeDown') }
  return { tone: 'ok', label: t('chipOk') }
}

function DeviceRow(props: {
  device: Device
  active: boolean
  t: (key: Key) => string
  onSelect: () => void
  onKeyDown: (event: React.KeyboardEvent<HTMLButtonElement>) => void
  tabIndex: number
}): React.JSX.Element {
  const { device, active, t, onSelect, onKeyDown, tabIndex } = props
  const [focused, setFocused] = React.useState(false)
  const name = device.model || t('tvUnknown')
  const bridgeLine = device.app ? `${device.app}${device.version ? ` v${device.version}` : ''}` : ''
  return (
    <button
      type="button"
      id={`whale-tv-device-${device.host.replace(/\./g, '-')}`}
      role="radio"
      aria-checked={active}
      tabIndex={tabIndex}
      onClick={onSelect}
      onKeyDown={onKeyDown}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        width: '100%',
        boxSizing: 'border-box',
        padding: '10px 12px',
        textAlign: 'left',
        font: 'inherit',
        cursor: 'pointer',
        borderRadius: 10,
        border: `1px solid ${active ? 'var(--dsw-alias-brand-primary)' : 'var(--dsw-alias-border-l2)'}`,
        background: active ? 'var(--dsw-alias-bg-layer-2)' : 'transparent',
        outline: focused ? '2px solid var(--dsw-alias-brand-primary)' : 'none',
        outlineOffset: 2,
      }}
    >
      <Dot tone={device.alive ? 'ok' : 'neutral'} />
      <span style={{ display: 'flex', flexDirection: 'column', gap: 2, minWidth: 0, flex: '1 1 auto' }}>
        <span style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--dsw-alias-label-primary)', overflowWrap: 'anywhere' }}>
          {name}
        </span>
        <span style={{ fontSize: 12, color: 'var(--dsw-alias-label-tertiary)', overflowWrap: 'anywhere' }}>
          {device.host}:{device.port}
          {bridgeLine ? ` · ${bridgeLine}` : ''}
        </span>
      </span>
      <span
        aria-hidden="true"
        style={{
          width: 16,
          height: 16,
          flex: 'none',
          borderRadius: 999,
          border: `1px solid ${active ? 'var(--dsw-alias-brand-primary)' : 'var(--dsw-alias-border-l3)'}`,
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {active ? (
          <span style={{ width: 8, height: 8, borderRadius: 999, background: 'var(--dsw-alias-brand-primary)' }} />
        ) : null}
      </span>
    </button>
  )
}

/**
 * The DeepSeek TV Settings section.
 *
 * Phases are independent: the device list can be empty or unavailable while
 * the pairing-request card keeps working, because approving a TV-initiated
 * pairing does not need a LAN scan.
 */
export function WhaleTvSection(props: Props): React.JSX.Element {
  const t = translatorOf(props)
  const preview = props.preview
  const [phase, setPhase] = React.useState<Phase>(preview?.phase ?? 'loading')
  const [status, setStatus] = React.useState<Status | null>(preview?.status ?? null)
  const [devices, setDevices] = React.useState<Device[]>(preview?.devices ?? [])
  const [scanned, setScanned] = React.useState<Scanned | null>(preview?.scanned ?? null)
  const [selected, setSelected] = React.useState<string | null>(preview?.devices?.[0]?.host ?? null)
  const [pending, setPending] = React.useState<PendingRequest[]>(preview?.pending ?? [])
  const [pendingDaemon, setPendingDaemon] = React.useState<boolean>(preview?.pendingDaemon ?? true)
  const [approval, setApproval] = React.useState<Approval | null>(preview?.approval ?? null)
  const [busyId, setBusyId] = React.useState<string | null>(preview?.busyId ?? null)
  const [error, setError] = React.useState(preview?.error ?? '')
  const [scanning, setScanning] = React.useState(false)

  const load = React.useCallback(async (initial: boolean) => {
    if (initial) setPhase('loading')
    setScanning(true)
    setError('')
    try {
      const statusRes = await fetch('/whale-chan/status', { headers: { accept: 'application/json' } })
      const nextStatus = (await statusRes.json()) as Status
      if (!nextStatus || typeof nextStatus !== 'object') throw new Error('bad status response')
      setStatus(nextStatus)

      const pendingRes = await fetch('/whale-chan/pending', { headers: { accept: 'application/json' } })
      const pendingBody = await pendingRes.json()
      setPending(Array.isArray(pendingBody?.pending) ? (pendingBody.pending as PendingRequest[]) : [])
      setPendingDaemon(pendingBody?.daemon !== false)

      if (nextStatus.daemon?.reachable !== true) {
        setDevices([])
        setPhase('down')
        return
      }
      if (!nextStatus.target) {
        setDevices([])
        setPhase('empty')
        return
      }
      const deviceRes = await fetch('/whale-chan/devices?fresh=1', { headers: { accept: 'application/json' } })
      const deviceBody = await deviceRes.json()
      const list = Array.isArray(deviceBody?.devices) ? (deviceBody.devices as Device[]) : []
      setDevices(list)
      setScanned(deviceBody?.scanned ?? null)
      setSelected((previous) => (previous && list.some((device) => device.host === previous) ? previous : list[0]?.host ?? null))
      setPhase(list.length > 0 ? 'ready' : 'empty')
    } catch (cause) {
      setError(String((cause as Error)?.message || cause))
      setPhase('error')
    } finally {
      setScanning(false)
    }
  }, [])

  React.useEffect(() => {
    if (preview) return
    void load(true)
  }, [load, preview])

  // Poll the daemon's pending pairings while the pane is open.
  React.useEffect(() => {
    if (preview) return
    let cancelled = false
    const timer = setInterval(async () => {
      try {
        const res = await fetch('/whale-chan/pending', { headers: { accept: 'application/json' } })
        const body = await res.json()
        if (cancelled) return
        setPending(Array.isArray(body?.pending) ? (body.pending as PendingRequest[]) : [])
        setPendingDaemon(body?.daemon !== false)
      } catch {
        if (!cancelled) setPendingDaemon(false)
      }
    }, 2000)
    return () => {
      cancelled = true
      clearInterval(timer)
    }
  }, [preview])

  const act = React.useCallback(
    async (entry: PendingRequest, kind: 'approve' | 'deny') => {
      setBusyId(entry.id)
      setApproval(null)
      try {
        const res = await fetch(`/whale-chan/pair/${kind}`, {
          method: 'POST',
          headers: { accept: 'application/json', 'content-type': 'application/json' },
          body: JSON.stringify({ id: entry.id }),
        })
        const body = await res.json()
        if (body && body.ok === true) {
          setApproval({ id: entry.id, kind: kind === 'approve' ? 'approved' : 'denied' })
          setPending((previous) => previous.filter((item) => item.id !== entry.id))
        } else {
          setApproval({ id: entry.id, kind: 'error' })
          setError(String(body?.error || 'request failed'))
        }
      } catch (cause) {
        setApproval({ id: entry.id, kind: 'error' })
        setError(String((cause as Error)?.message || cause))
      } finally {
        setBusyId(null)
      }
    },
    [],
  )

  const chip = chipFor(status, phase, t)
  const daemonOk = status?.daemon?.reachable === true
  const daemonDetail = status?.daemon
    ? [status.daemon.url, status.daemon.reachable ? null : status.daemon.error].filter(Boolean).join(' · ')
    : undefined
  const bridgeOk = status?.bridge?.alive === true
  const bridgeValue = !status?.target
    ? t('stateNotConfigured')
    : bridgeOk
      ? t('stateAnswering')
      : t('stateNoAnswer')
  const bridgeDetail = status?.target
    ? `${status.target.host}:${status.target.port}${status.bridge?.app ? ` · ${status.bridge.app}${status.bridge.version ? ` v${status.bridge.version}` : ''}` : ''}`
    : undefined
  const approvalText = approval
    ? approval.kind === 'approved'
      ? t('approved')
      : approval.kind === 'denied'
        ? t('denied')
        : t('approvalError')
    : null

  const onDeviceKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>, index: number) => {
    const keys = ['ArrowDown', 'ArrowRight', 'ArrowUp', 'ArrowLeft', 'Home', 'End']
    if (!keys.includes(event.key)) return
    event.preventDefault()
    const last = devices.length - 1
    let next = index
    if (event.key === 'ArrowDown' || event.key === 'ArrowRight') next = index >= last ? 0 : index + 1
    if (event.key === 'ArrowUp' || event.key === 'ArrowLeft') next = index <= 0 ? last : index - 1
    if (event.key === 'Home') next = 0
    if (event.key === 'End') next = last
    const target = devices[next]
    if (target) {
      setSelected(target.host)
      const node = document.getElementById(`whale-tv-device-${target.host.replace(/\./g, '-')}`)
      if (node instanceof HTMLElement) node.focus()
    }
  }

  return (
    <section
      aria-labelledby="whale-tv-heading"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 14,
        width: '100%',
        maxWidth: 760,
        color: 'var(--dsw-alias-label-primary)',
      }}
    >
      <header style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
          <h2 id="whale-tv-heading" style={{ margin: 0, fontSize: 18, fontWeight: 600, lineHeight: '26px' }}>
            {t('title')}
          </h2>
          <Chip tone={chip.tone}>
            <Dot tone={chip.tone} />
            {chip.label}
          </Chip>
        </div>
        <Muted>{t('subtitle')}</Muted>
      </header>

      <Card>
        <CardHeader title={t('sectionConnection')} hint={status?.token?.present === false ? t('tokenMissing') : undefined} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <StateRow
            tone={daemonOk ? 'ok' : 'error'}
            label={t('daemonLabel')}
            value={daemonOk ? t('stateRunning') : t('stateNotRunning')}
            detail={daemonDetail}
          />
          <StateRow
            tone={bridgeOk ? 'ok' : status?.target ? 'warn' : 'neutral'}
            label={t('bridgeLabel')}
            value={bridgeValue}
            detail={bridgeDetail}
          />
        </div>
      </Card>

      <Card>
        <CardHeader
          title={t('sectionDevices')}
          hint={t('devicesHint')}
          trailing={
            <Button small onClick={() => void load(false)} disabled={scanning}>
              {scanning ? t('scanningShort') : t('scanAgain')}
            </Button>
          }
        />
        {phase === 'loading' ? (
          <p role="status" aria-live="polite" style={{ margin: 0, fontSize: 13, color: 'var(--dsw-alias-label-tertiary)' }}>
            {t('scanning')}
          </p>
        ) : null}

        {phase === 'error' ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <Callout tone="error" title={t('routeErrorTitle')}>
              <Muted>{error ? `${error} — ` : ''}{t('routeErrorBody')}</Muted>
            </Callout>
            <div>
              <Button onClick={() => void load(true)}>{t('retry')}</Button>
            </div>
          </div>
        ) : null}

        {phase === 'down' ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <Callout tone="error" title={t('daemonDownTitle')}>
              <Muted>{t('daemonDownBody')}</Muted>
              <Command>{t('startCommand')}</Command>
            </Callout>
            <div>
              <Button onClick={() => void load(true)}>{t('retry')}</Button>
            </div>
          </div>
        ) : null}

        {phase === 'empty' ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <strong style={{ fontSize: 13.5, fontWeight: 600 }}>{t('noTvsTitle')}</strong>
            <Muted>{t('noTvsBody')}</Muted>
            {status && !status.target ? <Muted>{t('noTarget')}</Muted> : null}
          </div>
        ) : null}

        {phase === 'ready' ? (
          <div role="radiogroup" aria-label={t('sectionDevices')} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {devices.map((device, index) => (
              <DeviceRow
                key={device.host}
                device={device}
                active={selected === device.host}
                t={t}
                onSelect={() => setSelected(device.host)}
                onKeyDown={(event) => onDeviceKeyDown(event, index)}
                tabIndex={selected === device.host ? 0 : -1}
              />
            ))}
            {scanned && typeof scanned.tookMs === 'number' ? (
              <span style={{ fontSize: 12, color: 'var(--dsw-alias-label-tertiary)' }}>
                {`${devices.length} ${devices.length === 1 ? t('deviceFoundOne') : t('deviceFoundMany')} · ${scanned.tookMs}ms`}
              </span>
            ) : null}
          </div>
        ) : null}
      </Card>

      <Card>
        <CardHeader
          title={t('sectionPair')}
          hint={t('pairHint')}
          trailing={
            <Chip tone={pendingDaemon ? 'ok' : 'warn'}>
              <Dot tone={pendingDaemon ? 'ok' : 'warn'} />
              {pendingDaemon ? t('pairPolling') : t('pairPaused')}
            </Chip>
          }
        />
        <div
          role="status"
          aria-live="polite"
          style={{
            marginBottom: 8,
            fontSize: 13,
            lineHeight: '19px',
            fontWeight: approvalText !== null ? 500 : 400,
            color: approval
              ? approval.kind === 'error'
                ? 'var(--dsw-alias-state-error-primary)'
                : 'var(--dsw-alias-state-success-primary)'
              : 'var(--dsw-alias-label-tertiary)',
          }}
        >
          {approvalText !== null
            ? approvalText
            : pending.length > 0
              ? pending.length === 1
                ? t('requestWaitingOne')
                : `${pending.length} ${t('requestWaitingMany')}`
              : t('pairEmpty')}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {pending.map((entry) => {
            const address = entry.host
              ? `${entry.host}${status?.target ? `:${status.target.port}` : ''}`
              : t('tvUnknown')
            const busy = busyId === entry.id
            return (
              <div
                key={entry.id}
                style={{ ...nestedSurface, padding: 12, display: 'flex', flexDirection: 'column', gap: 10 }}
              >
                <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '6px 10px' }}>
                  <span style={{ fontSize: 11, letterSpacing: '.08em', textTransform: 'uppercase', color: 'var(--dsw-alias-label-tertiary)' }}>
                    {t('codeLabel')}
                  </span>
                  <Code>{entry.code}</Code>
                  <span style={{ fontSize: 12.5, color: 'var(--dsw-alias-label-secondary)', overflowWrap: 'anywhere' }}>
                    {address}
                  </span>
                  <span style={{ fontSize: 12, color: 'var(--dsw-alias-label-tertiary)' }}>{ageText(entry, t)}</span>
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                  <Button
                    variant="primary"
                    aria-label={`${t('approve')} — ${t('codeLabel')} ${entry.code}`}
                    disabled={busyId !== null}
                    onClick={() => void act(entry, 'approve')}
                  >
                    {busy ? t('approving') : t('approve')}
                  </Button>
                  <Button
                    aria-label={`${t('deny')} — ${t('codeLabel')} ${entry.code}`}
                    disabled={busyId !== null}
                    onClick={() => void act(entry, 'deny')}
                  >
                    {t('deny')}
                  </Button>
                </div>
              </div>
            )
          })}
        </div>
      </Card>
    </section>
  )
}

export default WhaleTvSection
