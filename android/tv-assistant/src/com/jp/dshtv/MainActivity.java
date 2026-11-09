package com.jp.dshtv;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.util.Log;
import android.util.TypedValue;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import java.util.ArrayList;
import java.util.List;

/**
 * TV-friendly control panel: shows bridge status and lets the user start the
 * server, enable accessibility, grant the microphone and refresh state.
 * Extras from adb are also honoured, e.g.:
 *   am start -n com.jp.dshtv/.MainActivity --es set_token secret --ez start_service true
 */
public class MainActivity extends Activity {

    private static final String TAG = "DshtvBridge";
    private static final int REQ_PERMISSIONS = 1001;
    private static final long REFRESH_MS = 2000;

    private SharedPreferences prefs;
    private TextView statusView;
    private TextView instructionsView;
    private final Handler handler = new Handler(Looper.getMainLooper());

    private final Runnable refreshRunnable = new Runnable() {
        @Override
        public void run() {
            refreshStatus();
            handler.postDelayed(this, REFRESH_MS);
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        prefs = BridgeService.prefs(this);
        buildUi();
        handleIntent(getIntent());
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        handleIntent(intent);
    }

    @Override
    protected void onResume() {
        super.onResume();
        handler.removeCallbacks(refreshRunnable);
        handler.post(refreshRunnable);
    }

    @Override
    protected void onPause() {
        handler.removeCallbacks(refreshRunnable);
        super.onPause();
    }

    @Override
    protected void onDestroy() {
        handler.removeCallbacksAndMessages(null);
        super.onDestroy();
    }

    /** Extras used by the Mac/adb to configure the bridge without the remote. */
    private void handleIntent(Intent intent) {
        if (intent == null) {
            return;
        }
        boolean changed = false;
        boolean portChanged = false;
        try {
            if (intent.hasExtra("set_token")) {
                String token = intent.getStringExtra("set_token");
                prefs.edit().putString(BridgeService.KEY_TOKEN,
                        token != null ? token : "").apply();
                changed = true;
                Log.i(TAG, "set_token via intent");
            }
            if (intent.getBooleanExtra("clear_token", false)) {
                prefs.edit().putString(BridgeService.KEY_TOKEN, "").apply();
                changed = true;
                Log.i(TAG, "clear_token via intent");
            }
            if (intent.hasExtra("set_port")) {
                int port = intent.getIntExtra("set_port", BridgeService.DEFAULT_PORT);
                if (port > 0 && port < 65536) {
                    prefs.edit().putInt(BridgeService.KEY_PORT, port).apply();
                    changed = true;
                    portChanged = true;
                    Log.i(TAG, "set_port via intent: " + port);
                }
            }
        } catch (Throwable t) {
            Log.i(TAG, "intent extras failed: " + t);
        }

        if (changed) {
            toast("Bridge settings updated");
        }
        if (portChanged && BridgeService.isRunning()) {
            // The listening socket needs a restart to pick up the new port.
            stopBridgeService();
            handler.postDelayed(new Runnable() {
                @Override
                public void run() {
                    startBridgeService();
                }
            }, 500);
        }
        if (intent.getBooleanExtra("start_service", false)) {
            startBridgeService();
            toast("Bridge service starting");
        }
        refreshStatus();
    }

    private void buildUi() {
        int background = 0xFF0E1116;
        int titleColor = 0xFF4FC3F7;
        int textColor = 0xFFE6EDF3;
        int mutedColor = 0xFF9AA7B4;

        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(background);
        scroll.setFillViewport(true);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(48), dp(32), dp(48), dp(32));
        scroll.addView(root, new ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        TextView title = new TextView(this);
        title.setText("DSH TV Bridge");
        title.setTextColor(titleColor);
        title.setTextSize(TypedValue.COMPLEX_UNIT_SP, 30f);
        root.addView(title);

        TextView subtitle = new TextView(this);
        subtitle.setText("com.jp.dshtv  v1.0  —  LAN control server");
        subtitle.setTextColor(mutedColor);
        subtitle.setTextSize(TypedValue.COMPLEX_UNIT_SP, 15f);
        root.addView(subtitle, marginTop(dp(2), dp(20)));

        statusView = new TextView(this);
        statusView.setTextColor(textColor);
        statusView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 19f);
        statusView.setLineSpacing(dp(3), 1f);
        root.addView(statusView, marginTop(dp(20), dp(20)));

        root.addView(button("Start service", new android.view.View.OnClickListener() {
            @Override
            public void onClick(android.view.View v) {
                startBridgeService();
                toast("Bridge service starting");
                refreshStatus();
            }
        }), marginTop(dp(10), dp(6)));

        root.addView(button("Stop service", new android.view.View.OnClickListener() {
            @Override
            public void onClick(android.view.View v) {
                stopBridgeService();
                toast("Bridge service stopped");
                refreshStatus();
            }
        }), marginTop(dp(0), dp(6)));

        root.addView(button("Open accessibility settings",
                new android.view.View.OnClickListener() {
                    @Override
                    public void onClick(android.view.View v) {
                        openAccessibilitySettings();
                    }
                }), marginTop(dp(0), dp(6)));

        root.addView(button("Grant microphone", new android.view.View.OnClickListener() {
            @Override
            public void onClick(android.view.View v) {
                requestBridgePermissions();
            }
        }), marginTop(dp(0), dp(6)));

        root.addView(button("Refresh", new android.view.View.OnClickListener() {
            @Override
            public void onClick(android.view.View v) {
                refreshStatus();
                toast("Status refreshed");
            }
        }), marginTop(dp(0), dp(6)));

        instructionsView = new TextView(this);
        instructionsView.setText(
                "Setup\n"
                        + "1. Open accessibility settings and enable \"DSH TV Bridge\".\n"
                        + "2. Grant the microphone if you want the /mic endpoint.\n"
                        + "3. Start the service (restarts automatically after a reboot).\n"
                        + "4. From the Mac:\n"
                        + "     curl http://<TV-IP>:8765/ping\n"
                        + "   If a token is set, add  -H 'X-DSH-Token: <token>'.\n"
                        + "5. Optional: tap the service notification to reopen this screen.");
        instructionsView.setTextColor(mutedColor);
        instructionsView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 15f);
        instructionsView.setLineSpacing(dp(2), 1f);
        root.addView(instructionsView, marginTop(dp(28), dp(30)));

        setContentView(scroll);
    }

    private Button button(String label, android.view.View.OnClickListener listener) {
        Button button = new Button(this);
        button.setText(label);
        button.setTextSize(TypedValue.COMPLEX_UNIT_SP, 18f);
        button.setAllCaps(false);
        button.setFocusable(true);
        button.setOnClickListener(listener);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        button.setLayoutParams(params);
        return button;
    }

    private LinearLayout.LayoutParams marginTop(int bottom, int top) {
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        params.topMargin = top;
        params.bottomMargin = bottom;
        return params;
    }

    private void refreshStatus() {
        if (statusView == null) {
            return;
        }
        StringBuilder sb = new StringBuilder();
        String ip = joinIps();
        sb.append("IP: ").append(ip.length() > 0 ? ip : "(no IPv4 address)")
                .append("    Port: ").append(BridgeService.port(this)).append('\n');
        sb.append("Server: ");
        if (BridgeService.isRunning()) {
            sb.append("RUNNING (uptime ").append(formatUptime(BridgeService.uptimeMs()))
                    .append(')');
        } else {
            sb.append("STOPPED");
        }
        sb.append('\n');
        sb.append("Accessibility service: ").append(accessibilityText()).append('\n');
        sb.append("Microphone permission: ")
                .append(MicRecorder.hasPermission(this) ? "GRANTED" : "DENIED").append('\n');
        sb.append("Token: ").append(tokenText()).append('\n');
        KeyService ks = KeyService.getInstance();
        String foreground = ks != null ? ks.foregroundPackage() : "";
        sb.append("Foreground app: ")
                .append(foreground != null && foreground.length() > 0 ? foreground : "(unknown)")
                .append('\n');
        sb.append("Model: ").append(Build.MANUFACTURER).append(' ').append(Build.MODEL);
        statusView.setText(sb.toString());
    }

    private String joinIps() {
        List<String> addresses = ApiHandler.ips();
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < addresses.size(); i++) {
            if (i > 0) {
                sb.append(", ");
            }
            sb.append(addresses.get(i));
        }
        return sb.toString();
    }

    private String accessibilityText() {
        boolean enabled = accessibilityEnabled();
        boolean connected = KeyService.isConnected();
        if (connected) {
            return "ENABLED, CONNECTED";
        }
        if (enabled) {
            return "ENABLED (not connected yet)";
        }
        return "DISABLED — enable it in accessibility settings";
    }

    private String tokenText() {
        String token = BridgeService.token(this);
        if (token.length() == 0) {
            return "not set (open API on LAN)";
        }
        if (token.length() <= 4) {
            return "set: " + token;
        }
        return "set: " + token.substring(0, 2) + "***" + token.substring(token.length() - 2);
    }

    private boolean accessibilityEnabled() {
        try {
            String enabled = Settings.Secure.getString(getContentResolver(),
                    Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES);
            return enabled != null && enabled.contains("com.jp.dshtv");
        } catch (Throwable t) {
            return false;
        }
    }

    private void startBridgeService() {
        try {
            startForegroundService(new Intent(this, BridgeService.class));
            Log.i(TAG, "startForegroundService requested");
        } catch (Throwable t) {
            Log.i(TAG, "startForegroundService failed: " + t);
            toast("Could not start service: " + t);
        }
    }

    private void stopBridgeService() {
        try {
            stopService(new Intent(this, BridgeService.class));
        } catch (Throwable t) {
            Log.i(TAG, "stopService failed: " + t);
        }
    }

    private void openAccessibilitySettings() {
        try {
            startActivity(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS));
        } catch (Throwable t) {
            Log.i(TAG, "open accessibility settings failed: " + t);
            toast("Could not open settings: " + t);
        }
    }

    private void requestBridgePermissions() {
        List<String> permissions = new ArrayList<String>();
        permissions.add(Manifest.permission.RECORD_AUDIO);
        if (Build.VERSION.SDK_INT >= 33) {
            permissions.add(Manifest.permission.POST_NOTIFICATIONS);
        }
        try {
            requestPermissions(permissions.toArray(new String[permissions.size()]),
                    REQ_PERMISSIONS);
        } catch (Throwable t) {
            Log.i(TAG, "requestPermissions failed: " + t);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions,
            int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == REQ_PERMISSIONS) {
            boolean granted = MicRecorder.hasPermission(this);
            toast(granted ? "Microphone granted" : "Microphone permission denied");
            refreshStatus();
        }
    }

    private String formatUptime(long millis) {
        long seconds = millis / 1000;
        long minutes = seconds / 60;
        long hours = minutes / 60;
        if (hours > 0) {
            return hours + "h" + (minutes % 60) + "m";
        }
        if (minutes > 0) {
            return minutes + "m" + (seconds % 60) + "s";
        }
        return seconds + "s";
    }

    private int dp(int value) {
        return (int) Math.round(value * getResources().getDisplayMetrics().density);
    }

    private void toast(String message) {
        try {
            Toast.makeText(this, message, Toast.LENGTH_SHORT).show();
        } catch (Throwable ignored) {
        }
    }
}
