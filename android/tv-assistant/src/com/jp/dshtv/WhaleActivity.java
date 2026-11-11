package com.jp.dshtv;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.view.KeyEvent;
import android.view.Window;
import android.view.WindowManager;
import android.view.View;
import android.widget.TextView;

/** Launcher-tile fallback: same whale UI, listens as soon as it opens. */
public class WhaleActivity extends Activity {

    private WhaleUi ui;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        setContentView(R.layout.whale_session);
        // Stronger scrim + a captured/blurred backdrop (cross-window blur is not
        // supported on these boxes). The modal fades/scales in when ready.
        OverlayModal.show(this, findViewById(R.id.whale_session_root));
        applyAppChip();
        applyBlurBehind();
        ensureBridgeRunning();
        // The agent is the app's home entry, so it must open. Pairing is offered once, on
        // first run; after that an unpaired agent still opens and BACK leads to settings.
        if (!WhaleConfig.paired(this) && WhaleConfig.takeFirstLaunch(this)) {
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
    /** App chip: name the app the assistant is actually over (the mockup's
     *  "Projectivy · Home" copy is only right when the launcher is behind). */
    private void applyAppChip() {
        try {
            TextView chip = (TextView) findViewById(R.id.whale_app_chip_text);
            if (chip == null) {
                return;
            }
            KeyService service = KeyService.getInstance();
            // by now our own window is foreground, so name the app that is
            // visible behind the modal
            String pkg = service != null ? service.refreshExternalPackage() : "";
            chip.setText(appChipLabel(pkg));
        } catch (Throwable ignored) {
        }
    }

    private String appChipLabel(String pkg) {
        if (pkg == null || pkg.length() == 0 || pkg.equals(getPackageName())) {
            return "DeepSeek TV";
        }
        if (pkg.equals("com.google.android.apps.tv.launcherx")) {
            return "Google TV · Home";
        }
        if (pkg.contains("projengmenu")) {
            return "Projectivy · Home";
        }
        try {
            PackageManager pm = getPackageManager();
            ApplicationInfo info = pm.getApplicationInfo(pkg, 0);
            CharSequence label = pm.getApplicationLabel(info);
            if (label != null && label.length() > 0) {
                return label.toString();
            }
        } catch (Throwable ignored) {
        }
        return pkg;
    }

    private void applyBlurBehind() {
        if (Build.VERSION.SDK_INT < 31) {
            return;
        }
        try {
            WindowManager wm = getSystemService(WindowManager.class);
            if (wm == null || !wm.isCrossWindowBlurEnabled()) {
                // expected on the onn boxes (no cross-window blur); the
                // OverlayModal capture fallback carries the blur instead
                return;
            }
            Window window = getWindow();
            WindowManager.LayoutParams lp = window.getAttributes();
            lp.flags |= WindowManager.LayoutParams.FLAG_BLUR_BEHIND;
            lp.setBlurBehindRadius(dp(24));
            window.setAttributes(lp);
            window.setBackgroundBlurRadius(dp(24));
        } catch (Throwable ignored) {
            // no blur support: the scrim/backdrop carries the contrast
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
        if (getIntent() != null && getIntent().getBooleanExtra("suggest", false)) {
            ui.suggest(getIntent().getStringExtra("suggest_title"),
                    getIntent().getStringExtra("suggest_reason"));
            return;
        }
        if (getIntent() != null && getIntent().getBooleanExtra("thinking", false)) {
            ui.debugState("THINKING", "DSH is working on it…");
            return;
        }
        if (getIntent() != null && getIntent().getBooleanExtra("demo", false)) {
            ui.demo("Open Stremio and search for anime",
                    "Opening Stremio and searching for “anime”, one moment.");
            return;
        }
        ui.listen();
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (ui != null && ui.handleDpad(keyCode)) {
            return true;
        }
        if (ui != null && ui.isListening()
                && (keyCode == KeyEvent.KEYCODE_DPAD_CENTER
                    || keyCode == KeyEvent.KEYCODE_ENTER
                    || keyCode == KeyEvent.KEYCODE_NUMPAD_ENTER)) {
            ui.commit();
            return true;
        }
        if (keyCode == KeyEvent.KEYCODE_BACK) {
            // Unpaired, there is nothing to fall back to: BACK opens the bridge settings
            // (which owns the pairing button) instead of leaving a dead app.
            if (!WhaleConfig.paired(this)) {
                startActivity(new Intent(this, MainActivity.class));
            }
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
