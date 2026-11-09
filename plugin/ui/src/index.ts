import { WhaleTvSection, NS, en, zh } from './client'

export const inject = ['slots', 'locale']

export function apply(ctx: any): void {
  ctx.effect(() => ctx.locale.register(NS, { en, zh }), 'whale-chan-ui: dictionaries')
  ctx.slots.inject('settings.section', () =>
    ctx.slots.register(
      {
        name: 'settings.section',
        id: 'whale-tv',
        order: 100,
        label: () => 'Whale-chan TV',
        locale: NS,
      },
      WhaleTvSection,
    ),
  )
}

export type { WhaleTvSection as Component } from './client'
