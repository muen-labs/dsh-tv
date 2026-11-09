package com.jp.dshtv;

import android.content.Context;
import android.media.AudioFormat;
import android.media.AudioRecord;
import android.media.MediaRecorder;
import android.media.audiofx.AcousticEchoCanceler;
import android.media.audiofx.AutomaticGainControl;
import android.media.audiofx.NoiseSuppressor;

import android.util.Log;

import java.io.ByteArrayOutputStream;

/**
 * Records a short utterance from the TV's built-in mics with a simple
 * energy-based end-of-speech detector. The far-field array is quiet, so AGC and
 * noise suppression are attached when the platform offers them, and the WAV is
 * normalised again on the Mac before transcription.
 */
public final class MicCapture {

    public interface Callback {
        void onDone(byte[] wav, boolean heardSpeech);
        void onError(String message);
    }

    private static final int SR = 16000;
    private static final int FRAME = 320;            // 20 ms mono 16-bit
    private static final int FRAME_BYTES = FRAME * 2;
    private static final int MAX_MS = 12000;
    private static final int NO_SPEECH_MS = 7000;
    private static final int TAIL_FRAMES = 45;       // ~900 ms of silence ends it
    private static final int MIN_SPEECH_FRAMES = 3;

    private volatile boolean running;
    private volatile boolean finishRequested;
    private Thread thread;
    private AudioRecord recorder;

    public void start(final Callback cb) {
        stop();
        running = true;
        finishRequested = false;
        thread = new Thread(new Runnable() {
            @Override
            public void run() {
                capture(cb);
            }
        }, "whale-mic");
        thread.start();
    }

    /** End the current utterance now and deliver what was captured (OK button). */
    public void finishNow() {
        finishRequested = true;
    }

    public void stop() {
        running = false;
        AudioRecord r = recorder;
        recorder = null;
        if (r != null) {
            try {
                r.stop();
            } catch (Throwable ignored) {
            }
            try {
                r.release();
            } catch (Throwable ignored) {
            }
        }
        Thread t = thread;
        thread = null;
        if (t != null) {
            try {
                t.join(600);
            } catch (InterruptedException ignored) {
                Thread.currentThread().interrupt();
            }
        }
    }

    private void capture(Callback cb) {
        for (int attempt = 0; attempt < 3 && running; attempt++) {
            try {
                if (attemptCapture(cb, attempt)) {
                    return;
                }
                Thread.sleep(350);
            } catch (InterruptedException ignored) {
                Thread.currentThread().interrupt();
                return;
            }
        }
        if (running) {
            cb.onError("microphone unavailable");
        }
    }

    /** @return true when the utterance finished (success), false to retry. */
    private boolean attemptCapture(Callback cb, int attempt) {
        AudioRecord rec = null;
        try {
            int min = AudioRecord.getMinBufferSize(SR, AudioFormat.CHANNEL_IN_MONO,
                    AudioFormat.ENCODING_PCM_16BIT);
            int bufBytes = Math.max(min * 3, 6400);
            rec = new AudioRecord(MediaRecorder.AudioSource.VOICE_RECOGNITION, SR,
                    AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT, bufBytes);
            if (rec.getState() != AudioRecord.STATE_INITIALIZED) {
                rec.release();
                Log.i("WhaleMic", "attempt " + attempt + ": init failed");
                return false;
            }
            recorder = rec;
            enableProcessing(rec.getAudioSessionId());
            rec.startRecording();
            if (rec.getRecordingState() != AudioRecord.RECORDSTATE_RECORDING) {
                Log.i("WhaleMic", "attempt " + attempt + ": not recording after start, retrying");
                try {
                    rec.release();
                } catch (Throwable ignored) {
                }
                recorder = null;
                return false;
            }
            Log.i("WhaleMic", "started sr=" + SR + " src=VOICE_RECOGNITION");

            byte[] buf = new byte[FRAME_BYTES];
            ByteArrayOutputStream pcm = new ByteArrayOutputStream(SR * 2 * 8);
            long started = System.currentTimeMillis();
            double floor = -1;
            int speechFrames = 0;
            double peak = 0;
            int silenceRun = 0;
            boolean speech = false;

            while (running) {
                int n = rec.read(buf, 0, FRAME_BYTES);
                if (n <= 0) {
                    Log.i("WhaleMic", "attempt " + attempt + ": read " + n + ", retrying");
                    try {
                        rec.stop();
                    } catch (Throwable ignored) {
                    }
                    try {
                        rec.release();
                    } catch (Throwable ignored) {
                    }
                    recorder = null;
                    return false;
                }
                pcm.write(buf, 0, n);
                double rms = rms(buf, n);
                if (rms > peak) peak = rms;
                if (floor < 0) {
                    floor = rms;
                } else if (!speech) {
                    floor = 0.95 * floor + 0.05 * Math.min(rms, floor * 3 + 1);
                }
                double threshold = Math.max(150.0, floor * 2.0);
                if (rms > threshold) {
                    speechFrames++;
                    silenceRun = 0;
                } else if (speechFrames > 0) {
                    silenceRun++;
                }
                if (speechFrames >= MIN_SPEECH_FRAMES) {
                    speech = true;
                }
                long elapsed = System.currentTimeMillis() - started;
                if (speech && silenceRun >= TAIL_FRAMES) {
                    Log.i("WhaleMic", "endpoint speech frames=" + speechFrames + " floor=" + (int) floor);
                    break;
                }
                if (finishRequested) {
                    Log.i("WhaleMic", "commit requested: speech=" + speech + " frames=" + speechFrames);
                    break;
                }
                if (!speech && elapsed > NO_SPEECH_MS) {
                    Log.i("WhaleMic", "no speech after " + elapsed + "ms floor=" + (int) floor + " peak=" + (int) peak);
                    break;
                }
                if (elapsed > MAX_MS) {
                    break;
                }
            }
            try {
                rec.stop();
            } catch (Throwable ignored) {
            }
            rec.release();
            recorder = null;
            Log.i("WhaleMic", "done speech=" + speech + " frames=" + speechFrames + " peak=" + (int) peak + " bytes=" + pcm.size());
            cb.onDone(wav(pcm.toByteArray()), speech && speechFrames >= MIN_SPEECH_FRAMES);
            return true;
        } catch (Throwable t) {
            if (rec != null) {
                try {
                    rec.release();
                } catch (Throwable ignored) {
                }
            }
            recorder = null;
            Log.i("WhaleMic", "attempt " + attempt + " threw: " + t);
            return false;
        }
    }

    private static void enableProcessing(int session) {
        try {
            if (AcousticEchoCanceler.isAvailable()) {
                AcousticEchoCanceler aec = AcousticEchoCanceler.create(session);
                if (aec != null) {
                    aec.setEnabled(true);
                }
            }
        } catch (Throwable ignored) {
        }
        try {
            if (AutomaticGainControl.isAvailable()) {
                AutomaticGainControl agc = AutomaticGainControl.create(session);
                if (agc != null) {
                    agc.setEnabled(true);
                }
            }
        } catch (Throwable ignored) {
        }
        try {
            if (NoiseSuppressor.isAvailable()) {
                NoiseSuppressor ns = NoiseSuppressor.create(session);
                if (ns != null) {
                    ns.setEnabled(true);
                }
            }
        } catch (Throwable ignored) {
        }
    }

    private static double rms(byte[] b, int n) {
        long sum = 0;
        int count = 0;
        for (int i = 0; i + 1 < n; i += 2) {
            int s = (short) ((b[i] & 0xff) | (b[i + 1] << 8));
            sum += (long) s * s;
            count++;
        }
        return count == 0 ? 0 : Math.sqrt((double) sum / count);
    }

    private static byte[] wav(byte[] pcm) {
        int len = pcm.length;
        byte[] out = new byte[44 + len];
        ascii(out, 0, "RIFF");
        int32(out, 4, 36 + len);
        ascii(out, 8, "WAVE");
        ascii(out, 12, "fmt ");
        int32(out, 16, 16);
        int16(out, 20, 1);
        int16(out, 22, 1);
        int32(out, 24, SR);
        int32(out, 28, SR * 2);
        int16(out, 32, 2);
        int16(out, 34, 16);
        ascii(out, 36, "data");
        int32(out, 40, len);
        System.arraycopy(pcm, 0, out, 44, len);
        return out;
    }

    private static void ascii(byte[] d, int o, String s) {
        for (int i = 0; i < s.length(); i++) {
            d[o + i] = (byte) s.charAt(i);
        }
    }

    private static void int32(byte[] d, int o, int v) {
        d[o] = (byte) v;
        d[o + 1] = (byte) (v >> 8);
        d[o + 2] = (byte) (v >> 16);
        d[o + 3] = (byte) (v >> 24);
    }

    private static void int16(byte[] d, int o, int v) {
        d[o] = (byte) v;
        d[o + 1] = (byte) (v >> 8);
    }
}
