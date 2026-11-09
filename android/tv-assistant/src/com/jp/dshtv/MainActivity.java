package com.jp.dshtv;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.res.ColorStateList;
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
    private TextView valueAddress;
    private TextView valueMic;
    private TextView valueAccessibility;
    private TextView valueForeground;
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
        valueAddress = (TextView) findViewById(R.id.value_address);
        valueMic = (TextView) findViewById(R.id.value_mic);
        valueAccessibility = (TextView) findViewById(R.id.value_accessibility);
        valueForeground = (TextView) findViewById(R.id.value_foreground);

        Button pair = (Button) findViewById(R.id.btn_pair);
        Button start = (Button) findViewById(R.id.btn_start);
        Button stop = (Button) findViewById(R.id.btn_stop);
        Button accessibility = (Button) findViewById(R.id.btn_accessibility);
        Button mic = (Button) findViewById(R.id.btn_mic);
        Button refresh = (Button) findViewById(R.id.btn_refresh);

        pair.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                startActivity(new Intent(MainActivity.this, PairingActivity.class));
            }
        });
        start.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                startBridgeService();
                toast("Bridge service starting");
                refreshStatus();
            }
        });
        stop.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                stopBridgeService();
                toast("Bridge service stopped");
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

        for (Button b : new Button[]{pair, start, stop, accessibility, mic, refresh}) {
            styleFocus(b);
        }
        pair.requestFocus();
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
        statusDot.setBackgroundResource(running ? R.drawable.dot_on : R.drawable.dot_off);
        statusText.setText(running
                ? "RUNNING · " + formatUptime(BridgeService.uptimeMs())
                : "STOPPED");
        statusText.setTextColor(getColor(running ? R.color.success : R.color.destructive));

        String ip = primaryIp();
        valueAddress.setText((ip.length() > 0 ? ip : "no IPv4") + " : " + BridgeService.port(this));

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
