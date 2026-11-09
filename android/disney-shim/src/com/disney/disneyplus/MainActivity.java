package com.disney.disneyplus;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;

/**
 * Shim that claims the package name the Onn remote's Disney+ button launches
 * (GlobalKey hardcodes com.disney.disneyplus). The real Disney+ app is not
 * installed on this unit, so pressing the button resolves here and we hand off
 * to Whale-chan.
 */
public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        Intent whale = new Intent(Intent.ACTION_MAIN);
        whale.setClassName("com.jp.dshtv", "com.jp.dshtv.WhaleActivity");
        whale.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        try {
            startActivity(whale);
        } catch (Throwable ignored) {
            // Whale-chan missing: nothing else to do
        }
        finish();
    }
}
