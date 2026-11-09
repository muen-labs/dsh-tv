package com.jp.dshtv;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.SpannableString;
import android.text.Spanned;
import android.text.style.ForegroundColorSpan;
import android.text.style.StyleSpan;
import android.util.Base64;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.TextView;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;

/**
 * QR pairing: the TV asks the Mac for a pairing id, shows the QR (which opens
 * the approval page on a phone), and polls until the user approves. The Mac
 * then returns host/port/token, which are stored for the assistant.
 *
 * States map onto the mockup (docs/ui-mockup.html #pairing):
 *   idle    -> READY badge, address input + "Pair this TV"
 *   scanning-> SCANNING badge, "Contacting <mac>…"
 *   waiting -> WAITING badge, real QR + code + "Waiting for DSH approval…"
 *   paired  -> PAIRED badge, all three tracker steps done
 *   error   -> ERROR badge, address input comes back with the reason
 */
public class PairingActivity extends Activity {

    private static final String TAG = "WhalePairing";
    private static final int CODE_TTL_SECONDS = 300;

    private final Handler main = new Handler(Looper.getMainLooper());
    private TextView badgeText;
    private TextView hint;
    private View badge;
    private View dot;
    private TextView codeView;
    private ImageView qrView;
    private View qrFallback;
    private TextView urlView;
    private EditText ipView;
    private View idleRow;
    private View waitingRow;
    private TextView waitingText;
    private Button startButton;
    private View changeMac;
    private TextView[] stepNums = new TextView[3];
    private TextView[] stepLabels = new TextView[3];
    private TextView ipChip;

    private String pairId;
    private boolean polling;
    private String pendingHost = "";
    private int remaining;
    private boolean counting;

    private final Runnable tick = new Runnable() {
        @Override
        public void run() {
            if (!counting) {
                return;
            }
            if (remaining > 0) {
                remaining--;
                showExpiry();
                main.postDelayed(this, 1000);
            } else {
                counting = false;
                hint.setText("Code expired — use a different Mac or re-pair.");
                hint.setTextColor(getColor(R.color.warning));
            }
        }
    };

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        setContentView(R.layout.pairing);
        try {
            getWindow().setSoftInputMode(
                    android.view.WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_HIDDEN);
        } catch (Throwable ignored) {
        }
        badgeText = (TextView) findViewById(R.id.pair_status);
        badge = findViewById(R.id.pair_badge);
        hint = (TextView) findViewById(R.id.pair_hint);
        dot = findViewById(R.id.pair_dot);
        codeView = (TextView) findViewById(R.id.pair_code);
        qrView = (ImageView) findViewById(R.id.pair_qr);
        qrFallback = findViewById(R.id.pair_qr_fallback);
        urlView = (TextView) findViewById(R.id.pair_url);
        ipView = (EditText) findViewById(R.id.pair_ip);
        idleRow = findViewById(R.id.pair_idle);
        waitingRow = findViewById(R.id.pair_waiting);
        waitingText = (TextView) findViewById(R.id.pair_waiting_text);
        startButton = (Button) findViewById(R.id.pair_start);
        changeMac = findViewById(R.id.btn_change_mac);
        ipChip = (TextView) findViewById(R.id.pair_ip_chip);
        stepNums[0] = (TextView) findViewById(R.id.pair_step1);
        stepNums[1] = (TextView) findViewById(R.id.pair_step2);
        stepNums[2] = (TextView) findViewById(R.id.pair_step3);
        stepLabels[0] = (TextView) findViewById(R.id.pair_step1_label);
        stepLabels[1] = (TextView) findViewById(R.id.pair_step2_label);
        stepLabels[2] = (TextView) findViewById(R.id.pair_step3_label);

        ipView.setText(WhaleConfig.host(this));
        ipView.clearFocus();
        showLocalIp();
        styleFocus(startButton);
        styleFocus(changeMac);

        startButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                beginPairing(ipView.getText().toString().trim());
            }
        });
        changeMac.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                polling = false;
                counting = false;
                main.removeCallbacks(tick);
                showIdle("Enter your Mac's address, then pair.");
            }
        });

        if (WhaleConfig.paired(this)) {
            showIdle("Already paired — re-pairing replaces the current Mac.");
        }
        beginPairing(WhaleConfig.host(this));
    }

    /** Same 10-foot focus treatment as the bridge home: lift + scale 1.03. */
    private void styleFocus(final View view) {
        view.setOnFocusChangeListener(new View.OnFocusChangeListener() {
            @Override
            public void onFocusChange(View v, boolean hasFocus) {
                v.animate().scaleX(hasFocus ? 1.03f : 1f)
                        .scaleY(hasFocus ? 1.03f : 1f)
                        .setDuration(120).start();
                v.setElevation(hasFocus ? 8 * getResources().getDisplayMetrics().density : 0);
            }
        });
    }

    private void showLocalIp() {
        try {
            java.util.List<String> addresses = ApiHandler.ips();
            String ip = "";
            for (String address : addresses) {
                if (address.startsWith("192.168.") || address.startsWith("10.")) {
                    ip = address;
                    break;
                }
            }
            if (ip.length() == 0 && !addresses.isEmpty()) {
                ip = addresses.get(0);
            }
            ipChip.setText(ip.length() > 0 ? ip : "no LAN IP");
        } catch (Throwable ignored) {
        }
    }

    private void setBadge(String word, int pillRes, int colorRes, boolean ok) {
        if (badgeText == null) {
            return;
        }
        badgeText.setText(word);
        badgeText.setTextColor(getColor(colorRes));
        badge.setBackgroundResource(pillRes);
        dot.setBackgroundResource(ok ? R.drawable.dot_on : R.drawable.dot_off);
    }

    private void setWaitingVisible(boolean waiting) {
        waitingRow.setVisibility(waiting ? View.VISIBLE : View.GONE);
        idleRow.setVisibility(waiting ? View.GONE : View.VISIBLE);
    }

    /** Tracker: 0..2; done steps turn green, the active one is filled primary. */
    private void setSteps(int doneUpTo, int active) {
        for (int i = 0; i < 3; i++) {
            if (i < doneUpTo) {
                stepNums[i].setBackgroundResource(R.drawable.mini_step_done);
                stepNums[i].setTextColor(getColor(R.color.success));
                stepLabels[i].setTextColor(getColor(R.color.foreground));
            } else if (i == active) {
                stepNums[i].setBackgroundResource(R.drawable.mini_step_on);
                stepNums[i].setTextColor(getColor(R.color.white));
                stepLabels[i].setTextColor(getColor(R.color.foreground));
            } else {
                stepNums[i].setBackgroundResource(R.drawable.mini_step_off);
                stepNums[i].setTextColor(getColor(R.color.muted_foreground));
                stepLabels[i].setTextColor(getColor(R.color.dim_label));
            }
        }
    }

    private void showIdle(String message) {
        counting = false;
        main.removeCallbacks(tick);
        setBadge("READY", R.drawable.pill_success, R.color.success, true);
        setWaitingVisible(false);
        codeView.setText("——————");
        qrView.setVisibility(View.GONE);
        qrFallback.setVisibility(View.GONE);
        hint.setText(message);
        hint.setTextColor(getColor(R.color.dim_label));
        setSteps(0, 0);
        startButton.post(new Runnable() {
            @Override
            public void run() {
                startButton.requestFocus();
            }
        });
    }

    private void showScanning(String host) {
        setBadge("SCANNING", R.drawable.pill_warn, R.color.warning, true);
        setWaitingVisible(true);
        waitingText.setText("Contacting " + host + "…");
        codeView.setText("——————");
        hint.setText("Listening for a pairing session on " + host + ".");
        hint.setTextColor(getColor(R.color.dim_label));
        setSteps(0, 0);
        changeMac.post(new Runnable() {
            @Override
            public void run() {
                changeMac.requestFocus();
            }
        });
    }

    private void showWaiting() {
        setBadge("WAITING", R.drawable.pill_plain, R.color.primary_hover, true);
        setWaitingVisible(true);
        waitingText.setText("Waiting for DSH approval…");
        setSteps(1, 1);
        focusChangeMac();
    }

    private void focusChangeMac() {
        changeMac.post(new Runnable() {
            @Override
            public void run() {
                changeMac.requestFocus();
            }
        });
    }

    private void startCountdown() {
        counting = true;
        remaining = CODE_TTL_SECONDS;
        showExpiry();
        main.removeCallbacks(tick);
        main.postDelayed(tick, 1000);
    }

    private void showExpiry() {
        int mins = remaining / 60;
        int secs = remaining % 60;
        String time = mins + ":" + (secs < 10 ? "0" + secs : String.valueOf(secs));
        SpannableString text = new SpannableString("Code expires in " + time);
        int start = text.length() - time.length();
        text.setSpan(new ForegroundColorSpan(getColor(R.color.warning)), start, text.length(),
                Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        text.setSpan(new StyleSpan(Typeface.BOLD), start, text.length(),
                Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        hint.setText(text);
        hint.setTextColor(getColor(R.color.dim_label));
    }

    private void beginPairing(final String host) {
        if (host == null || host.isEmpty()) {
            setBadge("ERROR", R.drawable.pill_danger, R.color.destructive, false);
            setWaitingVisible(false);
            hint.setText("Enter the Mac mini's IP address first.");
            hint.setTextColor(getColor(R.color.destructive));
            return;
        }
        pendingHost = host;
        showScanning(host);
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    final JSONObject reply = getJson("http://" + host + ":8766/pair/new");
                    main.post(new Runnable() {
                        @Override
                        public void run() {
                            onPairCreated(host, reply);
                        }
                    });
                } catch (final Throwable t) {
                    main.post(new Runnable() {
                        @Override
                        public void run() {
                            setBadge("ERROR", R.drawable.pill_danger, R.color.destructive, false);
                            setWaitingVisible(false);
                            hint.setText("Could not reach the Mac: " + t.getMessage());
                            hint.setTextColor(getColor(R.color.destructive));
                            startButton.post(new Runnable() {
                                @Override
                                public void run() {
                                    startButton.requestFocus();
                                }
                            });
                            Log.w(TAG, "pair/new failed", t);
                        }
                    });
                }
            }
        }, "whale-pair-new").start();
    }

    private void onPairCreated(String host, JSONObject reply) {
        try {
            pairId = reply.getString("id");
            String code = reply.getString("code");
            Log.i(TAG, "pair id=" + pairId + " code=" + code);
            codeView.setText(code);
            String qr = reply.optString("qr", "");
            String url = reply.optString("url", "");
            if (!qr.isEmpty()) {
                byte[] png = Base64.decode(qr, Base64.DEFAULT);
                Bitmap bmp = BitmapFactory.decodeByteArray(png, 0, png.length);
                qrView.setImageBitmap(bmp);
                qrView.setVisibility(View.VISIBLE);
                qrFallback.setVisibility(View.GONE);
            } else {
                // no QR from the Mac: show the approve link + code instead of a
                // blank white plate (the phone can open the link directly)
                qrView.setVisibility(View.GONE);
                qrFallback.setVisibility(View.VISIBLE);
                urlView.setText(url.length() > 0 ? url : "DSH is not rendering a QR");
            }
            showWaiting();
            startCountdown();
            startPolling(host);
        } catch (Throwable t) {
            setBadge("ERROR", R.drawable.pill_danger, R.color.destructive, false);
            hint.setText("Bad pairing reply: " + t.getMessage());
            hint.setTextColor(getColor(R.color.destructive));
        }
    }

    private void startPolling(final String host) {
        polling = true;
        main.postDelayed(new Runnable() {
            @Override
            public void run() {
                pollOnce(host);
            }
        }, 1200);
    }

    private void pollOnce(final String host) {
        if (!polling || pairId == null) {
            return;
        }
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    final JSONObject reply = getJson("http://" + host + ":8766/pair/status?id=" + pairId);
                    main.post(new Runnable() {
                        @Override
                        public void run() {
                            if (!polling) {
                                return;
                            }
                            if (reply.optBoolean("approved")) {
                                polling = false;
                                saveAndFinish(host, reply.optJSONObject("config"));
                            } else {
                                main.postDelayed(new Runnable() {
                                    @Override
                                    public void run() {
                                        pollOnce(host);
                                    }
                                }, 1500);
                            }
                        }
                    });
                } catch (Throwable t) {
                    main.postDelayed(new Runnable() {
                        @Override
                        public void run() {
                            pollOnce(host);
                        }
                    }, 2500);
                }
            }
        }, "whale-pair-poll").start();
    }

    private void saveAndFinish(String host, JSONObject config) {
        try {
            String h = config != null ? config.optString("host", host) : host;
            String p = config != null ? config.optString("port", "8766") : "8766";
            String t = config != null ? config.optString("token", "") : "";
            WhaleConfig.save(this, h, p, t);
            Log.i(TAG, "paired with " + h + ":" + p);
            counting = false;
            main.removeCallbacks(tick);
            setBadge("PAIRED", R.drawable.pill_success, R.color.success, true);
            setSteps(3, -1);
            hint.setText("Paired. Opening the assistant…");
            hint.setTextColor(getColor(R.color.success));
            main.postDelayed(new Runnable() {
                @Override
                public void run() {
                    Intent whale = new Intent(PairingActivity.this, WhaleActivity.class);
                    startActivity(whale);
                    finish();
                }
            }, 900);
        } catch (Throwable t) {
            setBadge("ERROR", R.drawable.pill_danger, R.color.destructive, false);
            hint.setText("Pairing approved but saving failed: " + t.getMessage());
            hint.setTextColor(getColor(R.color.destructive));
        }
    }

    private static JSONObject getJson(String url) throws Exception {
        HttpURLConnection c = null;
        try {
            c = (HttpURLConnection) new URL(url).openConnection();
            c.setConnectTimeout(4000);
            c.setReadTimeout(6000);
            InputStream is = c.getInputStream();
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte[] buf = new byte[2048];
            int n;
            while ((n = is.read(buf)) > 0) {
                out.write(buf, 0, n);
            }
            is.close();
            return new JSONObject(new String(out.toByteArray(), "UTF-8"));
        } finally {
            if (c != null) {
                c.disconnect();
            }
        }
    }

    @Override
    protected void onDestroy() {
        polling = false;
        counting = false;
        main.removeCallbacksAndMessages(null);
        super.onDestroy();
    }
}
