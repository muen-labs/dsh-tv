package com.jp.dshtv;

import android.content.Context;
import android.provider.Settings;

/**
 * Friendly identity of this TV, used by the Bridge home "Paired with" row and
 * the pairing screen's device chip. The design copy says "Living Room TV ·
 * onn. 4K Pro", but the second box is an "onn. 4K Plus Streaming", so both
 * labels now come from the device instead of the mockup.
 */
public final class DeviceInfo {

    private DeviceInfo() {
    }

    /** User-set name (Settings.Global.device_name), else the model, else "Android TV". */
    public static String name(Context ctx) {
        String name = "";
        try {
            name = clean(Settings.Global.getString(ctx.getContentResolver(), "device_name"));
        } catch (Throwable ignored) {
        }
        if (name.length() == 0) {
            name = model();
        }
        if (name.length() == 0) {
            name = "Android TV";
        }
        return name;
    }

    /** Build.MODEL, e.g. "onn. Streaming Device 4K pro". */
    public static String model() {
        return clean(android.os.Build.MODEL);
    }

    /** Show the model only when it adds information ("name · model"). */
    public static boolean nameDiffersFromModel(Context ctx) {
        String name = name(ctx);
        String model = model();
        return model.length() > 0 && !model.equalsIgnoreCase(name);
    }

    private static String clean(String value) {
        return value == null ? "" : value.trim();
    }
}
