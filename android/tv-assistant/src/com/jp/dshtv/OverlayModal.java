package com.jp.dshtv;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.Bitmap;
import android.graphics.RenderEffect;
import android.graphics.Shader;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.View;
import android.widget.ImageView;
import android.view.animation.DecelerateInterpolator;

import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Modal presentation for the voice overlay.
 *
 * Neither demo box supports cross-window blur (`ro.surface_flinger
 * .supports_background_blur` is empty on Android 14 sc2/s7d), so we fake a
 * real blur: capture the display through the KeyService accessibility service
 * while the overlay is still invisible (root alpha 0), downscale it hard,
 * box-blur it, then show it full-screen under the black scrim. If the capture
 * is unavailable (API < 30, service off, refused) we keep the scrim+vignette
 * only. The bubble/pet fade+scale in over 150-200ms.
 */
public final class OverlayModal {

    private static final String TAG = "WhaleOverlay";
    private static final long REVEAL_FALLBACK_MS = 900;

    // ---- modal treatment tunables (single place to dial it) ----------------
    /** Flat black dim over the backdrop; low enough to keep the app readable. */
    private static final float SCRIM_ALPHA = 0.20f;
    /** Resolution the screen is captured down to before blurring (1920 native). */
    private static final int DOWNSCALE_WIDTH = 960;
    /** Box-blur radius on the downscaled capture; 0 disables it. */
    private static final int BOX_BLUR_RADIUS = 1;
    /** Extra GPU blur on API 31+; small so text stays recognisable. */
    private static final float RENDER_BLUR_RADIUS = 8f;

    private OverlayModal() {
    }

    /** Capture the backdrop (async) and animate the modal in. */
    public static void show(final Activity activity, final View root) {
        if (activity == null || root == null) {
            return;
        }
        final ImageView backdrop = (ImageView) root.findViewById(R.id.whale_backdrop);
        final View modal = root.findViewById(R.id.whale_modal);
        final View pet = root.findViewById(R.id.whale_pet_wrap);
        final View chip = root.findViewById(R.id.whale_app_chip);
        final Handler main = new Handler(Looper.getMainLooper());
        final AtomicBoolean revealed = new AtomicBoolean(false);

        // flat dim is a runtime constant so the treatment stays tunable
        View dim = root.findViewById(R.id.whale_dim);
        if (dim != null) {
            dim.setBackgroundColor(Color.argb(Math.round(SCRIM_ALPHA * 255), 6, 10, 18));
        }

        // keep our layer invisible while the screen is captured so the shot
        // does not contain our own bubble
        root.setAlpha(0f);
        startHidden(modal, 0.96f);
        startHidden(pet, 0.96f);
        if (chip != null) {
            chip.setAlpha(0f);
        }

        final Runnable reveal = new Runnable() {
            @Override
            public void run() {
                if (!revealed.compareAndSet(false, true)) {
                    return;
                }
                root.animate().alpha(1f).setDuration(180)
                        .setInterpolator(new DecelerateInterpolator(1.4f)).start();
                if (chip != null) {
                    chip.animate().alpha(1f).setDuration(220).start();
                }
                animateIn(modal, 60);
                animateIn(pet, 120);
            }
        };

        // never keep the overlay invisible if the capture hangs
        main.postDelayed(reveal, REVEAL_FALLBACK_MS);

        new Thread(new Runnable() {
            @Override
            public void run() {
                Bitmap shot = null;
                try {
                    KeyService service = KeyService.getInstance();
                    if (service != null) {
                        shot = service.screenshotBitmap(2);
                    }
                } catch (Throwable t) {
                    Log.i(TAG, "backdrop capture failed: " + t);
                }
                final Bitmap blurred = shot == null ? null : blurred(shot);
                main.post(new Runnable() {
                    @Override
                    public void run() {
                        if (blurred != null && backdrop != null) {
                            backdrop.setImageBitmap(blurred);
                            if (Build.VERSION.SDK_INT >= 31 && RENDER_BLUR_RADIUS > 0f) {
                                try {
                                    backdrop.setRenderEffect(RenderEffect.createBlurEffect(
                                            RENDER_BLUR_RADIUS, RENDER_BLUR_RADIUS,
                                            Shader.TileMode.CLAMP));
                                } catch (Throwable ignored) {
                                }
                            }
                            backdrop.setVisibility(View.VISIBLE);
                            backdrop.setAlpha(0f);
                            backdrop.animate().alpha(1f).setDuration(240).start();
                        }
                        reveal.run();
                    }
                });
            }
        }, "whale-backdrop").start();
    }

    private static void startHidden(View view, float scale) {
        if (view == null) {
            return;
        }
        view.setAlpha(0f);
        view.setScaleX(scale);
        view.setScaleY(scale);
    }

    private static void animateIn(View view, long delay) {
        if (view == null) {
            return;
        }
        view.animate().alpha(1f).scaleX(1f).scaleY(1f)
                .setStartDelay(delay).setDuration(190)
                .setInterpolator(new DecelerateInterpolator(1.4f)).start();
    }

    /**
     * Light treatment: capture down to DOWNSCALE_WIDTH (960 of 1920), apply a
     * small box blur, and let the ImageView scale it back up. Text and blocks
     * behind stay recognisable; edges only soften.
     */
    private static Bitmap blurred(Bitmap src) {
        if (src == null || src.getWidth() < 8 || src.getHeight() < 8) {
            return null;
        }
        try {
            int width = Math.min(DOWNSCALE_WIDTH, src.getWidth());
            int height = Math.max(8, Math.round(width * (float) src.getHeight() / src.getWidth()));
            Bitmap small = Bitmap.createScaledBitmap(src, width, height, true);
            if (BOX_BLUR_RADIUS > 0) {
                boxBlur(small, BOX_BLUR_RADIUS);
            }
            return small;
        } catch (Throwable t) {
            Log.i(TAG, "blur failed: " + t);
            return null;
        } finally {
            try {
                src.recycle();
            } catch (Throwable ignored) {
            }
        }
    }

    /** Naive box blur on the downscaled capture - cheap in a worker thread. */
    private static void boxBlur(Bitmap bitmap, int radius) {
        int w = bitmap.getWidth();
        int h = bitmap.getHeight();
        int[] src = new int[w * h];
        bitmap.getPixels(src, 0, w, 0, 0, w, h);
        int[] dst = new int[w * h];
        for (int y = 0; y < h; y++) {
            for (int x = 0; x < w; x++) {
                int a = 0;
                int r = 0;
                int g = 0;
                int b = 0;
                int n = 0;
                for (int dy = -radius; dy <= radius; dy++) {
                    int yy = y + dy;
                    if (yy < 0 || yy >= h) {
                        continue;
                    }
                    for (int dx = -radius; dx <= radius; dx++) {
                        int xx = x + dx;
                        if (xx < 0 || xx >= w) {
                            continue;
                        }
                        int p = src[yy * w + xx];
                        a += (p >>> 24) & 0xFF;
                        r += (p >> 16) & 0xFF;
                        g += (p >> 8) & 0xFF;
                        b += p & 0xFF;
                        n++;
                    }
                }
                dst[y * w + x] = ((a / n) & 0xFF) << 24 | ((r / n) & 0xFF) << 16
                        | ((g / n) & 0xFF) << 8 | ((b / n) & 0xFF);
            }
        }
        bitmap.setPixels(dst, 0, w, 0, 0, w, h);
    }
}
