package com.jp.dshtv;

import android.content.Intent;
import android.speech.RecognitionService;
import android.speech.SpeechRecognizer;

/**
 * Declared only so the assistant role considers this package qualified: AOSP's
 * AssistantRoleBehavior requires the voice-interaction metadata to name a
 * recognitionService as well as a sessionService. Voice capture happens in the
 * session with AudioRecord, so this stub never transcribes anything.
 */
public class WhaleRecognitionService extends RecognitionService {

    @Override
    protected void onStartListening(Intent recognizerIntent, Callback callback) {
        try {
            callback.error(SpeechRecognizer.ERROR_CLIENT);
        } catch (Throwable ignored) {
            // the calling app has gone away; nothing to report
        }
    }

    @Override
    protected void onStopListening(Callback callback) {
    }

    @Override
    protected void onCancel(Callback callback) {
    }
}
