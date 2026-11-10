package com.jp.dshtv;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.AccessibilityServiceInfo;
import android.graphics.Bitmap;
import android.hardware.HardwareBuffer;
import android.os.Build;
import android.os.Bundle;
import android.util.Log;
import android.view.Display;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import android.view.accessibility.AccessibilityWindowInfo;

import java.io.ByteArrayOutputStream;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

/**
 * Accessibility service that gives the bridge real remote-control power:
 * global D-pad/Back/Home actions, text entry into the focused field,
 * screenshots, and foreground app tracking.
 */
public class KeyService extends AccessibilityService {

    private static final String TAG = "DshtvBridge";

    private static volatile KeyService instance;

    private volatile String foregroundPkg = "";
    private volatile String foregroundClass = "";
    /** Last foreground package that was NOT us (used by the overlay app chip,
     *  because by the time our window is up the tracker already sees us). */
    private volatile String lastExternalPkg = "";

    public static KeyService getInstance() {
        return instance;
    }

    public static boolean isConnected() {
        return instance != null;
    }

    /** Last non-DSH app that was foreground (the app the assistant is over). */
    public String lastExternalPackage() {
        return lastExternalPkg;
    }

    /**
     * Re-scan the interactive windows for the app behind us. Called when the
     * assistant overlay opens so the app chip names the app it is over even if
     * the service was bound after that app was already in front.
     */
    public String refreshExternalPackage() {
        try {
            java.util.List<AccessibilityWindowInfo> windows = getWindows();
            if (windows != null) {
                for (int i = 0; i < windows.size(); i++) {
                    AccessibilityWindowInfo window = windows.get(i);
                    if (window == null
                            || window.getType() != AccessibilityWindowInfo.TYPE_APPLICATION) {
                        continue;
                    }
                    AccessibilityNodeInfo root = window.getRoot();
                    if (root == null) {
                        continue;
                    }
                    try {
                        CharSequence pkg = root.getPackageName();
                        if (pkg != null && !pkg.toString().equals(getPackageName())) {
                            lastExternalPkg = pkg.toString();
                            return lastExternalPkg;
                        }
                    } finally {
                        try {
                            root.recycle();
                        } catch (Throwable ignored) {
                        }
                    }
                }
            }
        } catch (Throwable t) {
            Log.i(TAG, "refreshExternalPackage failed: " + t);
        }
        return lastExternalPkg;
    }

    @Override
    protected void onServiceConnected() {
        super.onServiceConnected();
        instance = this;
        try {
            AccessibilityServiceInfo info = getServiceInfo();
            if (info != null) {
                info.flags |= AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS;
                setServiceInfo(info);
            }
        } catch (Throwable t) {
            Log.i(TAG, "KeyService setServiceInfo failed: " + t);
        }
        try {
            AccessibilityNodeInfo root = getRootInActiveWindow();
            if (root != null) {
                try {
                    CharSequence pkg = root.getPackageName();
                    if (pkg != null && !pkg.toString().equals(getPackageName())) {
                        lastExternalPkg = pkg.toString();
                    }
                } finally {
                    try {
                        root.recycle();
                    } catch (Throwable ignored) {
                    }
                }
            }
        } catch (Throwable ignored) {
        }
        Log.i(TAG, "KeyService connected");
    }

    @Override
    public void onDestroy() {
        if (instance == this) {
            instance = null;
        }
        Log.i(TAG, "KeyService destroyed");
        super.onDestroy();
    }

    @Override
    public void onInterrupt() {
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        if (event == null) {
            return;
        }
        try {
            int type = event.getEventType();
            if (type == AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED) {
                CharSequence pkg = event.getPackageName();
                if (pkg != null) {
                    foregroundPkg = pkg.toString();
                    if (!foregroundPkg.equals(getPackageName())) {
                        lastExternalPkg = foregroundPkg;
                    }
                }
                CharSequence cls = event.getClassName();
                if (cls != null) {
                    foregroundClass = cls.toString();
                }
            } else if (type == AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED) {
                CharSequence pkg = event.getPackageName();
                if (pkg != null && pkg.length() > 0) {
                    foregroundPkg = pkg.toString();
                }
            }
        } catch (Throwable t) {
            Log.i(TAG, "onAccessibilityEvent: " + t);
        }
    }

    public String foregroundPackage() {
        return foregroundPkg;
    }

    public String foregroundClass() {
        return foregroundClass;
    }

    public boolean perform(int globalAction) {
        try {
            return performGlobalAction(globalAction);
        } catch (Throwable t) {
            Log.i(TAG, "performGlobalAction(" + globalAction + ") failed: " + t);
            return false;
        }
    }

    /** Put text into the currently focused editable field. */
    public boolean setFocusedText(String text) {
        AccessibilityNodeInfo root = null;
        AccessibilityNodeInfo target = null;
        try {
            root = getRootInActiveWindow();
            if (root == null) {
                Log.i(TAG, "setFocusedText: no active window");
                return false;
            }
            target = root.findFocus(AccessibilityNodeInfo.FOCUS_INPUT);
            if (target == null) {
                target = root.findFocus(AccessibilityNodeInfo.FOCUS_ACCESSIBILITY);
            }
            if (target == null) {
                Log.i(TAG, "setFocusedText: no focused node");
                return false;
            }
            if (!target.isEditable()) {
                Log.i(TAG, "setFocusedText: focused node is not editable");
                return false;
            }
            if (!target.isFocused()) {
                target.performAction(AccessibilityNodeInfo.ACTION_FOCUS);
            }
            Bundle args = new Bundle();
            args.putCharSequence(
                    AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE,
                    text != null ? text : "");
            boolean ok = target.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, args);
            Log.i(TAG, "setFocusedText len=" + (text != null ? text.length() : 0) + " ok=" + ok);
            return ok;
        } catch (Throwable t) {
            Log.i(TAG, "setFocusedText failed: " + t);
            return false;
        } finally {
            recycleQuietly(target);
            recycleQuietly(root);
        }
    }

    private static void recycleQuietly(AccessibilityNodeInfo node) {
        if (node == null) {
            return;
        }
        try {
            node.recycle();
        } catch (Throwable ignored) {
        }
    }

    /**
     * Capture the current display as a software Bitmap. Requires Android 11
     * (API 30) and the accessibility service's canTakeScreenshot capability.
     * Used by the assistant overlay to fake a real background blur (the box
     * has no cross-window blur support).
     */
    public Bitmap screenshotBitmap(final long timeoutSeconds) throws Exception {
        if (Build.VERSION.SDK_INT < 30) {
            throw new Exception("screenshot requires Android 11 (API 30) or newer");
        }
        final CountDownLatch latch = new CountDownLatch(1);
        final Object[] result = new Object[2]; // [0] Bitmap, [1] String error

        try {
            takeScreenshot(Display.DEFAULT_DISPLAY, getMainExecutor(),
                    new AccessibilityService.TakeScreenshotCallback() {
                        @Override
                        public void onSuccess(AccessibilityService.ScreenshotResult screenshot) {
                            HardwareBuffer buffer = null;
                            try {
                                buffer = screenshot.getHardwareBuffer();
                                Bitmap hardware = Bitmap.wrapHardwareBuffer(
                                        buffer, screenshot.getColorSpace());
                                if (hardware == null) {
                                    result[1] = "wrapHardwareBuffer returned null";
                                    return;
                                }
                                Bitmap soft = hardware.copy(Bitmap.Config.ARGB_8888, false);
                                if (soft == null) {
                                    result[1] = "bitmap copy failed";
                                    return;
                                }
                                result[0] = soft;
                            } catch (Throwable t) {
                                result[1] = "screenshot error: " + t;
                                Log.i(TAG, "screenshot onSuccess error: " + t);
                            } finally {
                                if (buffer != null) {
                                    try {
                                        buffer.close();
                                    } catch (Throwable ignored) {
                                    }
                                }
                                latch.countDown();
                            }
                        }

                        @Override
                        public void onFailure(int errorCode) {
                            result[1] = "takeScreenshot failed, errorCode=" + errorCode;
                            Log.i(TAG, "takeScreenshot onFailure code=" + errorCode);
                            latch.countDown();
                        }
                    });
        } catch (Throwable t) {
            throw new Exception("takeScreenshot call failed: " + t);
        }

        try {
            if (!latch.await(Math.max(1, timeoutSeconds), TimeUnit.SECONDS)) {
                throw new Exception("screenshot timed out");
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new Exception("screenshot interrupted");
        }

        if (result[0] instanceof Bitmap) {
            return (Bitmap) result[0];
        }
        throw new Exception(result[1] != null ? (String) result[1] : "screenshot failed");
    }

    /**
     * Capture the current display as a JPEG (used by the bridge HTTP API).
     */
    public byte[] screenshotJpeg(final int quality) throws Exception {
        Bitmap soft = screenshotBitmap(10);
        try {
            ByteArrayOutputStream out = new ByteArrayOutputStream(256 * 1024);
            soft.compress(Bitmap.CompressFormat.JPEG, quality, out);
            return out.toByteArray();
        } finally {
            try {
                soft.recycle();
            } catch (Throwable ignored) {
            }
        }
    }
}
