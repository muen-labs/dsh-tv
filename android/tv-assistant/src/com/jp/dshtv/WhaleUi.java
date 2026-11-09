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
 * Whale-chan state machine shared by the assistant activity and the session:
 * animated transparent pet, a three-line bubble (state / what was heard /
 * what DSH says) and TTS.
 */
public final class WhaleUi {

    private static final int DOT_ACCENT = R.drawable.dot_accent;
    private static final int DOT_OK = R.drawable.dot_on;
    private static final int DOT_ERROR = R.drawable.dot_off;

    private final Context ctx;
    private final WhalePet pet;
    private final View dot;
    private final TextView eyebrow;
    private final TextView you;
    private final TextView text;
    private final View closeBtn;
    private final View againBtn;
    private final View sendBtn;
    private final Runnable onFinished;
    private final Handler main = new Handler(Looper.getMainLooper());
    private final MicCapture mic = new MicCapture();

    private TextToSpeech tts;
    private boolean ttsReady;
    private Runnable closeTask;
    private Runnable busyTask;
    private String transcript = "";
    private boolean listening;

    public WhaleUi(Context ctx, View root, Runnable onFinished) {
        this.ctx = ctx;
        this.onFinished = onFinished;
        this.pet = new WhalePet((ImageView) root.findViewById(R.id.whale_art));
        this.dot = root.findViewById(R.id.whale_dot);
        this.eyebrow = (TextView) root.findViewById(R.id.whale_eyebrow);
        this.you = (TextView) root.findViewById(R.id.whale_you);
        this.text = (TextView) root.findViewById(R.id.whale_text);
        this.sendBtn = root.findViewById(R.id.whale_send);
        if (sendBtn != null) {
            sendBtn.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    if (listening) {
                        commit();
                    } else {
                        askAgain();
                    }
                }
            });
        }
        this.againBtn = root.findViewById(R.id.whale_again);
        if (againBtn != null) {
            againBtn.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    if (listening) {
                        commit();
                    } else {
                        askAgain();
                    }
                }
            });
        }
        this.closeBtn = root.findViewById(R.id.whale_close);
        if (closeBtn != null) {
            closeBtn.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    if (onFinished != null) {
                        onFinished.run();
                    }
                }
            });
        }
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

    public void listen() {
        Log.i("WhaleUi", "listen()");
        cancelClose();
        if (sendBtn != null) {
            sendBtn.setVisibility(View.VISIBLE);
        }
        if (againBtn != null) {
            againBtn.setContentDescription("Ask another question");
        }
        if (closeBtn != null) {
            closeBtn.setContentDescription("Close");
        }
        listening = true;
        pet.play(R.raw.whale_wave);
        setBubble("LISTENING", DOT_ACCENT, "", ctx.getString(R.string.listening));
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
                        setBubble("THINKING", DOT_ACCENT, "", "DSH is working on it…");
                        scheduleBusyPose();
                        new Thread(new Runnable() {
                            @Override
                            public void run() {
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
                                        setBubble("ASSISTANT", DOT_ACCENT, "“" + said + "”", "");
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
                        listening = false;
                        fail(message);
                    }
                });
            }
        });
    }

    /** QA-only: render a completed exchange without capture. */
    public void demo(String heard, String reply) {
        transcript = heard == null ? "" : heard;
        pet.play(R.raw.whale_celebrate);
        setBubble("ASSISTANT", DOT_OK,
                transcript.length() > 0 ? "“" + transcript + "”" : "", reply);
        showCloseButton();
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
        cancelBusyPose();
        mic.stop();
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
        cancelBusyPose();
        if (answer.error != null) {
            fail(ctx.getString(R.string.offline) + "\n" + answer.error);
            return;
        }
        String reply = answer.reply == null ? "" : answer.reply.trim();
        if (reply.length() == 0) {
            reply = "(no reply)";
        }
        pet.play(R.raw.whale_celebrate);
        setBubble("ASSISTANT", DOT_OK,
                transcript.length() > 0 ? "“" + transcript + "”" : "", reply);
        speak(reply);
        showCloseButton();
    }

    private void fail(String message) {
        Log.i("WhaleUi", "fail: " + message);
        cancelBusyPose();
        pet.play(R.raw.whale_wilt);
        setBubble("TRY AGAIN", DOT_ERROR, "", message);
        showCloseButton();
    }

    /** After a reply or error the overlay offers a focusable close (X) button. */
    private void showCloseButton() {
        try {
            if (sendBtn != null) {
                sendBtn.setVisibility(View.GONE);
            }
            if (againBtn != null) {
                againBtn.setContentDescription("Ask another question");
                againBtn.requestFocus();
            }
        } catch (Throwable ignored) {
        }
    }

    /** Ask another question in the same overlay. */
    private void askAgain() {
        try {
            if (tts != null) {
                tts.stop();
            }
        } catch (Throwable ignored) {
        }
        transcript = "";
        cancelClose();
        listen();
    }

    /** state / transcript / reply are three distinct lines, each optional. */
    private void setBubble(String state, int dotRes, String heard, String says) {
        try {
            eyebrow.setText(state);
            dot.setBackgroundResource(dotRes);
            if (heard == null || heard.length() == 0) {
                you.setText("");
                you.setVisibility(View.GONE);
            } else {
                you.setText(heard);
                you.setVisibility(View.VISIBLE);
            }
            if (says == null || says.length() == 0) {
                text.setText("");
                text.setVisibility(View.GONE);
            } else {
                text.setText(says);
                text.setVisibility(View.VISIBLE);
            }
            eyebrow.announceForAccessibility(state + ". " + (says == null ? "" : says));
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

    private void cancelClose() {
        if (closeTask != null) {
            main.removeCallbacks(closeTask);
            closeTask = null;
        }
    }
}
