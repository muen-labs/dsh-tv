# Contributing to DeepSeek TV Assistant

Thanks for wanting to build on this. It is an intentionally small, hackable
Android TV assistant: a single APK that exposes a LAN bridge + voice overlay,
a Mac-side daemon (DSH + SenseVoice), and an agent skill set that lets DSH drive
the TV.

## The shape of the project

```
android/tv-assistant/   single APK (no Gradle; aapt2/javac/d8/apksigner)
host/whale_voice.py     Mac daemon: /stt, /ask, /pair, /memory, /suggest
host/stt_worker.mjs     warm DSH SenseVoice STT worker
host/tv-apps.json       TV app catalog + per-app recipes
host/playbooks/         operational navigation playbooks (Stremio, TiviMate…)
host/tv_memory.py       local taste memory (SQLite)
host/suggest.py         proactive suggestions (web search + taste)
plugin/                 DSH host plugin + MCP tools + settings pane
docs/                   design system, mockups, app knowledge, personalisation
skills/                 agent skill(s) that ship with the repo
```

## Setup (Mac mini → onn 4K Pro)

1. **Java + Android SDK** — JDK 17 and `aapt2`, `d8`, `apksigner`, `zipalign`
   under `.tools/android-sdk` (see `android/tv-assistant/build.sh`).
2. **ADB** — enable developer mode on the TV, `adb connect <tv-ip>:5555`.
3. **Build + install**
   ```bash
   cd android/tv-assistant
   WHALE_TOKEN=$(cat ../../.auth/whale.token) bash build.sh
   adb install -r -g TVAssistant.apk
   ```
4. **Daemon** — run outside any sandbox:
   ```bash
   nohup /bin/zsh host/run-whale-daemon.sh > logs/whale-voice-daemon.log 2>&1 &
   ```
   The DSH child needs an unsandboxed parent (see `docs/VOICE-STT.md`).
5. **Tests / verification**
   ```bash
   python3 host/dshtv.py state
   python3 host/dshtv.py ui
   TOK=$(cat .auth/whale.token)
   curl -H "X-Whale-Token: $TOK" http://127.0.0.1:8766/health
   ```

## Where help is most useful

| Area | Why it matters |
| --- | --- |
| **Stremio stream selection** | Pick healthy Torrentio/yastream/debrid sources instead of the first card (current playback blocker: player exits with “Ow! That stings!”). |
| **Catalog-first navigation** | Reliably scan Home/Discover rows via `uiautomator` text, then fall back to search. |
| **Voice UX** | Streaming partial transcripts, barge-in, multi-turn “yes” without losing overlay state. |
| **App playbooks** | TiviMate M3U/EPG, Nuvio, CloudStream, OwnTV verification on real devices. |
| **DSH tools** | MCP `tv_*` tools for launch/key/text/ui/screenshot/search + memory. |
| **Proactivity** | Trigger policy, acceptance feedback, weekly digest. |

## Ground rules

- Everything local-first: taste memory stays in `host/tv-memory.db`; never commit
  `.auth/`, pairing tokens, or `.auth/tivimate-sources.json`.
- No hard-coded “Google Assistant” flows. Prefer the agent + `ui` + playbooks.
- Test on a real TV before claiming a UI change; include a screenshot/screen
  recording.
- Keep the Android app dependency-free (no AndroidX).
- PRs: one focused change, `docs/` updated, `git log` message in the imperative.
