package com.jp.dshtv;

import android.content.Context;
import android.speech.tts.TextToSpeech;
import android.util.Log;

import java.util.Locale;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

/**
 * Lazy TextToSpeech wrapper. Initialised on first /speak request so the
 * bridge does not pay the engine bring-up cost at boot.
 */
public final class Tts {

    private static final String TAG = "DshtvBridge";
    private static final long INIT_TIMEOUT_MS = 8000;

    private static Tts instance;

    private final TextToSpeech engine;

    private Tts(Context ctx) throws Exception {
        final CountDownLatch latch = new CountDownLatch(1);
        final boolean[] ok = new boolean[1];
        TextToSpeech created = new TextToSpeech(ctx.getApplicationContext(),
                new TextToSpeech.OnInitListener() {
                    @Override
                    public void onInit(int status) {
                        ok[0] = status == TextToSpeech.SUCCESS;
                        latch.countDown();
                    }
                });
        this.engine = created;
        boolean inited;
        try {
            inited = latch.await(INIT_TIMEOUT_MS, TimeUnit.MILLISECONDS);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            shutdownQuietly(created);
            throw new Exception("TTS init interrupted");
        }
        if (!inited) {
            shutdownQuietly(created);
            throw new Exception("TTS init timed out");
        }
        if (!ok[0]) {
            shutdownQuietly(created);
            throw new Exception("TTS init failed (no engine?)");
        }
        try {
            engine.setLanguage(Locale.US);
        } catch (Throwable t) {
            Log.i(TAG, "TTS setLanguage failed: " + t);
        }
        Log.i(TAG, "TTS ready");
    }

    public static synchronized Tts get(Context ctx) throws Exception {
        if (instance == null) {
            instance = new Tts(ctx);
        }
        return instance;
    }

    public boolean speak(String text) {
        try {
            int result = engine.speak(text, TextToSpeech.QUEUE_FLUSH, null,
                    "dshtv-" + System.currentTimeMillis());
            return result == TextToSpeech.SUCCESS;
        } catch (Throwable t) {
            Log.i(TAG, "TTS speak failed: " + t);
            return false;
        }
    }

    public static synchronized void shutdown() {
        if (instance != null) {
            shutdownQuietly(instance.engine);
            instance = null;
        }
    }

    private static void shutdownQuietly(TextToSpeech engine) {
        if (engine == null) {
            return;
        }
        try {
            engine.stop();
        } catch (Throwable ignored) {
        }
        try {
            engine.shutdown();
        } catch (Throwable ignored) {
        }
    }
}
