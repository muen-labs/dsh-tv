package com.jp.dshtv;

import android.Manifest;
import android.content.Context;
import android.content.pm.PackageManager;
import android.media.AudioFormat;
import android.media.AudioRecord;
import android.media.MediaRecorder;
import android.util.Log;

import java.io.ByteArrayOutputStream;

/**
 * Records a short WAV clip from the built-in microphone with AudioRecord.
 */
public final class MicRecorder {

    private static final String TAG = "DshtvBridge";

    private static final int SAMPLE_RATE = 16000;
    private static final int CHANNELS = 1;
    private static final int BITS_PER_SAMPLE = 16;

    private MicRecorder() {
    }

    public static boolean hasPermission(Context ctx) {
        try {
            return ctx.checkSelfPermission(Manifest.permission.RECORD_AUDIO)
                    == PackageManager.PERMISSION_GRANTED;
        } catch (Throwable t) {
            return false;
        }
    }

    /** Record seconds (already clamped) with the requested source, return WAV. */
    public static byte[] recordWav(Context ctx, int seconds) throws Exception {
        return recordWav(ctx, seconds, "voice");
    }

    /**
     * Record seconds (already clamped) and return a complete WAV byte array.
     * The "voice" source enables the platform's speech-tuned processing
     * (noise suppression / AGC), which matters on this box's quiet far-field
     * array. "mic" is the raw source; "voice_communication", "camcorder" and
     * "unprocessed" are also accepted.
     */
    public static byte[] recordWav(Context ctx, int seconds, String sourceName)
            throws Exception {
        if (!hasPermission(ctx)) {
            throw new SecurityException("RECORD_AUDIO permission not granted");
        }
        int source = audioSource(sourceName);
        int bufferSize = AudioRecord.getMinBufferSize(SAMPLE_RATE,
                AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT);
        if (bufferSize <= 0) {
            bufferSize = SAMPLE_RATE; // fallback: 1 second of mono 16-bit
        }
        int recordBufferSize = Math.max(bufferSize * 2, 4096);
        AudioRecord recorder = null;
        try {
            recorder = new AudioRecord(source, SAMPLE_RATE,
                    AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT,
                    recordBufferSize);
            int state = recorder.getState();
            if (state != AudioRecord.STATE_INITIALIZED) {
                throw new Exception("AudioRecord not initialized (state=" + state + ")");
            }
            byte[] buffer = new byte[recordBufferSize];
            ByteArrayOutputStream pcm = new ByteArrayOutputStream(SAMPLE_RATE * seconds);
            int targetBytes = SAMPLE_RATE * seconds * (BITS_PER_SAMPLE / 8) * CHANNELS;
            recorder.startRecording();
            Log.i(TAG, "recording " + seconds + "s source=" + sourceName
                    + " (" + targetBytes + " bytes)");
            while (pcm.size() < targetBytes) {
                int want = Math.min(buffer.length, targetBytes - pcm.size());
                int read = recorder.read(buffer, 0, want);
                if (read <= 0) {
                    break;
                }
                pcm.write(buffer, 0, read);
            }
            try {
                recorder.stop();
            } catch (Throwable ignored) {
            }
            return wav(pcm.toByteArray(), SAMPLE_RATE, CHANNELS, BITS_PER_SAMPLE);
        } finally {
            if (recorder != null) {
                try {
                    recorder.release();
                } catch (Throwable ignored) {
                }
            }
        }
    }

    private static int audioSource(String name) {
        String s = name == null ? "" : name.trim().toLowerCase(java.util.Locale.US);
        if (s.equals("mic")) {
            return MediaRecorder.AudioSource.MIC;
        }
        if (s.equals("camcorder")) {
            return MediaRecorder.AudioSource.CAMCORDER;
        }
        if (s.equals("voice_communication") || s.equals("communication")) {
            return MediaRecorder.AudioSource.VOICE_COMMUNICATION;
        }
        if (s.equals("unprocessed")) {
            return MediaRecorder.AudioSource.UNPROCESSED;
        }
        // Default: speech recognition processing.
        return MediaRecorder.AudioSource.VOICE_RECOGNITION;
    }

    private static byte[] wav(byte[] pcm, int sampleRate, int channels, int bits) {
        int dataLen = pcm.length;
        byte[] header = new byte[44];
        writeAscii(header, 0, "RIFF");
        writeIntLE(header, 4, 36 + dataLen);
        writeAscii(header, 8, "WAVE");
        writeAscii(header, 12, "fmt ");
        writeIntLE(header, 16, 16);                                  // fmt chunk size
        writeShortLE(header, 20, 1);                                 // PCM
        writeShortLE(header, 22, channels);
        writeIntLE(header, 24, sampleRate);
        int byteRate = sampleRate * channels * (bits / 8);
        writeIntLE(header, 28, byteRate);
        writeShortLE(header, 32, channels * (bits / 8));             // block align
        writeShortLE(header, 34, bits);
        writeAscii(header, 36, "data");
        writeIntLE(header, 40, dataLen);

        byte[] out = new byte[44 + dataLen];
        System.arraycopy(header, 0, out, 0, 44);
        System.arraycopy(pcm, 0, out, 44, dataLen);
        return out;
    }

    private static void writeAscii(byte[] dst, int off, String value) {
        for (int i = 0; i < value.length(); i++) {
            dst[off + i] = (byte) value.charAt(i);
        }
    }

    private static void writeIntLE(byte[] dst, int off, int value) {
        dst[off] = (byte) (value & 0xff);
        dst[off + 1] = (byte) ((value >> 8) & 0xff);
        dst[off + 2] = (byte) ((value >> 16) & 0xff);
        dst[off + 3] = (byte) ((value >> 24) & 0xff);
    }

    private static void writeShortLE(byte[] dst, int off, int value) {
        dst[off] = (byte) (value & 0xff);
        dst[off + 1] = (byte) ((value >> 8) & 0xff);
    }
}
