package com.jp.dshtv;

import android.content.Context;
import android.content.Intent;
import android.media.AudioManager;
import android.net.Uri;
import android.os.Build;
import android.os.PowerManager;
import android.util.Log;

import java.net.Inet4Address;
import java.net.InetAddress;
import java.net.NetworkInterface;
import java.util.ArrayList;
import java.util.Enumeration;
import java.util.List;
import java.util.Locale;

/**
 * Routes HTTP requests to the bridge features and renders the JSON contract
 * the Mac mini expects. Every successful response carries "ok": true.
 */
public final class ApiHandler {

    private static final String TAG = "DshtvBridge";
    private static final String APP = "dshtv";
    private static final int VERSION = 1;

    private ApiHandler() {
    }

    public static Http.Response handle(Context ctx, Http.Request req) {
        String path = req.path;
        try {
            if ("/ping".equals(path)) {
                return ping();
            }
            if ("/info".equals(path)) {
                return info(ctx);
            }
            if ("/state".equals(path)) {
                return state(ctx);
            }
            if ("/key".equals(path)) {
                return key(ctx, req);
            }
            if ("/text".equals(path)) {
                return text(ctx, req);
            }
            if ("/launch".equals(path)) {
                return launch(ctx, req);
            }
            if ("/apps".equals(path)) {
                return apps(ctx);
            }
            if ("/screenshot".equals(path)) {
                return screenshot(ctx, req);
            }
            if ("/voice".equals(path)) {
                return voice(ctx);
            }
            if ("/speak".equals(path)) {
                return speak(ctx, req);
            }
            if ("/mic".equals(path)) {
                return mic(ctx, req);
            }
            if ("/open".equals(path)) {
                return open(ctx, req);
            }
            if ("/volume".equals(path)) {
                return volume(ctx, req);
            }
            return Http.Response.error(404, "not_found");
        } catch (Throwable t) {
            Log.i(TAG, "api error on " + path + ": " + t);
            return Http.Response.error(500, "internal_error");
        }
    }

    private static Http.Response ping() {
        Json.Obj out = new Json.Obj();
        out.put("ok", Boolean.TRUE);
        out.put("app", APP);
        out.put("version", Integer.valueOf(VERSION));
        out.put("now", Long.valueOf(System.currentTimeMillis()));
        return Http.Response.json(200, out);
    }

    private static Http.Response info(Context ctx) {
        KeyService ks = KeyService.getInstance();
        Json.Obj out = new Json.Obj();
        out.put("ok", Boolean.TRUE);
        out.put("app", APP);
        out.put("version", Integer.valueOf(VERSION));
        out.put("sdk", Integer.valueOf(Build.VERSION.SDK_INT));
        out.put("model", safe(Build.MODEL));
        out.put("brand", safe(Build.BRAND));

        Json.Arr ips = new Json.Arr();
        List<String> addresses = ips();
        for (int i = 0; i < addresses.size(); i++) {
            ips.add(addresses.get(i));
        }
        out.put("ips", ips);
        out.put("port", Integer.valueOf(BridgeService.port(ctx)));
        out.put("serverRunning", Boolean.valueOf(BridgeService.isRunning()));
        out.put("accessibility", Boolean.valueOf(ks != null));
        out.put("foregroundPackage", ks != null ? safe(ks.foregroundPackage()) : "");
        out.put("screenOn", Boolean.valueOf(screenOn(ctx)));
        out.put("tokenRequired",
                Boolean.valueOf(BridgeService.token(ctx).length() > 0));
        out.put("micPermission", Boolean.valueOf(MicRecorder.hasPermission(ctx)));
        out.put("uptimeMs", Long.valueOf(BridgeService.uptimeMs()));
        return Http.Response.json(200, out);
    }

    private static Http.Response state(Context ctx) {
        KeyService ks = KeyService.getInstance();
        AudioManager am = (AudioManager) ctx.getSystemService(Context.AUDIO_SERVICE);
        int volume = 0;
        int max = 0;
        boolean muted = false;
        if (am != null) {
            try {
                volume = am.getStreamVolume(AudioManager.STREAM_MUSIC);
                max = am.getStreamMaxVolume(AudioManager.STREAM_MUSIC);
                muted = am.isStreamMute(AudioManager.STREAM_MUSIC);
            } catch (Throwable t) {
                Log.i(TAG, "state audio failed: " + t);
            }
        }
        Json.Obj out = new Json.Obj();
        out.put("ok", Boolean.TRUE);
        out.put("foregroundPackage", ks != null ? safe(ks.foregroundPackage()) : "");
        out.put("foregroundClass", ks != null ? safe(ks.foregroundClass()) : "");
        out.put("screenOn", Boolean.valueOf(screenOn(ctx)));
        out.put("accessibility", Boolean.valueOf(ks != null));
        out.put("musicVolume", Integer.valueOf(volume));
        out.put("musicMax", Integer.valueOf(max));
        out.put("muted", Boolean.valueOf(muted));
        return Http.Response.json(200, out);
    }

    private static Http.Response key(Context ctx, Http.Request req) {
        String code = req.q("code");
        if (code == null || code.trim().length() == 0) {
            return Http.Response.error(400, "missing_code");
        }
        code = code.trim();
        int n = parseIntRange(req.q("n"), 1, 1, 20);
        int result = KeyMap.RESULT_ERROR;
        for (int i = 0; i < n; i++) {
            result = KeyMap.execute(ctx, code);
            if (result != KeyMap.RESULT_OK) {
                break;
            }
            if (i + 1 < n) {
                try {
                    Thread.sleep(60);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        }
        if (result == KeyMap.RESULT_OK) {
            return Http.Response.json(200, new Json.Obj()
                    .put("ok", Boolean.TRUE)
                    .put("code", code)
                    .put("n", Integer.valueOf(n)));
        }
        if (result == KeyMap.RESULT_UNSUPPORTED) {
            return Http.Response.json(501, new Json.Obj()
                    .put("ok", Boolean.FALSE)
                    .put("error", "unsupported")
                    .put("code", code));
        }
        if (result == KeyMap.RESULT_NO_ACCESSIBILITY) {
            return Http.Response.json(503, new Json.Obj()
                    .put("ok", Boolean.FALSE)
                    .put("error", "accessibility_service_not_connected")
                    .put("code", code));
        }
        return Http.Response.json(500, new Json.Obj()
                .put("ok", Boolean.FALSE)
                .put("error", "key_failed")
                .put("code", code));
    }

    private static Http.Response text(Context ctx, Http.Request req) {
        KeyService ks = KeyService.getInstance();
        if (ks == null) {
            return Http.Response.json(503, new Json.Obj()
                    .put("ok", Boolean.FALSE)
                    .put("error", "accessibility_service_not_connected"));
        }
        String value = req.q("q");
        if (value == null) {
            value = "";
        }
        if (!ks.setFocusedText(value)) {
            return Http.Response.error(409, "no focused editable field");
        }
        if (isTrue(req.q("enter"))) {
            ks.perform(android.accessibilityservice.AccessibilityService
                    .GLOBAL_ACTION_DPAD_CENTER);
        }
        return Http.Response.json(200, new Json.Obj().put("ok", Boolean.TRUE));
    }

    private static Http.Response launch(Context ctx, Http.Request req) {
        String pkg = req.q("pkg");
        String app = req.q("app");
        String url = req.q("url");

        if (pkg != null && pkg.trim().length() > 0) {
            return launchResult(AppIndex.launch(ctx, pkg), pkg);
        }
        if (app != null && app.trim().length() > 0) {
            return launchResult(AppIndex.launch(ctx, app), app);
        }
        if (url != null && url.trim().length() > 0) {
            AppIndex.LaunchResult result = AppIndex.launchUrl(ctx, url);
            if (result.ok) {
                return Http.Response.json(200, new Json.Obj()
                        .put("ok", Boolean.TRUE)
                        .put("url", url.trim()));
            }
            return Http.Response.json(409, new Json.Obj()
                    .put("ok", Boolean.FALSE)
                    .put("error", result.error != null ? result.error : "launch_failed")
                    .put("detail", safe(result.detail)));
        }
        return Http.Response.error(400, "pkg_app_or_url_required");
    }

    private static Http.Response launchResult(AppIndex.LaunchResult result, String query) {
        if (result.ok) {
            Json.Obj out = new Json.Obj();
            out.put("ok", Boolean.TRUE);
            out.put("package", result.pkg != null ? result.pkg : query.trim());
            out.put("activity", result.activity != null ? result.activity : "");
            return Http.Response.json(200, out);
        }
        int status;
        if ("app_not_found".equals(result.error)) {
            status = 404;
        } else if ("activity_not_found".equals(result.error)) {
            status = 404;
        } else if ("bad_request".equals(result.error)) {
            status = 400;
        } else {
            status = 409;
        }
        Json.Obj out = new Json.Obj();
        out.put("ok", Boolean.FALSE);
        out.put("error", result.error != null ? result.error : "launch_failed");
        out.put("detail", safe(result.detail));
        return Http.Response.json(status, out);
    }

    private static Http.Response apps(Context ctx) {
        List<AppIndex.Entry> list = AppIndex.list(ctx);
        Json.Arr arr = new Json.Arr();
        for (int i = 0; i < list.size(); i++) {
            AppIndex.Entry entry = list.get(i);
            arr.add(new Json.Obj()
                    .put("package", entry.pkg)
                    .put("label", entry.label));
        }
        return Http.Response.json(200, new Json.Obj()
                .put("ok", Boolean.TRUE)
                .put("apps", arr));
    }

    private static Http.Response screenshot(Context ctx, Http.Request req) {
        if (Build.VERSION.SDK_INT < 30) {
            return Http.Response.json(503, new Json.Obj()
                    .put("ok", Boolean.FALSE)
                    .put("error", "screenshot_requires_api30"));
        }
        KeyService ks = KeyService.getInstance();
        if (ks == null) {
            return Http.Response.json(503, new Json.Obj()
                    .put("ok", Boolean.FALSE)
                    .put("error", "accessibility_service_not_connected"));
        }
        int quality = parseIntRange(req.q("quality"), 85, 1, 100);
        try {
            byte[] jpeg = ks.screenshotJpeg(quality);
            if (jpeg == null || jpeg.length == 0) {
                return Http.Response.json(503, new Json.Obj()
                        .put("ok", Boolean.FALSE)
                        .put("error", "screenshot_failed"));
            }
            return Http.Response.bytes(200, "image/jpeg", jpeg);
        } catch (Throwable t) {
            Log.i(TAG, "screenshot failed: " + t);
            return Http.Response.json(503, new Json.Obj()
                    .put("ok", Boolean.FALSE)
                    .put("error", "screenshot_failed")
                    .put("detail", safe(String.valueOf(t.getMessage()))));
        }
    }

    private static Http.Response voice(Context ctx) {
        String via = null;
        String detail = null;
        // On Google TV the ASSIST intent resolves to Katniss (the dashboard /
        // assistant trampoline); VOICE_COMMAND usually has no handler there.
        String[] actions = new String[] { Intent.ACTION_ASSIST, Intent.ACTION_VOICE_COMMAND };
        for (int i = 0; i < actions.length; i++) {
            String action = actions[i];
            try {
                Intent intent = new Intent(action);
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                AppIndex.startIntent(ctx, intent);
                via = Intent.ACTION_ASSIST.equals(action) ? "assist" : "voice_command";
                Log.i(TAG, "voice: started " + action);
                break;
            } catch (Throwable t) {
                detail = String.valueOf(t);
                Log.i(TAG, "voice: " + action + " failed: " + t);
            }
        }
        if (via != null) {
            return Http.Response.json(200, new Json.Obj()
                    .put("ok", Boolean.TRUE)
                    .put("via", via));
        }
        return Http.Response.json(500, new Json.Obj()
                .put("ok", Boolean.FALSE)
                .put("error", "voice_not_available")
                .put("detail", safe(detail)));
    }

    private static Http.Response speak(Context ctx, Http.Request req) {
        String text = req.q("text");
        if (text == null) {
            text = req.q("q");
        }
        if (text == null || text.trim().length() == 0) {
            return Http.Response.error(400, "missing_text");
        }
        try {
            Tts tts = Tts.get(ctx);
            if (!tts.speak(text)) {
                return Http.Response.error(500, "tts_speak_failed");
            }
            return Http.Response.json(200, new Json.Obj().put("ok", Boolean.TRUE));
        } catch (Throwable t) {
            Log.i(TAG, "speak failed: " + t);
            return Http.Response.json(500, new Json.Obj()
                    .put("ok", Boolean.FALSE)
                    .put("error", "tts_init_failed")
                    .put("detail", safe(String.valueOf(t.getMessage()))));
        }
    }

    private static Http.Response mic(Context ctx, Http.Request req) {
        if (!MicRecorder.hasPermission(ctx)) {
            return Http.Response.json(403, new Json.Obj()
                    .put("ok", Boolean.FALSE)
                    .put("error", "record_audio_permission_denied"));
        }
        int seconds = parseIntRange(req.q("seconds"), 5, 1, 30);
        String source = req.q("source");
        if (source == null || source.trim().length() == 0) {
            source = "voice";
        }
        try {
            byte[] wav = MicRecorder.recordWav(ctx, seconds, source);
            return Http.Response.bytes(200, "audio/wav", wav);
        } catch (SecurityException e) {
            return Http.Response.json(403, new Json.Obj()
                    .put("ok", Boolean.FALSE)
                    .put("error", "record_audio_permission_denied"));
        } catch (Throwable t) {
            Log.i(TAG, "mic failed: " + t);
            return Http.Response.json(500, new Json.Obj()
                    .put("ok", Boolean.FALSE)
                    .put("error", "mic_failed")
                    .put("detail", safe(String.valueOf(t.getMessage()))));
        }
    }

    private static Http.Response open(Context ctx, Http.Request req) {
        String url = req.q("url");
        if (url == null || url.trim().length() == 0) {
            return Http.Response.error(400, "missing_url");
        }
        try {
            Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url.trim()));
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            AppIndex.startIntent(ctx, intent);
            return Http.Response.json(200, new Json.Obj().put("ok", Boolean.TRUE));
        } catch (Throwable t) {
            Log.i(TAG, "open failed: " + t);
            return Http.Response.json(409, new Json.Obj()
                    .put("ok", Boolean.FALSE)
                    .put("error", "open_failed")
                    .put("detail", safe(String.valueOf(t))));
        }
    }

    private static Http.Response volume(Context ctx, Http.Request req) {
        AudioManager am = (AudioManager) ctx.getSystemService(Context.AUDIO_SERVICE);
        if (am == null) {
            return Http.Response.error(500, "audio_unavailable");
        }
        try {
            int max = am.getStreamMaxVolume(AudioManager.STREAM_MUSIC);
            String level = req.q("level");
            String delta = req.q("delta");
            if (level != null) {
                int percent = parseIntRange(level, -1, 0, 100);
                if (percent < 0) {
                    return Http.Response.error(400, "bad_level");
                }
                int target = (int) Math.round(percent * (max / 100.0));
                target = clamp(target, 0, max);
                am.setStreamVolume(AudioManager.STREAM_MUSIC, target,
                        AudioManager.FLAG_SHOW_UI);
            } else if (delta != null) {
                int d = parseInt(delta, 0);
                int current = am.getStreamVolume(AudioManager.STREAM_MUSIC);
                int target = clamp(current + d, 0, max);
                am.setStreamVolume(AudioManager.STREAM_MUSIC, target,
                        AudioManager.FLAG_SHOW_UI);
            }
            return Http.Response.json(200, new Json.Obj()
                    .put("ok", Boolean.TRUE)
                    .put("volume", Integer.valueOf(
                            am.getStreamVolume(AudioManager.STREAM_MUSIC)))
                    .put("max", Integer.valueOf(max)));
        } catch (Throwable t) {
            Log.i(TAG, "volume failed: " + t);
            return Http.Response.json(500, new Json.Obj()
                    .put("ok", Boolean.FALSE)
                    .put("error", "volume_failed")
                    .put("detail", safe(String.valueOf(t))));
        }
    }

    // ---------------------------------------------------------------- utils

    private static boolean screenOn(Context ctx) {
        try {
            PowerManager pm = (PowerManager) ctx.getSystemService(Context.POWER_SERVICE);
            return pm != null && pm.isInteractive();
        } catch (Throwable t) {
            return false;
        }
    }

    /** Non-loopback IPv4 addresses of this device, most useful first. */
    public static List<String> ips() {
        List<String> out = new ArrayList<String>();
        try {
            Enumeration<NetworkInterface> interfaces = NetworkInterface.getNetworkInterfaces();
            if (interfaces == null) {
                return out;
            }
            while (interfaces.hasMoreElements()) {
                NetworkInterface networkInterface = interfaces.nextElement();
                if (networkInterface == null || !networkInterface.isUp()
                        || networkInterface.isLoopback()) {
                    continue;
                }
                Enumeration<InetAddress> addresses = networkInterface.getInetAddresses();
                while (addresses.hasMoreElements()) {
                    InetAddress address = addresses.nextElement();
                    if (!(address instanceof Inet4Address)) {
                        continue;
                    }
                    String ip = address.getHostAddress();
                    if (ip == null || ip.startsWith("127.") || ip.startsWith("169.254.")) {
                        continue;
                    }
                    if (!out.contains(ip)) {
                        out.add(ip);
                    }
                }
            }
        } catch (Throwable t) {
            Log.i(TAG, "ips failed: " + t);
        }
        return out;
    }

    private static int parseInt(String value, int def) {
        if (value == null) {
            return def;
        }
        try {
            return Integer.parseInt(value.trim());
        } catch (Throwable t) {
            return def;
        }
    }

    private static int parseIntRange(String value, int def, int min, int max) {
        int parsed = parseInt(value, def);
        return clamp(parsed, min, max);
    }

    private static int clamp(int value, int min, int max) {
        if (value < min) {
            return min;
        }
        if (value > max) {
            return max;
        }
        return value;
    }

    private static boolean isTrue(String value) {
        if (value == null) {
            return false;
        }
        String v = value.trim().toLowerCase(Locale.US);
        return v.equals("1") || v.equals("true") || v.equals("yes") || v.equals("on");
    }

    private static String safe(String value) {
        return value != null ? value : "";
    }
}
