package com.jp.dshtv;

import android.app.AlertDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.os.Handler;
import android.os.Looper;
import android.speech.tts.TextToSpeech;
import android.util.Log;
import android.view.View;
import android.view.WindowManager;
import android.view.inputmethod.EditorInfo;
import android.view.inputmethod.InputMethodManager;
import android.widget.EditText;
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
    private final View root;
    private final WhalePet pet;
    private final View dot;
    private final View rule;
    private final TextView eyebrow;
    private final TextView you;
    private final TextView text;
    private final View closeBtn;
    private final View againBtn;
    private View settingsBtn;
    private View typeBtn;
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
        this.root = root;
        this.onFinished = onFinished;
        this.pet = new WhalePet((ImageView) root.findViewById(R.id.whale_art));
        this.dot = root.findViewById(R.id.whale_dot);
        this.rule = root.findViewById(R.id.whale_rule);
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
        this.typeBtn = root.findViewById(R.id.whale_type);
        if (this.typeBtn != null) {
            this.typeBtn.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    openTypeEntry();
                }
            });
        }
        this.settingsBtn = root.findViewById(R.id.whale_settings);
        if (this.settingsBtn != null) {
            this.settingsBtn.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    openBridge();
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
            // put D-pad focus straight on Send for each new request
            sendBtn.post(new Runnable() {
                @Override
                public void run() {
                    try {
                        sendBtn.requestFocus();
                    } catch (Throwable ignored) {
                    }
                }
            });
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

    /** Render a proactive suggestion (no transcript). */
    public void suggest(String title, String reason) {
        pet.play(R.raw.whale_celebrate);
        String line = ((reason == null ? "" : reason.trim()) + " "
                + (title == null || title.length() == 0 ? "" : "Want to watch “" + title + "”?")).trim();
        setBubble("FOR YOU", DOT_OK, "", line);
        showCloseButton();
    }

    /** QA-only: render an intermediate state (e.g. THINKING) without capture. */
    public void debugState(String state, String says) {
        pet.play(R.raw.whale_think);
        setBubble(state, DOT_ACCENT, "", says);
        showCloseButton();
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

    /**
     * Typing exists because voice capture fails in a noisy room and recognition errors are
     * worse than a typo the person can see. The TV's on-screen keyboard is driven by the
     * same remote, so this is not a fallback for "no remote" — it is for "no microphone".
     */
    private void openTypeEntry() {
        final EditText input = new EditText(ctx);
        input.setSingleLine(true);
        input.setImeOptions(EditorInfo.IME_ACTION_DONE);
        input.setOnEditorActionListener(new TextView.OnEditorActionListener() {
            @Override
            public boolean onEditorAction(TextView v, int actionId, android.view.KeyEvent event) {
                if (actionId == EditorInfo.IME_ACTION_DONE
                        || (event != null && event.getKeyCode() == android.view.KeyEvent.KEYCODE_ENTER)) {
                    submitTyped(v.getText().toString());
                    if (dialogRef != null && dialogRef.isShowing()) {
                        dialogRef.dismiss();
                    }
                    return true;
                }
                return false;
            }
        });
        // A TV remote has no "Done": OK on the field must submit. Hardware keys do not fire
        // the IME action, so they are handled explicitly.
        input.setOnKeyListener(new View.OnKeyListener() {
            @Override
            public boolean onKey(View v, int keyCode, android.view.KeyEvent event) {
                if (event.getAction() != android.view.KeyEvent.ACTION_DOWN) {
                    return false;
                }
                if (keyCode == android.view.KeyEvent.KEYCODE_ENTER
                        || keyCode == android.view.KeyEvent.KEYCODE_DPAD_CENTER
                        || keyCode == android.view.KeyEvent.KEYCODE_NUMPAD_ENTER) {
                    submitTyped(input.getText().toString());
                    if (dialogRef != null && dialogRef.isShowing()) {
                        dialogRef.dismiss();
                    }
                    return true;
                }
                return false;
            }
        });
        input.setHint("Ask Whale-chan…");
        input.setPadding(28, 14, 28, 14);

        final AlertDialog dialog = new AlertDialog.Builder(ctx)
                .setTitle("Type a request")
                .setView(input)
                .setPositiveButton("Ask", new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface d, int which) {
                        submitTyped(input.getText().toString());
                    }
                })
                .setNegativeButton("Cancel", null)
                .create();

        dialogRef = dialog;
        dialog.setOnShowListener(new DialogInterface.OnShowListener() {
            @Override
            public void onShow(DialogInterface d) {
                input.requestFocus();
                if (dialog.getWindow() != null) {
                    dialog.getWindow().setSoftInputMode(
                            WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_VISIBLE);
                }
                InputMethodManager ime = (InputMethodManager)
                        ctx.getSystemService(Context.INPUT_METHOD_SERVICE);
                if (ime != null) {
                    ime.showSoftInput(input, InputMethodManager.SHOW_IMPLICIT);
                }
            }
        });
        dialog.show();
    }

    private AlertDialog dialogRef;

    private void submitTyped(String raw) {
        final String said = raw == null ? "" : raw.trim();
        if (said.length() == 0) {
            fail(ctx.getString(R.string.empty));
            return;
        }
        transcript = said;
        pet.play(R.raw.whale_think);
        setBubble("THINKING", DOT_ACCENT, "“" + said + "”", "DSH is working on it…");
        scheduleBusyPose();
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

    /**
     * Explicit D-pad contract for the overlay (the user asked for
     * "left goes to the gear, up defaults back to the mic"). The gear sits at
     * the left end of the control row above the composer:
     *   Send:   LEFT -> gear, UP -> mic
     *   gear:   RIGHT -> mic, DOWN -> Send, UP -> mic
     *   mic:    LEFT -> gear
     *   close:  LEFT -> mic
     * nextFocus* ids are declared in the layout as well, but this handler makes
     * the contract deterministic when the composer state hides/shows controls.
     */
    public boolean handleDpad(int keyCode) {
        try {
            if (root == null) {
                return false;
            }
            View focused = root.findFocus();
            if (focused == null) {
                return false;
            }
            if (focused == sendBtn) {
                if (keyCode == android.view.KeyEvent.KEYCODE_DPAD_LEFT) {
                    return focus(settingsBtn);
                }
                if (keyCode == android.view.KeyEvent.KEYCODE_DPAD_UP) {
                    return focus(againBtn);
                }
                return false;
            }
            if (focused == settingsBtn) {
                if (keyCode == android.view.KeyEvent.KEYCODE_DPAD_RIGHT
                        || keyCode == android.view.KeyEvent.KEYCODE_DPAD_UP) {
                    return focus(againBtn);
                }
                if (keyCode == android.view.KeyEvent.KEYCODE_DPAD_DOWN) {
                    if (sendBtn != null && sendBtn.getVisibility() == View.VISIBLE) {
                        return focus(sendBtn);
                    }
                    return focus(againBtn);
                }
                return false;
            }
            if (focused == againBtn && keyCode == android.view.KeyEvent.KEYCODE_DPAD_LEFT) {
                return focus(settingsBtn);
            }
            if (focused == closeBtn && keyCode == android.view.KeyEvent.KEYCODE_DPAD_LEFT) {
                return focus(againBtn);
            }
        } catch (Throwable ignored) {
        }
        return false;
    }

    private boolean focus(View view) {
        if (view == null) {
            return false;
        }
        try {
            return view.requestFocus();
        } catch (Throwable t) {
            return false;
        }
    }

    /** Gear: leave the overlay and open the Bridge home / settings screen. */
    private void openBridge() {
        try {
            stop();
            Intent intent = new Intent(ctx, MainActivity.class);
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            ctx.startActivity(intent);
        } catch (Throwable t) {
            Log.i("WhaleUi", "openBridge failed: " + t);
        }
        if (onFinished != null) {
            onFinished.run();
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
            if (rule != null) {
                // the 4px accent rule takes the state colour (design: primary /
                // success / destructive)
                rule.setBackgroundColor(dotRes == DOT_OK ? 0xFF00E096
                        : dotRes == DOT_ERROR ? 0xFFFF3D71 : 0xFF3366FF);
            }
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
