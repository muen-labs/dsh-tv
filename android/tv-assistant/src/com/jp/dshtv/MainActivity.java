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
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import java.util.ArrayList;
import java.util.List;

/**
 * TV control panel: status at a glance, the pairing entry point, and the
 * bridge controls. Extras from adb are still honoured, e.g.
 *   am start -n com.jp.dshtv/.MainActivity --es set_token secret --ez start_service true
 */
public class MainActivity extends Activity {

    private static final String TAG = "DshtvBridge";
    private static final int REQ_PERMISSIONS = 1001;
    private static final long REFRESH_MS = 2000;

    private SharedPreferences prefs;
    private View statusDot;
    private TextView statusText;
    private View statusBadge;
    private View healthyBadge;
    private View healthyDot;
    private TextView healthyText;
    private View connectedBadge;
    private View connectedDot;
    private TextView connectedText;
    private TextView valueAddress;
    private TextView valuePort;
    private TextView valueMic;
    private TextView valueAccessibility;
    private TextView valueForeground;
    private TextView valueUptime;
    private TextView codeCurl;
    private Button btnStop;
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
        setContentView(R.layout.activity_main);
        bindUi();
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

    private void bindUi() {
        statusDot = findViewById(R.id.status_dot);
        statusText = (TextView) findViewById(R.id.status_text);
        statusBadge = findViewById(R.id.status_badge);
        healthyBadge = findViewById(R.id.healthy_badge);
        healthyDot = findViewById(R.id.healthy_dot);
        healthyText = (TextView) findViewById(R.id.healthy_text);
        connectedBadge = findViewById(R.id.connected_badge);
        connectedDot = findViewById(R.id.connected_dot);
        connectedText = (TextView) findViewById(R.id.connected_text);
        valueAddress = (TextView) findViewById(R.id.value_address);
        valuePort = (TextView) findViewById(R.id.value_port);
        valueMic = (TextView) findViewById(R.id.value_mic);
        valueAccessibility = (TextView) findViewById(R.id.value_accessibility);
        valueForeground = (TextView) findViewById(R.id.value_foreground);
        valueUptime = (TextView) findViewById(R.id.value_uptime);
        codeCurl = (TextView) findViewById(R.id.code_curl);

        Button pair = (Button) findViewById(R.id.btn_pair);
        Button pairSecond = (Button) findViewById(R.id.btn_pair_second);
        Button testMic = (Button) findViewById(R.id.btn_test_mic);
        btnStop = (Button) findViewById(R.id.btn_stop);
        View accessibility = findViewById(R.id.btn_accessibility);
        View mic = findViewById(R.id.btn_mic);
        View refresh = findViewById(R.id.btn_refresh);

        pair.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                startActivity(new Intent(MainActivity.this, PairingActivity.class));
            }
        });
        pairSecond.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                startActivity(new Intent(MainActivity.this, PairingActivity.class));
            }
        });
        testMic.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                openAssistant();
            }
        });
        btnStop.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                if (BridgeService.isRunning()) {
                    stopBridgeService();
                    toast("Bridge service stopped");
                } else {
                    startBridgeService();
                    toast("Bridge service starting");
                }
                refreshStatus();
            }
        });
        accessibility.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                openAccessibilitySettings();
            }
        });
        mic.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                requestBridgePermissions();
            }
        });
        refresh.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                refreshStatus();
                toast("Status refreshed");
            }
        });

        // the mockup bolds the product/device names inside the setup steps
        boldPart(R.id.step_text_1, "DSH TV Bridge");
        boldPart(R.id.step_text_3, "Mac");
        boldPart(R.id.step_text_4, "Disney+");

        for (View b : new View[]{pair, pairSecond, testMic, btnStop, accessibility, mic,
                refresh}) {
            styleFocus(b);
        }
        pair.requestFocus();
    }

    /** Render one substring of a TextView in Roboto Bold (mockup inline <b>). */
    private void boldPart(int viewId, String part) {
        try {
            TextView view = (TextView) findViewById(viewId);
            if (view == null || part == null) {
                return;
            }
            String text = view.getText().toString();
            int at = text.indexOf(part);
            if (at < 0) {
                return;
            }
            android.text.SpannableString spanned = new android.text.SpannableString(text);
            spanned.setSpan(new android.text.style.StyleSpan(android.graphics.Typeface.BOLD),
                    at, at + part.length(), android.text.Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
            view.setText(spanned);
        } catch (Throwable ignored) {
        }
    }

    /** 10-foot focus: lift and scale the focused control so the remote is obvious. */
    private void styleFocus(final View view) {
        view.setOnFocusChangeListener(new View.OnFocusChangeListener() {
            @Override
            public void onFocusChange(View v, boolean hasFocus) {
                v.animate().scaleX(hasFocus ? 1.03f : 1f)
                        .scaleY(hasFocus ? 1.03f : 1f)
                        .setDuration(120).start();
                v.setElevation(hasFocus ? dp(8) : 0);
            }
        });
    }

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
            }
            if (intent.getBooleanExtra("clear_token", false)) {
                prefs.edit().putString(BridgeService.KEY_TOKEN, "").apply();
                changed = true;
            }
            if (intent.hasExtra("set_port")) {
                int port = intent.getIntExtra("set_port", BridgeService.DEFAULT_PORT);
                if (port > 0 && port < 65536) {
                    prefs.edit().putInt(BridgeService.KEY_PORT, port).apply();
                    changed = true;
                    portChanged = true;
                }
            }
        } catch (Throwable t) {
            Log.i(TAG, "intent extras failed: " + t);
        }

        if (changed) {
            toast("Bridge settings updated");
        }
        if (portChanged && BridgeService.isRunning()) {
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

    private void refreshStatus() {
        if (statusText == null) {
            return;
        }
        boolean running = BridgeService.isRunning();
        String uptime = running ? formatUptime(BridgeService.uptimeMs()) : "";
        statusDot.setBackgroundResource(running ? R.drawable.dot_on : R.drawable.dot_off);
        statusText.setText(running ? "RUNNING · " + uptime : "STOPPED");
        statusText.setTextColor(getColor(running ? R.color.success : R.color.destructive));
        statusBadge.setBackgroundResource(running
                ? R.drawable.pill_success : R.drawable.pill_danger);

        btnStop.setText(running ? "Stop service" : "Start service");

        String ip = primaryIp();
        String shownIp = ip.length() > 0 ? ip : "no IPv4";
        valueAddress.setText(shownIp);
        valuePort.setText(": " + BridgeService.port(this));
        codeCurl.setText("curl " + shownIp + ":" + BridgeService.port(this) + "/ping");

        boolean micGranted = MicRecorder.hasPermission(this);
        valueMic.setText(micGranted ? "Granted" : "Denied");
        valueMic.setTextColor(getColor(micGranted ? R.color.foreground : R.color.warning));

        boolean accessibilityEnabled = accessibilityEnabled();
        boolean connected = KeyService.isConnected();
        valueAccessibility.setText(connected ? "Connected"
                : accessibilityEnabled ? "Enabled" : "Disabled");
        valueAccessibility.setTextColor(getColor(connected ? R.color.foreground
                : accessibilityEnabled ? R.color.warning : R.color.destructive));

        KeyService ks = KeyService.getInstance();
        String foreground = ks != null ? ks.foregroundPackage() : "";
        valueForeground.setText(foreground != null && foreground.length() > 0 ? foreground : "—");

        valueUptime.setText(uptime.length() > 0 ? formatUptimeLong(BridgeService.uptimeMs()) : "—");

        // Healthy = bridge running and the accessibility key path is connected.
        boolean healthy = running && connected;
        healthyDot.setBackgroundResource(healthy ? R.drawable.dot_on : R.drawable.dot_off);
        healthyText.setText(healthy ? "Healthy" : running ? "Degraded" : "Stopped");
        healthyText.setTextColor(getColor(healthy ? R.color.success
                : running ? R.color.warning : R.color.destructive));
        healthyBadge.setBackgroundResource(healthy ? R.drawable.pill_success
                : running ? R.drawable.pill_warn : R.drawable.pill_danger);

        boolean paired = WhaleConfig.paired(this);
        connectedDot.setBackgroundResource(paired ? R.drawable.dot_on : R.drawable.dot_off);
        connectedText.setText(paired ? "CONNECTED" : "OFFLINE");
        connectedText.setTextColor(getColor(paired ? R.color.success : R.color.muted_foreground));
        connectedBadge.setBackgroundResource(paired
                ? R.drawable.pill_success : R.drawable.pill_plain);
    }

    /** Prefer the LAN address over a VPN/loopback interface. */
    private String primaryIp() {
        List<String> addresses = ApiHandler.ips();
        for (String address : addresses) {
            if (address.startsWith("192.168.") || address.startsWith("10.")) {
                return address;
            }
        }
        return addresses.isEmpty() ? "" : addresses.get(0);
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
        } catch (Throwable t) {
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
            toast("Could not open settings: " + t);
        }
    }

    /** "Test the mic": opens the assistant overlay (which starts listening). */
    private void openAssistant() {
        if (!MicRecorder.hasPermission(this)) {
            requestBridgePermissions();
            return;
        }
        try {
            startActivity(new Intent(this, WhaleActivity.class));
        } catch (Throwable t) {
            toast("Could not open the assistant: " + t);
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

    /** The mockup prints "2h 14m" with a space in the status card. */
    private String formatUptimeLong(long millis) {
        long seconds = millis / 1000;
        long minutes = seconds / 60;
        long hours = minutes / 60;
        if (hours > 0) {
            return hours + "h " + (minutes % 60) + "m";
        }
        if (minutes > 0) {
            return minutes + "m " + (seconds % 60) + "s";
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
