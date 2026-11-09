package com.jp.dshtv;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

/**
 * Restarts the bridge server after the TV boots so the Mac can drive it
 * without anyone picking up the remote.
 */
public class BootReceiver extends BroadcastReceiver {

    private static final String TAG = "DshtvBridge";

    @Override
    public void onReceive(Context context, Intent intent) {
        String action = intent != null ? intent.getAction() : null;
        if (!Intent.ACTION_BOOT_COMPLETED.equals(action)) {
            return;
        }
        Log.i(TAG, "BOOT_COMPLETED: starting bridge service");
        try {
            Intent service = new Intent(context, BridgeService.class);
            context.startForegroundService(service);
        } catch (Throwable t) {
            Log.i(TAG, "could not start bridge service at boot: " + t);
        }
    }
}
