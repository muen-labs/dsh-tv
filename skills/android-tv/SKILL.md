---
name: android-tv
description: Build, install, and tune native Android TV apps (APKs) and voice-assistant overlays for the onn. 4K Pro / Google TV — 10-foot UI, D-pad focus, transparent overlays, icons/banners, and the build→install→screenshot verification loop. Use whenever the user asks to work on an Android TV app, fix TV UI/focus, add or polish an overlay, make TV icons, or debug TV input/launcher behaviour.
whenToUse: The user says Android TV / Google TV / onn / Fire TV–style box / TV app / APK on the TV / D-pad focus / TV overlay / Leanback banner / "looks pixelated on the TV" / "home button doesn't work" / screenshot or install on the TV.
---

# Android TV app craft (onn. 4K Pro, Android 14)

This workspace builds and ships **DeepSeek TV Assistant** (`com.jp.dshtv`), a
single APK that is both a LAN bridge and the Whale-chan voice overlay. The rules
below are the ones that cost time while getting it to look and feel right.

## Layout

| What | Where |
| --- | --- |
| Working APK source | `.tools/tv-assistant` (build here, install from here) |
| Repo copy (commit this) | `dsh-tv/android/tv-assistant` |
| Repo root | `dsh-tv/` (`github.com/thuyqpham/dsh-tv`) |
| Android SDK / JDK | `.tools/android-sdk`, `.tools/jdk` |
| ADB | `.tools/platform-tools/adb -s 192.168.4.58:5555` |
| Host voice daemon | `.tools`-independent: `host/whale_voice.py --serve` on `:8766` |
| Design reference | `dsh-tv/DESIGN.md`, `dsh-tv/docs/ui-mockup.html` |

No Gradle. `build.sh` runs aapt2 → javac → d8 → zipalign → apksigner.

```bash
cd .tools/tv-assistant
WHALE_TOKEN=$(cat ../../.auth/whale.token) bash build.sh
adb install -r -g TVAssistant.apk
adb exec-out screencap -p > /tmp/tv.png     # then read the image
```

Always run the full loop: **build → install → launch the screen → screenshot →
look at the pixels**. Do not claim a UI change without a capture.

## 10-foot UI rules

- Controls ≥ 56dp tall; one primary action per card; 20px card radius.
- **Focus is the whole UX.** Every D-pad target is `focusable`, has a visible
  2dp accent ring (+ 1.03 scale where it helps), and is explicitly focused when
  a screen/overlay opens (`requestFocus()` inside `post(...)` after layout).
- Focus the action the user most likely presses next. In the voice overlay that
  is the in-composer **send** while listening, and the mic ("ask again") after a
  reply.
- Status is always **word + dot**, never colour alone. Destructive actions get
  the red treatment (Stop service, X); primary CTAs are tinted, secondaries are
  dark bordered pills.
- Keep generous side gutters; content should not run edge-to-edge at 16:9.
- Persist stateful surfaces: do **not** auto-dismiss an assistant reply. Close
  only on explicit X/Back or when the user issues the next command.
- Overlay layout that works: 64dp round controls *above the composer*,
  right-aligned with it (not pinned to viewport corners), a send control inside
  the bubble, transcript ~20sp, reply ~24sp.

## Transparent voice overlay

- Activity theme: `windowIsTranslucent`, transparent background, no dim; a
  full-screen gradient scrim (`session_scrim.xml`) plus a frosted bubble gives
  contrast without touching the app behind.
- This box has **no window blur support** (`ro.surface_flinger` has no blur
  props; `SurfaceFlinger backgroundBlurRadius=0`). `FLAG_BLUR_BEHIND` +
  `setBlurBehindRadius()` is still worth requesting for other devices, but the
  gradient scrim is the real fallback. Never depend on blur for legibility.
- Animated pet/whale art: animated WebP (`res/raw`), decoded with
  `ImageDecoder` + `AnimatedImageDrawable` (API 28+) so alpha works. VP9-alpha
  WebM decoders on Android drop the alpha channel — don't use them at runtime.
- **Pixelation = upscaling.** Match the on-screen size to the asset: a 440px
  animation should render at ~200–260dp at TV density 2 (i.e. 400–520px), not
  380dp. Shrink the art before regenerating higher-res assets.
- Persistence + controls: X closes, mic re-listens in place, send commits the
  current capture; OK is also wired to commit while listening; Back closes.

## Icons and banners

- Launcher icon: 512×512 PNG (`ic_launcher.png`); launcher label short
  (currently "DeepSeek TV").
- Leanback banner: 320×180 PNG with name legible at couch distance
  (`banner.png`); a white tile + brand mark is fine for dark launchers.
- Android TV launchers differ in what they show (icon vs banner vs app card).
  **Projectivy caches app cards/icons** — a reinstall may not refresh the dock.
  Force-stop the launcher, reboot, or use a fresh composite for mockups.
- The current icon is a white tile with the DeepSeek whale + lowercase `tv`
  (Poppins Medium, `#4D6BFF`); keep `docs/ui-assets/icon-preview.png` in sync.

## Assistant / bridge integration

- `MainActivity` = bridge control panel, `PairingActivity` = QR pairing,
  `WhaleActivity` = launcher fallback overlay, `WhaleSessionService` =
  `VoiceInteractionService` session (`WhaleSession` + `WhaleUi`).
- Voice flow: `MicCapture` (AudioRecord + VAD, retries 3×) → daemon `/stt`
  (SenseVoice) → daemon `/ask` (DSH headless) → bubble + TTS. OK commits early;
  Back cancels.
- QA without speaking: `am start -n com.jp.dshtv/.WhaleActivity --ez demo true`
  renders a completed exchange (transcript + reply + celebrating pet).
- Bridge server is plain HTTP on `:8765`; the app needs
  `android:usesCleartextTraffic="true"`. Never commit `.tools/tv-assistant/res/values/config.xml`
  (generated token) or `.auth/`.

## Input / launcher pitfalls

- **HOME to Google TV:** HOME role should be
  `com.google.android.apps.tv.launcherx`; check `cmd role get-role-holders
  android.app.role.HOME`. Projectivy can be default only when the stock launcher
  is disabled, and `com.google.android.tungsten.setupwraith` may become the
  fallback home — restore the stock launcher immediately if that happens.
- **HOME doing the wrong thing:** a remapper can hijack it. Check accessibility
  services with filter-key capability (`tvQuickActions`, Projector OSD). In
  tvQuickActions: Mappings → Button HOME → delete the action. Re-enable the
  service afterwards; HDMI remaps often apply only to physical key presses, so
  test with the remote, not just `input keyevent`.
- Physical keys vs adb: `input keyevent 3/4/19/20/21/22/23` is reliable for
  navigation; use `getevent -lt /dev/input/event6` (Onn-Remote Keyboard) when
  mapping a physical button.
- Mic HAL can wedge (AudioRecord status -32, digital silence) after heavy
  Assistant/voice churn — a reboot clears it; the app retries start and gates on
  RMS. Katniss (Google Assistant) can also hold the mic briefly.

## Build & code gotchas

- No AndroidX: use plain `Activity`, `ImageView`, selectors, `Handler`.
- Selector drawables implement button variants/focus rings; `state_focused` is
  what TV users see, so it must be obvious.
- Custom view classes from `resources` must be fully qualified; system prefixes
  the package only for bare `.Class` on framework components.
- Don't collide CSS/XML ids with device-mock classes (a `.laptop`/`.tv` styling
  collision silently absolutely-positioned a chip).
- `postDelayed` auto-close hooks are easy to leave behind: delete reply/error
  `scheduleClose(...)` when the product wants persistence.
- Keep the repo `android/tv-assistant` copy synced after AOSP changes, then
  commit in `dsh-tv/`.

## Verification checklist

1. APK builds with no warnings that matter.
2. Install succeeds; label/icon checked (`aapt2 dump badging`).
3. Launch the specific screen and capture it; check focus ring placement.
4. Exercise with `input keyevent` (send / ask again / close / back / home).
5. Check the *physics*: readable at 1080p from ~3 m; nothing clipped at edges;
   controls not in the viewport corner unless intentional.
6. Sync to `dsh-tv/android/tv-assistant`, update `docs/screenshots`, commit and
   push.
