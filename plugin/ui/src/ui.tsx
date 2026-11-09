import * as React from 'react'

/** shadcn/ui primitives, themed with Eva Design System dark tokens. */
export const evaTheme: React.CSSProperties = {
  // Eva dark theme (UI Kitten dark.json) mapped to shadcn semantic names.
  ['--background' as string]: '#101426',
  ['--foreground' as string]: '#FFFFFF',
  ['--card' as string]: '#1A2138',
  ['--card-foreground' as string]: '#FFFFFF',
  ['--popover' as string]: '#222B45',
  ['--primary' as string]: '#3366FF',
  ['--primary-foreground' as string]: '#FFFFFF',
  ['--secondary' as string]: '#222B45',
  ['--secondary-foreground' as string]: '#FFFFFF',
  ['--muted' as string]: '#151A30',
  ['--muted-foreground' as string]: '#8F9BB3',
  ['--destructive' as string]: '#FF3D71',
  ['--success' as string]: '#00E096',
  ['--warning' as string]: '#FFAA00',
  ['--border' as string]: '#2E3A59',
  ['--input' as string]: '#2E3A59',
  ['--ring' as string]: '#598BFF',
  ['--radius' as string]: '8px',
  color: 'var(--foreground)',
  background: 'var(--background)',
}

export function cn(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(' ')
}

type ButtonVariant = 'default' | 'secondary' | 'outline' | 'ghost' | 'destructive'
type ButtonSize = 'sm' | 'default' | 'lg'

const buttonBase: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: 8,
  borderRadius: 'var(--radius)',
  border: '1px solid transparent',
  font: 'inherit',
  fontWeight: 500,
  lineHeight: 1,
  cursor: 'pointer',
  transition: 'background-color .15s ease, box-shadow .15s ease, border-color .15s ease',
  whiteSpace: 'nowrap',
  outline: 'none',
}

const buttonVariants: Record<ButtonVariant, React.CSSProperties> = {
  default: { background: 'var(--primary)', color: 'var(--primary-foreground)', borderColor: 'var(--primary)' },
  secondary: { background: 'var(--secondary)', color: 'var(--secondary-foreground)', borderColor: 'var(--border)' },
  outline: { background: 'transparent', color: 'var(--foreground)', borderColor: 'var(--border)' },
  ghost: { background: 'transparent', color: 'var(--foreground)', borderColor: 'transparent' },
  destructive: { background: 'var(--destructive)', color: 'var(--primary-foreground)', borderColor: 'var(--destructive)' },
}

const buttonSizes: Record<ButtonSize, React.CSSProperties> = {
  sm: { height: 32, padding: '0 12px', fontSize: 13 },
  default: { height: 38, padding: '0 16px', fontSize: 14 },
  lg: { height: 44, padding: '0 22px', fontSize: 15 },
}

export function Button(
  props: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant; size?: ButtonSize },
): React.JSX.Element {
  const { variant = 'default', size = 'default', style, onFocus, onBlur, ...rest } = props
  const [focus, setFocus] = React.useState(false)
  return (
    <button
      {...rest}
      onFocus={(event) => { setFocus(true); onFocus?.(event) }}
      onBlur={(event) => { setFocus(false); onBlur?.(event) }}
      style={{
        ...buttonBase,
        ...buttonVariants[variant],
        ...buttonSizes[size],
        ...(rest.disabled ? { opacity: 0.5, cursor: 'not-allowed' } : null),
        ...(focus ? { boxShadow: '0 0 0 2px var(--background), 0 0 0 4px var(--ring)' } : null),
        ...style,
      }}
    />
  )
}

export function Card(props: React.HTMLAttributes<HTMLDivElement>): React.JSX.Element {
  return (
    <div
      {...props}
      style={{
        background: 'var(--card)',
        color: 'var(--card-foreground)',
        border: '1px solid var(--border)',
        borderRadius: 12,
        ...props.style,
      }}
    />
  )
}

export function CardHeader(props: React.HTMLAttributes<HTMLDivElement>): React.JSX.Element {
  return <div {...props} style={{ padding: '16px 16px 0', display: 'flex', flexDirection: 'column', gap: 4, ...props.style }} />
}

export function CardTitle(props: React.HTMLAttributes<HTMLHeadingElement>): React.JSX.Element {
  return <h3 {...props} style={{ margin: 0, fontSize: 14, fontWeight: 600, letterSpacing: '-.01em', ...props.style }} />
}

export function CardDescription(props: React.HTMLAttributes<HTMLParagraphElement>): React.JSX.Element {
  return <p {...props} style={{ margin: 0, fontSize: 12.5, color: 'var(--muted-foreground)', lineHeight: 1.45, ...props.style }} />
}

export function CardContent(props: React.HTMLAttributes<HTMLDivElement>): React.JSX.Element {
  return <div {...props} style={{ padding: 16, ...props.style }} />
}

export function Badge(
  props: React.HTMLAttributes<HTMLSpanElement> & { variant?: 'default' | 'secondary' | 'outline' | 'success' | 'destructive' },
): React.JSX.Element {
  const { variant = 'secondary', style, ...rest } = props
  const variants: Record<string, React.CSSProperties> = {
    default: { background: 'var(--primary)', color: 'var(--primary-foreground)', borderColor: 'var(--primary)' },
    secondary: { background: 'var(--secondary)', color: 'var(--secondary-foreground)', borderColor: 'var(--border)' },
    outline: { background: 'transparent', color: 'var(--foreground)', borderColor: 'var(--border)' },
    success: { background: 'color-mix(in srgb, var(--success) 16%, transparent)', color: 'var(--success)', borderColor: 'color-mix(in srgb, var(--success) 40%, transparent)' },
    destructive: { background: 'color-mix(in srgb, var(--destructive) 16%, transparent)', color: 'var(--destructive)', borderColor: 'color-mix(in srgb, var(--destructive) 40%, transparent)' },
  }
  return (
    <span
      {...rest}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 6, height: 22, padding: '0 8px',
        borderRadius: 999, border: '1px solid', fontSize: 11, fontWeight: 600,
        letterSpacing: '.02em', whiteSpace: 'nowrap', ...variants[variant], ...style,
      }}
    />
  )
}

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>): React.JSX.Element {
  const { style, ...rest } = props
  const [focus, setFocus] = React.useState(false)
  return (
    <input
      {...rest}
      onFocus={(event) => { setFocus(true); rest.onFocus?.(event) }}
      onBlur={(event) => { setFocus(false); rest.onBlur?.(event) }}
      style={{
        height: 38, width: '100%', padding: '0 12px', fontSize: 14, font: 'inherit',
        background: 'var(--muted)', color: 'var(--foreground)',
        border: '1px solid var(--input)', borderRadius: 'var(--radius)',
        boxShadow: focus ? '0 0 0 2px var(--ring)' : 'none',
        outline: 'none', ...style,
      }}
    />
  )
}

export function Separator(props: React.HTMLAttributes<HTMLDivElement>): React.JSX.Element {
  return <div role="separator" {...props} style={{ height: 1, background: 'var(--border)', ...props.style }} />
}

export function Alert(
  props: React.HTMLAttributes<HTMLDivElement> & { variant?: 'default' | 'destructive' },
): React.JSX.Element {
  const { variant = 'default', style, ...rest } = props
  return (
    <div
      role="alert"
      {...rest}
      style={{
        border: '1px solid',
        borderColor: variant === 'destructive' ? 'color-mix(in srgb, var(--destructive) 45%, transparent)' : 'var(--border)',
        background: variant === 'destructive' ? 'color-mix(in srgb, var(--destructive) 10%, transparent)' : 'color-mix(in srgb, var(--muted) 70%, transparent)',
        borderRadius: 10, padding: '10px 12px', fontSize: 12.5, lineHeight: 1.45, ...style,
      }}
    />
  )
}

export function AlertTitle(props: React.HTMLAttributes<HTMLHeadingElement>): React.JSX.Element {
  return <h4 {...props} style={{ margin: '0 0 4px', fontSize: 13, fontWeight: 600, ...props.style }} />
}

export function AlertDescription(props: React.HTMLAttributes<HTMLParagraphElement>): React.JSX.Element {
  return <p {...props} style={{ margin: 0, color: 'var(--muted-foreground)', ...props.style }} />
}
