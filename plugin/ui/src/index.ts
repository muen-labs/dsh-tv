import { WhaleTvSection, NS, en, zh } from './client'

/** Services the client half needs: slot registration and locale dictionaries. */
export const inject = ['slots', 'locale']

/**
 * Contribute the Whale-chan TV Settings section.
 *
 * The registration mirrors the house sections: dictionaries first, then the
 * slot with `locale: NS`, so the host passes a bound `t` to the component and
 * the section's nav label follows the active language.
 * @param ctx - the browser plugin context.
 */
export function apply(ctx: any): void {
  ctx.effect(() => ctx.locale.register(NS, { en, zh }), 'whale-chan-ui: dictionaries')
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
}

export type { WhaleTvSection as Component } from './client'
