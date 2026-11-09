package com.jp.dshtv;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import android.speech.tts.TextToSpeech;
import android.util.Log;
import android.view.View;
import android.widget.ImageView;
import android.widget.TextView;

import java.util.Locale;

/**
 * Whale-chan state machine shared by the assistant session window and the
 * launcher activity: animated transparent pet + speech bubble.
 */
public final class WhaleUi {

    private final Context ctx;
    private final WhalePet pet;
    private final TextView state;
    private final TextView text;
    private final Runnable onFinished;
    private final Handler main = new Handler(Looper.getMainLooper());
    private final MicCapture mic = new MicCapture();

    private TextToSpeech tts;
    private boolean ttsReady;
    private Runnable closeTask;
    private String transcript = "";
    private boolean listening;
    private Runnable busyTask;

    public WhaleUi(Context ctx, View root, Runnable onFinished) {
        this.ctx = ctx;
        this.onFinished = onFinished;
        this.pet = new WhalePet((ImageView) root.findViewById(R.id.whale_art));
        this.state = (TextView) root.findViewById(R.id.whale_state);
        this.text = (TextView) root.findViewById(R.id.whale_text);
        try {
            tts = new TextToSpeech(ctx, new TextToSpeech.OnInitListener() {
                @Override
                public void onInit(int status) {
                    ttsReady = status == TextToSpeech.SUCCESS;
                    if (ttsReady) {
                        try {
                            tts.setLanguage(Locale.US);
                        } catch (Throwable ignored) {
                        }
                    }
                }
            });
        } catch (Throwable ignored) {
        }
        pet.play(R.raw.whale_idle);
    }

    /** Start listening immediately; ends itself via onFinished when done. */
    public void listen() {
        Log.i("WhaleUi", "listen()");
        cancelClose();
        listening = true;
        pet.play(R.raw.whale_wave);
        bubble(ctx.getString(R.string.listening), "");
        mic.start(new MicCapture.Callback() {
            @Override
            public void onDone(final byte[] wav, final boolean heard) {
                main.post(new Runnable() {
                    @Override
                    public void run() {
                        listening = false;
                        if (!heard) {
                            fail(ctx.getString(R.string.empty));
                            return;
                        }
                        pet.play(R.raw.whale_think);
                        bubble(ctx.getString(R.string.thinking), "");
                        scheduleBusyPose();
                        new Thread(new Runnable() {
                            @Override
                            public void run() {
                                // Step 1: show what was spoken as soon as STT returns.
                                final WhaleClient.Stt stt = WhaleClient.transcribe(ctx, wav);
                                main.post(new Runnable() {
                                    @Override
                                    public void run() {
                                        if (stt.error != null) {
                                            fail(ctx.getString(R.string.offline) + "\n" + stt.error);
                                            return;
                                        }
                                        final String said = stt.text == null ? "" : stt.text.trim();
                                        if (said.length() == 0) {
                                            fail(ctx.getString(R.string.empty));
                                            return;
                                        }
                                        transcript = said;
                                        bubble("You said", said);
                                        // Step 2: hand the text to DSH.
                                        new Thread(new Runnable() {
                                            @Override
                                            public void run() {
                                                final WhaleClient.Answer answer = WhaleClient.ask(ctx, said);
                                                main.post(new Runnable() {
                                                    @Override
                                                    public void run() {
                                                        deliver(answer);
                                                    }
                                                });
                                            }
                                        }, "whale-brain").start();
                                    }
                                });
                            }
                        }, "whale-stt").start();
                    }
                });
            }

            @Override
            public void onError(final String message) {
                main.post(new Runnable() {
                    @Override
                    public void run() {
                        fail(message);
                    }
                });
            }
        });
    }

    public boolean isListening() {
        return listening;
    }

    /** OK button: stop capturing and send what we have to STT/DSH now. */
    public void commit() {
        if (listening) {
            mic.finishNow();
        }
    }

    public void stop() {
        cancelClose();
        mic.stop();
        cancelBusyPose();
        pet.stop();
        try {
            if (tts != null) {
                tts.stop();
            }
        } catch (Throwable ignored) {
        }
    }

    public void shutdown() {
        stop();
        try {
            if (tts != null) {
                tts.shutdown();
                tts = null;
                ttsReady = false;
            }
        } catch (Throwable ignored) {
        }
    }

    private void deliver(WhaleClient.Answer answer) {
        Log.i("WhaleUi", "deliver err=" + answer.error + " reply=" + answer.reply);
        if (answer.error != null) {
            fail(ctx.getString(R.string.offline) + "\n" + answer.error);
            return;
        }
        String reply = answer.reply == null ? "" : answer.reply.trim();
        if (reply.length() == 0) {
            reply = "(no reply)";
        }
        StringBuilder bubble = new StringBuilder();
        if (transcript.length() > 0) {
            bubble.append("You: ").append(transcript).append("\n");
        }
        bubble.append(reply);
        cancelBusyPose();
        pet.play(R.raw.whale_celebrate);
        bubble("Whale-chan", bubble.toString());
        speak(reply);
        scheduleClose(12000);
    }

    private void fail(String message) {
        Log.i("WhaleUi", "fail: " + message);
        cancelBusyPose();
        pet.play(R.raw.whale_wilt);
        bubble("Oops", message);
        scheduleClose(7000);
    }

    private void bubble(String stateText, String body) {
        try {
            state.setText(stateText);
            if (body == null || body.length() == 0) {
                text.setText("");
                text.setVisibility(View.GONE);
            } else {
                text.setText(body);
                text.setVisibility(View.VISIBLE);
            }
        } catch (Throwable ignored) {
        }
    }

    private void speak(String sentence) {
        if (!ttsReady || tts == null || sentence == null) {
            return;
        }
        String trimmed = sentence.length() > 240 ? sentence.substring(0, 240) : sentence;
        try {
            tts.speak(trimmed, TextToSpeech.QUEUE_FLUSH, null, "whale");
        } catch (Throwable ignored) {
        }
    }

    private void scheduleClose(long millis) {
        cancelClose();
        if (onFinished == null) {
            return;
        }
        closeTask = new Runnable() {
            @Override
            public void run() {
                onFinished.run();
            }
        };
        main.postDelayed(closeTask, millis);
    }

    private void scheduleBusyPose() {
        cancelBusyPose();
        busyTask = new Runnable() {
            @Override
            public void run() {
                pet.play(R.raw.whale_busy);
            }
        };
        main.postDelayed(busyTask, 6000);
    }

    private void cancelBusyPose() {
        if (busyTask != null) {
            main.removeCallbacks(busyTask);
            busyTask = null;
        }
    }

    private void cancelClose() {
        if (closeTask != null) {
            main.removeCallbacks(closeTask);
            closeTask = null;
        }
    }
}
