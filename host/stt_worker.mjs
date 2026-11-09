#!/usr/bin/env node
// Warm SenseVoice worker: loads the DSH speech-to-text model once, then
// transcribes WAV paths line-by-line over stdin/stdout (JSON per line).
//
// request : {"id": 1, "wav": "/tmp/x.wav"}
// response: {"id": 1, "ok": true, "text": "...", "ms": 42}
import { createRequire } from 'node:module';
import path from 'node:path';
import readline from 'node:readline';

function arg(name, fallback) {
  const i = process.argv.indexOf(name);
  return i >= 0 && i + 1 < process.argv.length ? process.argv[i + 1] : fallback;
}

const modelDir = arg('--model-dir',
  process.env.DSH_STT_MODEL_DIR ||
  `${process.env.HOME}/.dsh/speech-to-text/sensevoice/models/sensevoice-onnx`);
const language = arg('--language', process.env.DSH_STT_LANGUAGE || 'auto');

let sherpa;
try {
  const require = createRequire(import.meta.url);
  sherpa = require('sherpa-onnx-node');
} catch (e) {
  console.log(JSON.stringify({ ready: false, error: `sherpa-onnx-node: ${e.message}` }));
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
  console.log(JSON.stringify({ ready: false, error: `model: ${e.message}` }));
  process.exit(3);
}

console.log(JSON.stringify({ ready: true, model: modelDir }));

const rl = readline.createInterface({ input: process.stdin });
rl.on('line', (line) => {
  line = line.trim();
  if (!line) return;
  let req;
  try {
    req = JSON.parse(line);
  } catch {
    console.log(JSON.stringify({ id: null, ok: false, error: 'bad json' }));
    return;
  }
  const started = Date.now();
  try {
    const wave = sherpa.readWave(req.wav);
    const stream = recognizer.createStream();
    stream.acceptWaveform({ samples: wave.samples, sampleRate: wave.sampleRate });
    recognizer.decode(stream);
    const result = recognizer.getResult(stream);
    console.log(JSON.stringify({
      id: req.id, ok: true, text: (result.text || '').trim(),
      ms: Date.now() - started,
    }));
  } catch (e) {
    console.log(JSON.stringify({ id: req.id, ok: false, error: String(e.message || e) }));
  }
});
