import { WhaleTvSection, NS, en, zh } from './client'

/** Services the client half needs: slot registration and locale dictionaries. */
export const inject = ['slots', 'locale']

/**
 * The TV glyph for the settings rail.
 *
 * The settings shell picks a section's nav icon from a host-owned id table
 * (`models`, `plugins`, …) and falls back to the settings gear for every other
 * id — the slot contract has no icon seat, so a third-party section cannot ask
 * for one. We therefore swap the gear for a TV outline on our own nav row after
 * the shell renders it (Lucide `tv`, 16px outline so it matches the host icons).
 */
const TV_ICON =
  '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" ' +
  'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
  '<rect x="2" y="7" width="20" height="14" rx="2.5"/><path d="m17 2-5 5-5-5"/></svg>'

/** Labels the section can appear under (both locale dictionaries use this). */
const LABELS = new Set([en.nav, zh.nav])

/**
 * Put the TV icon on our settings-rail button, and keep it there across the
 * shell's re-renders. Returns a disposer for the plugin effect.
 */
function installNavIcon(): () => void {
  const decorate = (): void => {
    const buttons = document.querySelectorAll<HTMLButtonElement>('nav button')
    buttons.forEach((button) => {
      const label = (button.textContent || '').trim()
      if (!LABELS.has(label)) return
      if (button.querySelector('[data-deepseek-tv-icon]')) return
      const hostIcon = button.querySelector('svg')
      const holder = document.createElement('span')
      holder.innerHTML = TV_ICON
      const icon = holder.firstElementChild as SVGElement | null
      if (!icon) return
      icon.setAttribute('data-deepseek-tv-icon', '')
      const hostClass = hostIcon?.getAttribute('class')
      if (hostClass) icon.setAttribute('class', hostClass)
      if (hostIcon) hostIcon.replaceWith(icon)
      else button.prepend(icon)
    })
  }

  decorate()
  const observer = new MutationObserver(() => decorate())
  observer.observe(document.body, { childList: true, subtree: true })
  return () => observer.disconnect()
}

/**
 * Contribute the DeepSeek TV Settings section.
 *
 * The registration mirrors the house sections: dictionaries first, then the
 * slot with `locale: NS`, so the host passes a bound `t` to the component and
 * the section's nav label follows the active language.
 * @param ctx - the browser plugin context.
 */
export function apply(ctx: any): void {
  ctx.effect(() => ctx.locale.register(NS, { en, zh }), 'deepseek-tv: dictionaries')
  const t = ctx.locale.bind(NS)
  ctx.slots.inject('settings.section', () =>
    ctx.slots.register(
      {
        name: 'settings.section',
        id: 'whale-tv',
        order: 100,
        label: () => t('nav'),
        locale: NS,
      },
      WhaleTvSection,
    ),
  )
  ctx.effect(() => installNavIcon(), 'deepseek-tv: nav icon')
}

export type { WhaleTvSection as Component } from './client'
