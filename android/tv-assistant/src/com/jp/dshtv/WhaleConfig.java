package com.jp.dshtv;

import android.content.Context;
import android.content.SharedPreferences;

/** Paired Mac settings; build-time values act as defaults for testing. */
public final class WhaleConfig {

    private static final String PREFS = "whale";

    private WhaleConfig() {
    }

    private static SharedPreferences prefs(Context ctx) {
        return ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public static String host(Context ctx) {
        return prefs(ctx).getString("host", ctx.getString(R.string.whale_host));
    }

    public static String port(Context ctx) {
        return prefs(ctx).getString("port", ctx.getString(R.string.whale_port));
    }

    public static String token(Context ctx) {
        return prefs(ctx).getString("token", ctx.getString(R.string.whale_token));
    }

    public static boolean paired(Context ctx) {
        String t = token(ctx);
        return prefs(ctx).getBoolean("paired", false) && t != null && !t.isEmpty();
    }

    public static void save(Context ctx, String host, String port, String token) {
        prefs(ctx).edit()
                .putString("host", host)
                .putString("port", port)
                .putString("token", token)
                .putBoolean("paired", true)
                .apply();
    }
}
