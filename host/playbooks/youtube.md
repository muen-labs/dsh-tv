# YouTube (TV) — playbook

Package `com.google.android.youtube.tv`
Role: video/search.

## Search
```
launch youtube
key up            # focus top bar
key right/left    # to the search icon
key ok
text "lofi"
key enter
```
Then `ui` results; OK plays. BACK returns. Voice search is available via the
Google Assistant button, but prefer typing for determinism.

## Notes
- DRM/long ads can black out captures; use `ui` to verify playback.
- Autoplay/next: `key next`; pause: `key playpause`.
