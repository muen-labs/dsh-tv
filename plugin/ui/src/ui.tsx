import * as React from 'react'

/**
 * The pane's small local kit. Everything here is inline styles on the host's
 * own `--dsw-*` tokens: no CSS imports, no theme of our own, so the pane is
 * legible in both the light and dark DSH themes and inherits the house shape
 * wherever the Settings shell puts it.
 */

/** Shared focus treatment: the house ring, not a browser default inside a modal. */
export function focusRing(active: boolean): React.CSSProperties {
  return active
    ? { outline: '2px solid var(--dsw-alias-brand-primary)', outlineOffset: 2 }
    : { outline: 'none' }
}

export const surface: React.CSSProperties = {
  background: 'var(--dsw-alias-bg-layer-3)',
  border: '1px solid var(--dsw-alias-border-l2)',
  borderRadius: 12,
}

export const nestedSurface: React.CSSProperties = {
  background: 'var(--dsw-alias-bg-layer-2)',
  border: '1px solid var(--dsw-alias-border-l3)',
  borderRadius: 10,
}

export function Card(props: { children?: React.ReactNode; style?: React.CSSProperties }): React.JSX.Element {
  return <div style={{ ...surface, padding: 16, ...props.style }}>{props.children}</div>
}

export function CardHeader(props: { title: React.ReactNode; hint?: React.ReactNode; trailing?: React.ReactNode }): React.JSX.Element {
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'baseline', gap: 8, marginBottom: 10 }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2, flex: '1 1 220px', minWidth: 0 }}>
        <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, lineHeight: '20px', color: 'var(--dsw-alias-label-primary)' }}>
          {props.title}
        </h3>
        {props.hint !== undefined ? (
          <p style={{ margin: 0, fontSize: 12, lineHeight: '18px', color: 'var(--dsw-alias-label-tertiary)' }}>{props.hint}</p>
        ) : null}
      </div>
      {props.trailing}
    </div>
  )
}

export function Muted(props: { children?: React.ReactNode; as?: 'p' | 'span' }): React.JSX.Element {
  const Tag = props.as === 'span' ? 'span' : 'p'
  return (
    <Tag style={{ margin: 0, fontSize: 12.5, lineHeight: '19px', color: 'var(--dsw-alias-label-tertiary)' }}>
      {props.children}
    </Tag>
  )
}

type Tone = 'ok' | 'warn' | 'error' | 'neutral'

const toneColor: Record<Tone, string> = {
  ok: 'var(--dsw-alias-state-success-primary)',
  warn: 'var(--dsw-alias-state-warn-primary)',
  error: 'var(--dsw-alias-state-error-primary)',
  neutral: 'var(--dsw-alias-label-tertiary)',
}

/** A status dot carries meaning together with the text next to it, never alone. */
export function Dot(props: { tone: Tone }): React.JSX.Element {
  return (
    <span
      aria-hidden="true"
      style={{
        width: 7,
        height: 7,
        borderRadius: 999,
        flex: 'none',
        display: 'inline-block',
        background: toneColor[props.tone],
      }}
    />
  )
}

export function Chip(props: { tone: Tone; children?: React.ReactNode }): React.JSX.Element {
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        height: 22,
        padding: '0 9px',
        borderRadius: 999,
        border: `1px solid color-mix(in srgb, ${toneColor[props.tone]} 38%, transparent)`,
        background: `color-mix(in srgb, ${toneColor[props.tone]} 12%, transparent)`,
        color: toneColor[props.tone],
        fontSize: 11.5,
        fontWeight: 600,
        lineHeight: '16px',
        whiteSpace: 'nowrap',
      }}
    >
      {props.children}
    </span>
  )
}

type ButtonVariant = 'primary' | 'secondary' | 'ghost'

function buttonStyle(variant: ButtonVariant): React.CSSProperties {
  if (variant === 'primary') {
    return {
      background: 'var(--dsw-alias-label-primary)',
      color: 'var(--dsw-alias-bg-layer-3)',
      border: '1px solid transparent',
    }
  }
  if (variant === 'secondary') {
    return {
      background: 'transparent',
      color: 'var(--dsw-alias-label-primary)',
      border: '1px solid var(--dsw-alias-border-l2)',
    }
  }
  return { background: 'transparent', color: 'var(--dsw-alias-label-secondary)', border: '1px solid transparent' }
}

export function Button(
  props: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant; small?: boolean },
): React.JSX.Element {
  const { variant = 'secondary', small = false, style, disabled, onFocus, onBlur, ...rest } = props
  const [focused, setFocused] = React.useState(false)
  return (
    <button
      {...rest}
      type="button"
      disabled={disabled}
      onFocus={(event) => {
        setFocused(true)
        onFocus?.(event)
      }}
      onBlur={(event) => {
        setFocused(false)
        onBlur?.(event)
      }}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 6,
        height: small ? 28 : 32,
        padding: small ? '0 10px' : '0 14px',
        borderRadius: 8,
        font: 'inherit',
        fontSize: 13,
        fontWeight: 500,
        lineHeight: 1,
        whiteSpace: 'nowrap',
        cursor: disabled ? 'default' : 'pointer',
        opacity: disabled ? 0.45 : 1,
        ...buttonStyle(variant),
        ...focusRing(focused),
        ...style,
      }}
    />
  )
}

/** The pairing code: monospace, tracked out like the TV screen shows it. */
export function Code(props: { children?: React.ReactNode }): React.JSX.Element {
  return (
    <code
      style={{
        display: 'inline-block',
        fontFamily: 'var(--ds-font-family-code)',
        fontSize: 20,
        fontWeight: 600,
        letterSpacing: '.2em',
        lineHeight: '26px',
        color: 'var(--dsw-alias-label-primary)',
        background: 'var(--dsw-alias-bg-module-platform)',
        border: '1px solid var(--dsw-alias-border-l2)',
        borderRadius: 8,
        padding: '3px 4px 3px 10px',
        whiteSpace: 'nowrap',
      }}
    >
      {props.children}
    </code>
  )
}

/** A one-line label/value pair used by the connection card. */
export function StateRow(props: { tone: Tone; label: React.ReactNode; value: React.ReactNode; detail?: React.ReactNode }): React.JSX.Element {
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '4px 8px', minWidth: 0 }}>
      <Dot tone={props.tone} />
      <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--dsw-alias-label-primary)' }}>{props.label}</span>
      <span style={{ fontSize: 13, color: 'var(--dsw-alias-label-secondary)' }}>{props.value}</span>
      {props.detail !== undefined ? (
        <span
          style={{
            fontSize: 12,
            color: 'var(--dsw-alias-label-tertiary)',
            fontFamily: 'var(--ds-font-family-code)',
            overflowWrap: 'anywhere',
            minWidth: 0,
          }}
        >
          {props.detail}
        </span>
      ) : null}
    </div>
  )
}

/** House callout for a state the person must act on. */
export function Callout(props: { tone?: 'info' | 'error'; title?: React.ReactNode; children?: React.ReactNode }): React.JSX.Element {
  const error = props.tone === 'error'
  return (
    <div
      role={error ? 'alert' : undefined}
      style={{
        ...nestedSurface,
        borderColor: error
          ? 'color-mix(in srgb, var(--dsw-alias-state-error-primary) 40%, transparent)'
          : 'var(--dsw-alias-border-l3)',
        background: error
          ? 'color-mix(in srgb, var(--dsw-alias-state-error-primary) 8%, var(--dsw-alias-bg-layer-3))'
          : 'var(--dsw-alias-bg-layer-2)',
        padding: '10px 12px',
        display: 'flex',
        flexDirection: 'column',
        gap: 4,
      }}
    >
      {props.title !== undefined ? (
        <strong style={{ fontSize: 13, fontWeight: 600, color: 'var(--dsw-alias-label-primary)' }}>{props.title}</strong>
      ) : null}
      {props.children}
    </div>
  )
}

/** The exact command a person can copy when the daemon is down. */
export function Command(props: { children?: React.ReactNode }): React.JSX.Element {
  return (
    <code
      style={{
        display: 'block',
        fontFamily: 'var(--ds-font-family-code)',
        fontSize: 12,
        lineHeight: '18px',
        color: 'var(--dsw-alias-label-secondary)',
        background: 'var(--dsw-alias-bg-layer-1)',
        border: '1px solid var(--dsw-alias-border-l2)',
        borderRadius: 6,
        padding: '6px 8px',
        overflowWrap: 'anywhere',
      }}
    >
      {props.children}
    </code>
  )
}
