package com.jp.dshtv;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
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
 */
public class PairingActivity extends Activity {

    private static final String TAG = "WhalePairing";
    private final Handler main = new Handler(Looper.getMainLooper());
    private TextView status;
    private TextView hint;
    private View stateDot;
    private TextView codeView;
    private ImageView qrView;
    private EditText ipView;
    private Button pairButton;
    private String pairId;
    private boolean polling;
    private String pendingHost = "";

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        setContentView(R.layout.pairing);
        try {
            getWindow().setSoftInputMode(
                    android.view.WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_HIDDEN);
        } catch (Throwable ignored) {
        }
        status = (TextView) findViewById(R.id.pair_status);
        hint = (TextView) findViewById(R.id.pair_hint);
        stateDot = findViewById(R.id.pair_dot);
        codeView = (TextView) findViewById(R.id.pair_code);
        qrView = (ImageView) findViewById(R.id.pair_qr);
        ipView = (EditText) findViewById(R.id.pair_ip);
        pairButton = (Button) findViewById(R.id.pair_start);
        ipView.setText(WhaleConfig.host(this));
        ipView.clearFocus();
        pairButton.requestFocus();
        pairButton.setOnFocusChangeListener(new View.OnFocusChangeListener() {
            @Override
            public void onFocusChange(View v, boolean hasFocus) {
                v.animate().scaleX(hasFocus ? 1.03f : 1f).scaleY(hasFocus ? 1.03f : 1f)
                        .setDuration(120).start();
                v.setElevation(hasFocus ? 8 * getResources().getDisplayMetrics().density : 0);
            }
        });
        pairButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                beginPairing(ipView.getText().toString().trim());
            }
        });
        if (WhaleConfig.paired(this)) {
            setState("PAIRED", "Already paired — re-pairing replaces the current Mac.", true);
        }
        beginPairing(WhaleConfig.host(this));
    }

    private void setState(String pill, String message, boolean ok) {
        if (status != null) {
            status.setText(pill);
        }
        if (hint != null) {
            hint.setText(message);
            hint.setTextColor(ok ? 0xFF35D0FF : 0xFFFF6B6B);
        }
        if (stateDot != null) {
            stateDot.setBackgroundResource(ok ? R.drawable.dot_accent : R.drawable.dot_off);
        }
    }

    private void beginPairing(final String host) {
        if (host == null || host.isEmpty()) {
            setState("SETUP", "Enter the Mac mini's IP address first.", false);
            return;
        }
        pendingHost = host;
        setState("SCANNING", "Contacting " + host + "…", true);
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
                            setState("ERROR", "Could not reach the Mac: " + t.getMessage(), false);
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
            setState("WAITING", "Scan the QR with your phone and approve the code.", true);
            String qr = reply.optString("qr", "");
            if (!qr.isEmpty()) {
                byte[] png = Base64.decode(qr, Base64.DEFAULT);
                Bitmap bmp = BitmapFactory.decodeByteArray(png, 0, png.length);
                qrView.setImageBitmap(bmp);
            }
            startPolling(host);
        } catch (Throwable t) {
            setState("ERROR", "Bad pairing reply: " + t.getMessage(), false);
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
            setState("PAIRED", "Paired. Opening Whale-chan…", true);
            Intent whale = new Intent(this, WhaleActivity.class);
            startActivity(whale);
            finish();
        } catch (Throwable t) {
            setState("ERROR", "Pairing approved but saving failed: " + t.getMessage(), false);
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
        super.onDestroy();
    }
}
