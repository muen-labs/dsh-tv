package com.jp.dshtv;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.ImageDecoder;
import android.graphics.drawable.AnimatedImageDrawable;
import android.graphics.drawable.BitmapDrawable;
import android.graphics.drawable.Drawable;
import android.os.Build;
import android.util.Log;
import android.widget.ImageView;

import java.util.HashMap;
import java.util.Map;

/**
 * Plays the whale's transparent animations. These are animated WebP files with
 * a real alpha channel, converted from the WebM source animations in
 * 1tryout/dsh-whale-pixel-pet (VP9 alpha → frames → animated WebP). Android's
 * ImageDecoder (API 28+) plays them natively with alpha and per-frame timing;
 * older releases fall back to the first frame.
 */
final class WhalePet {

    private final ImageView view;
    private final Map<Integer, Drawable> cache = new HashMap<>();
    private AnimatedImageDrawable active;

    WhalePet(ImageView view) {
        this.view = view;
    }

    void play(int rawRes) {
        try {
            Drawable drawable = cache.get(rawRes);
            if (drawable == null) {
                drawable = decode(rawRes);
                if (drawable == null) {
                    return;
                }
                cache.put(rawRes, drawable);
            }
            if (active != null && active != drawable) {
                active.stop();
            }
            view.setImageDrawable(drawable);
            Log.i("WhalePet", "play res=" + rawRes + " class=" + drawable.getClass().getSimpleName()
                    + " anim=" + (drawable instanceof AnimatedImageDrawable));
            if (drawable instanceof AnimatedImageDrawable) {
                AnimatedImageDrawable animated = (AnimatedImageDrawable) drawable;
                animated.setRepeatCount(AnimatedImageDrawable.REPEAT_INFINITE);
                animated.stop();
                animated.start();
                active = animated;
            } else {
                active = null;
            }
        } catch (Throwable ignored) {
            // never let a drawable failure kill the assistant session
        }
    }

    void stop() {
        if (active != null) {
            active.stop();
        }
    }

    private Drawable decode(int rawRes) {
        if (Build.VERSION.SDK_INT >= 28) {
            try {
                ImageDecoder.Source source = ImageDecoder.createSource(view.getResources(), rawRes);
                return ImageDecoder.decodeDrawable(source);
            } catch (Throwable ignored) {
                // fall through to a static first frame
            }
        }
        try {
            Bitmap bitmap = BitmapFactory.decodeResource(view.getResources(), rawRes);
            return bitmap == null ? null : new BitmapDrawable(view.getResources(), bitmap);
        } catch (Throwable ignored) {
            return null;
        }
    }
}
