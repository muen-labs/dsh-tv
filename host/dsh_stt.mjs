#!/usr/bin/env node
// Transcribe a 16 kHz mono WAV with the same SenseVoiceSmall ONNX model and
// sherpa-onnx runtime that DSH's own speech-to-text plugin uses.
// Prints one JSON line: {ok, text} or {ok:false, error}.
import { createRequire } from 'node:module';
import path from 'node:path';

const require = createRequire(import.meta.url);
const sherpa = require('sherpa-onnx-node');

function arg(name, fallback) {
  const i = process.argv.indexOf(name);
  return i >= 0 && i + 1 < process.argv.length ? process.argv[i + 1] : fallback;
}

const wav = arg('--wav');
const modelDir = arg('--model-dir', `${process.env.HOME}/.dsh/speech-to-text/sensevoice/models/sensevoice-onnx`);
const language = arg('--language', process.env.DSH_STT_LANGUAGE || 'auto');
if (!wav) {
  console.log(JSON.stringify({ ok: false, error: '--wav required' }));
  process.exit(2);
}

let recognizer;
try {
  recognizer = new sherpa.OfflineRecognizer({
    featConfig: { sampleRate: 16000, featureDim: 80 },
    modelConfig: {
      senseVoice: {
        model: path.join(modelDir, 'model.int8.onnx'),
        language,
        useInverseTextNormalization: 1,
      },
      tokens: path.join(modelDir, 'tokens.txt'),
      numThreads: Number(arg('--threads', '2')),
      provider: 'cpu',
      debug: 0,
    },
  });
} catch (e) {
  console.log(JSON.stringify({ ok: false, error: String((e && e.message) || e) }));
  process.exit(1);
}

try {
  const wave = sherpa.readWave(wav);
  const stream = recognizer.createStream();
  stream.acceptWaveform({ samples: wave.samples, sampleRate: wave.sampleRate });
  recognizer.decode(stream);
  const result = recognizer.getResult(stream);
  console.log(JSON.stringify({ ok: true, text: (result.text || '').trim(), language, sampleRate: wave.sampleRate }));
} catch (e) {
  console.log(JSON.stringify({ ok: false, error: String((e && e.message) || e) }));
  process.exit(1);
}
