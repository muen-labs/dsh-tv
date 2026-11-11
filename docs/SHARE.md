# Sharing on Reddit (copy/paste)

Links to use:

- Repo: <https://github.com/muen-labs/dsh-tv>
- Download: <https://github.com/muen-labs/dsh-tv/releases/latest>
Two cuts, because the first frame decides which sub it works in:

- **r/DeepSeek · r/LocalLLaMA** — [`docs/demo-short.mp4`](demo-short.mp4) (1.5 MB, 13.8 s):
  opens on the source pick, drops the 1 s buffering gap, ends on the episode playing with the
  scrubber visible. Poster: [`demo-poster.jpg`](demo-poster.jpg)
- **r/AndroidTV** — [`docs/demo-launch.mp4`](demo-launch.mp4) (0.9 MB, 8.5 s): the assistant on
  the launcher announcing *"Opening Nuvio — a sideloaded app Google Assistant cannot launch"*,
  then Nuvio's home with content. Poster: [`demo-launch-poster.jpg`](demo-launch-poster.jpg)
  - The last 3 s are a **still with a slow push-in** ([`demo-launch-payoff.jpg`](demo-launch-payoff.jpg)),
    not a capture: `screenrecord` returns a 0-byte file for Nuvio's surface, so a launched app
    can't be recorded as video on this box. Screenshots work fine. Say so if asked rather than
    implying the whole clip is live.
  - TiviMate (`ar.tvplayer.tv`) **launches correctly** but has no playlist on this box, so it
    opens to a black screen — not a usable demo subject until one is added. Nuvio was chosen
    because it is also sideloaded and actually renders.
- Full flow if someone asks: [`docs/demo.mp4`](demo.mp4) (2.9 MB, 34 s),
  [`docs/demo.gif`](demo.gif) (2.0 MB)
- UI gallery: <https://github.com/muen-labs/dsh-tv/blob/main/docs/ui-gallery.html>

## Post title options

1. **I turned an Android TV box into a voice terminal for DeepSeek Harness —
   press one remote button, talk, the agent drives the TV**
2. **Whale-chan: an Android TV assistant for DeepSeek Harness (one APK, QR
   pairing, local STT, no cloud audio)**
3. **DeepSeek TV Assistant — a voice-controlled Android TV bridge for DSH
   (open source, MIT)**

## Post body

> I built **DeepSeek TV Assistant** — it turns an Android TV / Google TV box
> into a voice terminal for [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness).
>
> Press the Disney+ button (or open the tile), talk, and DSH on my Mac drives
> the TV: it launches apps, moves the D-pad, types, searches, reads the screen.
> Replies come back through an animated whale-girl pet and TTS.
>
> - **One APK** contains the TV bridge (accessibility key injection + launch +
>   screenshots) and the assistant UI.
> - **QR pairing** — no IP or token typed with a remote. The TV shows a code, a
>   phone (or the DSH settings pane) approves it.
> - **Audio never leaves the LAN**: SenseVoice STT runs on the host, only text
>   goes to the model.
> - **DSH does the thinking** in one persistent voice session; the TV is the
>   mic, screen and remote.
> - Works with Google Assistant kept intact: the mic button stays Google's, the
>   Disney+ button becomes the assistant (optional shim).
> - Also a small DSH plugin: Settings → **DeepSeek TV** shows the daemon and TV
>   bridge, finds TVs on the LAN, and approves pairing requests in the GUI.
>
> **What the demo shows:** I ask *“Suggest an anime that is trending.”* It
> researches AniList, shows the pick in the assistant's FOR YOU card, opens
> Stremio, searches, opens the currently-airing season, picks a stream and plays
> it on the TV.
>
> It's not a standalone IPTV app — you need a Mac/Linux host on the same LAN
> running DSH (credentialed) plus the APK on the TV.
>
> Demo GIF: <https://github.com/muen-labs/dsh-tv/blob/main/docs/demo.gif>
> Repo (MIT, build from source or grab the release APK):
> <https://github.com/muen-labs/dsh-tv>
> Everything I could test is in the repo: real 1920×1080 screenshots of every
> screen, a browser UI gallery, and CI that builds the APK on every push.
>
> Known gaps (issues open): Stremio catalog/search matching + stream health for
> the demo playback leg, a broader Android TV test matrix, and some work on the
> reusable agent skill. Feedback welcome, especially from people with other TV
> boxes.

## Where to post

- **r/AndroidTV** — primary; the "turn a TV into an agent terminal" angle fits.
- **r/DeepSeek** / **r/LocalLLaMA** — DSH + local STT angle; lead with the two
  repos and the no-cloud-audio point.
- **r/googleTV**, **r/homelab**, **r/selfhosted** — secondary; mention the
  LAN-only design and that it needs a host machine.
- **r/onntv** (if active) — the boxes used for testing.

## Tips

- Attach the GIF or a short screen recording as the post media; Reddit surfaces
  posts with a video/image much better than a bare repo link.
- Mention up front that it is **not an IPTV player** — just an assistant/remote
  bridge — to avoid the usual comments.
- Ask for the model of people's boxes; a test-matrix issue is open and real
  reports help.
