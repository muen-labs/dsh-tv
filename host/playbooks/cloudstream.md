# CloudStream — playbook

Package `com.lagradost.cloudstream3` · component `…/.ui.account.AccountSelectActivity`
Role: multi-provider streaming (movies/series/anime), provider extensions.

## Navigation
- Launch usually lands on **account selection**; pick a profile (or "Skip").
- Left sidebar/rail: Home, Search, Library, Downloads, Settings/Extensions.
- `ui` first — screen order changes between builds.

## Providers / repositories
1. Settings → **Extensions / Providers** (sometimes "Plugins").
2. Add a **repository URL** (community repo) if the built-in list is empty.
3. Install providers you want; enable/disable them in the same list.
4. Return Home → provider rows appear.

## Search
```
launch cloudstream
ui                         # dismiss account screen if present
key left / key up          # to Search
key ok
text "anime"
key enter
```
Pick a result → pick provider → pick server/quality → play.

## Notes
- Results need a provider installed; if empty, install a repository first.
- Subtitle/quality options appear after server selection.
- Long repository URLs are easier from the app's community list; confirm with ui.
