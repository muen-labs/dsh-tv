# Third-party notices

## Character artwork

The animated pet uses the WebM animations from
**[1tryout/dsh-whale-pixel-pet](https://github.com/1tryout/dsh-whale-pixel-pet)**
(MIT). Six animations are converted to transparent animated WebP by
`tools/make-pet-assets.sh`; the converted files in `android/whale-app/res/raw/`
are derivatives of that artwork. The character is © its original author; the
MIT licence of that repository covers the project, and any artwork terms of the
original author continue to apply. Do not relicense the artwork as your own.

An earlier design used the sprites from
**[Er1c0v0/dsh-whale-pet](https://github.com/Er1c0v0/dsh-whale-pet)** — character
art © Er1c0v0, licensed **CC BY 4.0**. If you switch back to those assets,
keep the attribution.

Credit is rendered on the TV overlay (`android/whale-app/res/values/strings.xml`)
and bundled in `res/raw/attribution.txt`.

## Speech-to-text

`host/dsh_stt.mjs` runs the **SenseVoiceSmall** ONNX model through
**sherpa-onnx** (Apache-2.0), using the model files that DeepSeek Harness
already caches under `~/.dsh/speech-to-text/sensevoice/models`. The optional
Whisper fallback uses [mlx-whisper](https://github.com/ml-explore/mlx-examples)
and `mlx-community/whisper-base.en-mlx`.

## Other

- The DeepSeek Harness plugin itself is not bundled; the companion reads its
  `dsh` CLI and its SenseVoice cache.
- The Disney+ button shim is an original stub; it contains no Disney code,
  marks, or assets.


## App icon — DeepSeek Harness Whale Girl

- Source: <https://github.com/fornarwhal/deepseek-whale-girl-icon>
- Files: `docs/ui-assets/app-icon*.png` derived from `whale-girl-transparent.png`
- Characters: 上善无形 (OC「溟月」), DeepSeek elements by ZipZipPipe, restoration by QYQCAMIAO
- License: **CC BY-NC-SA 4.0** (attribution, non-commercial, share-alike)

This icon is used in the UI mockup and as the proposed app icon. It is **not
MIT-compatible** and must not be redistributed in the MIT-licensed APK/release
without permission from the rights holders. A project-owned or permissively
licensed icon should be used for release builds until then.
