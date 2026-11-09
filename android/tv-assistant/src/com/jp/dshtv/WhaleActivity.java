package com.jp.dshtv;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.view.KeyEvent;
import android.view.Window;
import android.view.WindowManager;
import android.view.View;

/** Launcher-tile fallback: same whale UI, listens as soon as it opens. */
public class WhaleActivity extends Activity {

    private WhaleUi ui;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        setContentView(R.layout.whale_session);
        applyBlurBehind();
        ensureBridgeRunning();
        if (!WhaleConfig.paired(this)) {
            startActivity(new Intent(this, PairingActivity.class));
            finish();
            return;
        }
        if (checkSelfPermission(Manifest.permission.RECORD_AUDIO)
                != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, 1);
            return;
        }
        startListening();
    }

    /**
     * Android 12+ can blur whatever is behind this window. The TV box reports no
     * blur support, so the gradient scrim in the layout is the real fallback;
     * this call is a no-op there and a bonus on supported devices.
     */
    private void applyBlurBehind() {
        if (Build.VERSION.SDK_INT < 31) {
            return;
        }
        try {
            Window window = getWindow();
            WindowManager.LayoutParams lp = window.getAttributes();
            lp.flags |= WindowManager.LayoutParams.FLAG_BLUR_BEHIND;
            lp.setBlurBehindRadius(dp(40));
            window.setAttributes(lp);
        } catch (Throwable ignored) {
            // no blur support: the scrim carries the contrast
        }
    }

    private int dp(int value) {
        return (int) Math.round(value * getResources().getDisplayMetrics().density);
    }

    /** The merged APK also serves the TV bridge; keep it running. */
    private void ensureBridgeRunning() {
        try {
            Intent service = new Intent(this, BridgeService.class);
            startForegroundService(service);
        } catch (Throwable ignored) {
            // the bridge setup activity can start it manually
        }
    }

    private void startListening() {
        View root = findViewById(R.id.whale_session_root);
        ui = new WhaleUi(this, root, new Runnable() {
            @Override
            public void run() {
                finish();
            }
        });
        if (getIntent() != null && getIntent().getBooleanExtra("demo", false)) {
            ui.demo("Open Stremio and search for anime",
                    "Opening Stremio and searching for “anime”, one moment.");
            return;
        }
        ui.listen();
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (ui != null && ui.isListening()
                && (keyCode == KeyEvent.KEYCODE_DPAD_CENTER
                    || keyCode == KeyEvent.KEYCODE_ENTER
                    || keyCode == KeyEvent.KEYCODE_NUMPAD_ENTER)) {
            ui.commit();
            return true;
        }
        if (keyCode == KeyEvent.KEYCODE_BACK) {
            finish();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

    @Override
    public void onRequestPermissionsResult(int code, String[] permissions, int[] results) {
        if (results.length > 0 && results[0] == PackageManager.PERMISSION_GRANTED) {
            startListening();
        } else {
            finish();
        }
    }

    @Override
    protected void onDestroy() {
        if (ui != null) {
            ui.shutdown();
        }
        super.onDestroy();
    }
}
