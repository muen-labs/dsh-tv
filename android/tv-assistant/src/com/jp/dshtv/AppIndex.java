package com.jp.dshtv;

import android.content.ActivityNotFoundException;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.net.Uri;
import android.util.Log;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

/**
 * Index of launchable apps (TV leanback + regular launcher) and helpers to
 * launch by package name, fuzzy label or URL.
 */
public final class AppIndex {

    private static final String TAG = "DshtvBridge";

    private AppIndex() {
    }

    public static final class Entry {
        public final String pkg;
        public final String label;
        public final String activity;

        Entry(String pkg, String label, String activity) {
            this.pkg = pkg;
            this.label = label;
            this.activity = activity;
        }
    }

    public static final class LaunchResult {
        public final boolean ok;
        public final String pkg;
        public final String activity;
        public final String error;
        public final String detail;

        private LaunchResult(boolean ok, String pkg, String activity,
                String error, String detail) {
            this.ok = ok;
            this.pkg = pkg;
            this.activity = activity;
            this.error = error;
            this.detail = detail;
        }

        static LaunchResult ok(String pkg, String activity) {
            return new LaunchResult(true, pkg, activity, null, null);
        }

        static LaunchResult fail(String error, String detail) {
            return new LaunchResult(false, null, null, error, detail);
        }
    }

    public static List<Entry> list(Context ctx) {
        List<Entry> result = new ArrayList<Entry>();
        Set<String> seen = new HashSet<String>();
        PackageManager pm = ctx.getPackageManager();
        if (pm == null) {
            return result;
        }
        try {
            addResolved(pm, result, seen, Intent.ACTION_MAIN,
                    Intent.CATEGORY_LEANBACK_LAUNCHER);
        } catch (Throwable t) {
            Log.i(TAG, "query leanback apps failed: " + t);
        }
        try {
            addResolved(pm, result, seen, Intent.ACTION_MAIN,
                    Intent.CATEGORY_LAUNCHER);
        } catch (Throwable t) {
            Log.i(TAG, "query launcher apps failed: " + t);
        }
        Collections.sort(result, new Comparator<Entry>() {
            @Override
            public int compare(Entry a, Entry b) {
                return a.label.compareToIgnoreCase(b.label);
            }
        });
        return result;
    }

    private static void addResolved(PackageManager pm, List<Entry> result,
            Set<String> seen, String action, String category) {
        Intent intent = new Intent(action);
        intent.addCategory(category);
        List<ResolveInfo> resolved = pm.queryIntentActivities(intent, 0);
        if (resolved == null) {
            return;
        }
        for (int i = 0; i < resolved.size(); i++) {
            ResolveInfo ri = resolved.get(i);
            if (ri == null || ri.activityInfo == null) {
                continue;
            }
            String pkg = ri.activityInfo.packageName;
            if (pkg == null || pkg.length() == 0 || !seen.add(pkg)) {
                continue;
            }
            String label;
            try {
                CharSequence cs = ri.loadLabel(pm);
                label = cs != null ? cs.toString() : pkg;
            } catch (Throwable t) {
                label = pkg;
            }
            if (label == null || label.trim().length() == 0) {
                label = pkg;
            }
            result.add(new Entry(pkg, label, ri.activityInfo.name));
        }
    }

    /** Launch by exact package name, then case-insensitive label contains. */
    public static LaunchResult launch(Context ctx, String pkgOrLabel) {
        String query = pkgOrLabel == null ? "" : pkgOrLabel.trim();
        if (query.length() == 0) {
            return LaunchResult.fail("bad_request", "empty package or label");
        }
        PackageManager pm = ctx.getPackageManager();
        List<Entry> apps = list(ctx);

        Entry match = null;
        for (int i = 0; i < apps.size(); i++) {
            if (apps.get(i).pkg.equals(query)) {
                match = apps.get(i);
                break;
            }
        }

        Intent explicit = null;
        if (match == null && query.indexOf('.') > 0 && pm != null) {
            try {
                explicit = pm.getLaunchIntentForPackage(query);
            } catch (Throwable t) {
                explicit = null;
            }
            if (explicit != null) {
                return start(ctx, explicit, query, null);
            }
        }

        if (match == null) {
            String lower = query.toLowerCase(Locale.US);
            Entry best = null;
            for (int i = 0; i < apps.size(); i++) {
                Entry e = apps.get(i);
                String label = e.label.toLowerCase(Locale.US);
                if (label.equals(lower)) {
                    best = e;
                    break;
                }
                if (best == null && label.indexOf(lower) >= 0) {
                    best = e;
                }
            }
            match = best;
        }

        if (match == null) {
            return LaunchResult.fail("app_not_found", query);
        }

        Intent intent = new Intent(Intent.ACTION_MAIN);
        intent.addCategory(Intent.CATEGORY_LEANBACK_LAUNCHER);
        intent.setComponent(new ComponentName(match.pkg, match.activity));
        LaunchResult res = start(ctx, intent, match.pkg, match.activity);
        if (!res.ok) {
            // Retry with the plain launcher category in case the app is not
            // leanback-aware.
            Intent fallback = new Intent(Intent.ACTION_MAIN);
            fallback.addCategory(Intent.CATEGORY_LAUNCHER);
            fallback.setComponent(new ComponentName(match.pkg, match.activity));
            return start(ctx, fallback, match.pkg, match.activity);
        }
        return res;
    }

    public static LaunchResult launchUrl(Context ctx, String url) {
        String value = url == null ? "" : url.trim();
        if (value.length() == 0) {
            return LaunchResult.fail("bad_request", "empty url");
        }
        try {
            Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(value));
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            startIntent(ctx, intent);
            return LaunchResult.ok(null, null);
        } catch (Throwable t) {
            Log.i(TAG, "launchUrl failed: " + t);
            return LaunchResult.fail("launch_failed", String.valueOf(t));
        }
    }

    private static LaunchResult start(Context ctx, Intent intent, String pkg,
            String activity) {
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        try {
            startIntent(ctx, intent);
            return LaunchResult.ok(pkg, activity);
        } catch (ActivityNotFoundException e) {
            Log.i(TAG, "start failed (not found): " + pkg + " " + e);
            return LaunchResult.fail("activity_not_found", String.valueOf(e));
        } catch (Throwable t) {
            Log.i(TAG, "start failed: " + pkg + " " + t);
            return LaunchResult.fail("launch_failed", String.valueOf(t));
        }
    }

    /**
     * Start an activity, preferring the AccessibilityService context: apps
     * with an enabled accessibility service are the most likely to be allowed
     * to start activities from the background on modern Android.
     */
    public static void startIntent(Context ctx, Intent intent) throws ActivityNotFoundException {
        try {
            ctx.startActivity(intent);
            return;
        } catch (ActivityNotFoundException e) {
            throw e;
        } catch (Throwable first) {
            Log.i(TAG, "direct startActivity failed: " + first);
            KeyService ks = KeyService.getInstance();
            if (ks != null) {
                ks.startActivity(intent);
                return;
            }
            throw new RuntimeException(String.valueOf(first));
        }
    }
}
