package com.jp.dshtv;

import android.accessibilityservice.AccessibilityService;
import android.content.Context;
import android.media.AudioManager;
import android.os.Build;
import android.util.Log;
import android.view.KeyEvent;

/**
 * Maps remote-control names ("up", "playpause", "volup", ...) onto
 * accessibility global actions, media key events and stream volume changes.
 */
public final class KeyMap {

    private static final String TAG = "DshtvBridge";

    /** Action handled successfully. */
    public static final int RESULT_OK = 0;
    /** Known name but not supported by this app (menu, power, ...). */
    public static final int RESULT_UNSUPPORTED = 1;
    /** Needs the accessibility service, which is not connected. */
    public static final int RESULT_NO_ACCESSIBILITY = 2;
    /** The platform rejected the action. */
    public static final int RESULT_ERROR = 3;

    private KeyMap() {
    }

    public static int execute(Context ctx, String code) {
        String c = code == null ? "" : code.trim().toLowerCase(java.util.Locale.US);
        if (c.length() == 0) {
            return RESULT_UNSUPPORTED;
        }

        int globalAction = -1;
        if (c.equals("up")) {
            globalAction = AccessibilityService.GLOBAL_ACTION_DPAD_UP;
        } else if (c.equals("down")) {
            globalAction = AccessibilityService.GLOBAL_ACTION_DPAD_DOWN;
        } else if (c.equals("left")) {
            globalAction = AccessibilityService.GLOBAL_ACTION_DPAD_LEFT;
        } else if (c.equals("right")) {
            globalAction = AccessibilityService.GLOBAL_ACTION_DPAD_RIGHT;
        } else if (c.equals("center") || c.equals("ok") || c.equals("select")) {
            globalAction = AccessibilityService.GLOBAL_ACTION_DPAD_CENTER;
        } else if (c.equals("back")) {
            globalAction = AccessibilityService.GLOBAL_ACTION_BACK;
        } else if (c.equals("home")) {
            globalAction = AccessibilityService.GLOBAL_ACTION_HOME;
        } else if (c.equals("recents")) {
            globalAction = AccessibilityService.GLOBAL_ACTION_RECENTS;
        } else if (c.equals("notifications")) {
            globalAction = AccessibilityService.GLOBAL_ACTION_NOTIFICATIONS;
        } else if (c.equals("sleep")) {
            if (Build.VERSION.SDK_INT >= 28) {
                globalAction = AccessibilityService.GLOBAL_ACTION_LOCK_SCREEN;
            } else {
                return RESULT_UNSUPPORTED;
            }
        }

        if (globalAction != -1) {
            KeyService ks = KeyService.getInstance();
            if (ks == null) {
                return RESULT_NO_ACCESSIBILITY;
            }
            return ks.perform(globalAction) ? RESULT_OK : RESULT_ERROR;
        }

        if (c.equals("playpause")) {
            return mediaKey(ctx, KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE);
        } else if (c.equals("play")) {
            return mediaKey(ctx, KeyEvent.KEYCODE_MEDIA_PLAY);
        } else if (c.equals("pause")) {
            return mediaKey(ctx, KeyEvent.KEYCODE_MEDIA_PAUSE);
        } else if (c.equals("next")) {
            return mediaKey(ctx, KeyEvent.KEYCODE_MEDIA_NEXT);
        } else if (c.equals("prev")) {
            return mediaKey(ctx, KeyEvent.KEYCODE_MEDIA_PREVIOUS);
        } else if (c.equals("rewind")) {
            return mediaKey(ctx, KeyEvent.KEYCODE_MEDIA_REWIND);
        } else if (c.equals("fastforward")) {
            return mediaKey(ctx, KeyEvent.KEYCODE_MEDIA_FAST_FORWARD);
        }

        if (c.equals("volup")) {
            return adjustVolume(ctx, AudioManager.ADJUST_RAISE);
        } else if (c.equals("voldown")) {
            return adjustVolume(ctx, AudioManager.ADJUST_LOWER);
        } else if (c.equals("mute")) {
            return adjustVolume(ctx, AudioManager.ADJUST_TOGGLE_MUTE);
        }

        // menu, power, info, guide and anything unknown are not available to
        // a normal (non-system) app; the Mac side falls back to adb.
        return RESULT_UNSUPPORTED;
    }

    private static int mediaKey(Context ctx, int keyCode) {
        try {
            AudioManager am = (AudioManager) ctx.getSystemService(Context.AUDIO_SERVICE);
            if (am == null) {
                return RESULT_ERROR;
            }
            am.dispatchMediaKeyEvent(new KeyEvent(KeyEvent.ACTION_DOWN, keyCode));
            am.dispatchMediaKeyEvent(new KeyEvent(KeyEvent.ACTION_UP, keyCode));
            return RESULT_OK;
        } catch (Throwable t) {
            Log.i(TAG, "dispatchMediaKeyEvent(" + keyCode + ") failed: " + t);
            return RESULT_ERROR;
        }
    }

    private static int adjustVolume(Context ctx, int direction) {
        try {
            AudioManager am = (AudioManager) ctx.getSystemService(Context.AUDIO_SERVICE);
            if (am == null) {
                return RESULT_ERROR;
            }
            am.adjustStreamVolume(AudioManager.STREAM_MUSIC, direction,
                    AudioManager.FLAG_SHOW_UI);
            return RESULT_OK;
        } catch (Throwable t) {
            Log.i(TAG, "adjustStreamVolume(" + direction + ") failed: " + t);
            return RESULT_ERROR;
        }
    }
}
