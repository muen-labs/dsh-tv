# Voice STT (DSH SenseVoice)

The TV overlay streams 16 kHz mono WAV to the Mac daemon; the daemon transcribes
with **DSH's own SenseVoiceSmall ONNX model** via sherpa-onnx (same model/runtime
as DSH's speech-to-text plugin). mlx-whisper is only a last-resort fallback and
is not installed here.

## Engine

- Warm worker: `host/stt_worker.mjs` loads the model once, then transcribes
  line-by-line over stdio (`{"id":1,"wav":"..."}` → `{"id":1,"ok":true,"text":...}`).
- One-shot fallback: `host/dsh_stt.mjs` (spawns node per request).
- Node module resolution: sherpa-onnx-node lives in DSH's pnpm store
  (`~/.local/share/dsh-superagent-runtime/node_modules/.pnpm/node_modules`).
  The daemon injects this as `NODE_PATH` (`_node_path()`; override with
  `DSH_NODE_PATH`). Without it the engine silently fell back to a missing Whisper.

## Measured (Mac mini, base M-series)

| Path | First call | Warm call |
| --- | --- | --- |
| DSH SenseVoice one-shot | 0.60 s | 0.60 s |
| DSH SenseVoice warm worker | 0.52 s (load) | **0.05–0.08 s** |
| mlx-whisper base | not installed | — |

## Accuracy guardrails

- Near-silence gate (`rms < 90`) skips decode.
- SenseVoice emits one punctuation char on silence; text without alphanumerics
  becomes empty.
- App-name repair (`_correct_app_names`) maps common slips onto the installed
  apps: "OpenStreio" → "open Stremio", "nubio" → "Nuvio", "netflicks" →
  "Netflix", "tivimate" → "TiviMate".

## Daemon must run outside the agent sandbox

DSH's bash tool refuses to run when nested inside the agent's macOS sandbox
(`sandbox-exec: Operation not permitted`), so a daemon started from a tool call
cannot control the TV. Run it from a normal terminal/launchd context:

```bash
nohup /bin/zsh /Volumes/External SSD/iptv/dsh-tv/host/run-whale-daemon.sh \
  > logs/whale-voice-daemon.log 2>&1 &
```

(launchd could not read the external volume — EX_CONFIG — so use the wrapper from
a non-sandboxed shell. The wrapper exports PATH/DSH_HOME and starts the daemon.)

Verify:

```bash
TOK=$(cat .auth/whale.token)
curl -H "X-Whale-Token: $TOK" http://127.0.0.1:8766/health
curl -H "X-Whale-Token: $TOK" -H 'Content-Type: audio/wav' \
  --data-binary @/tmp/speech.wav http://127.0.0.1:8766/stt
```
