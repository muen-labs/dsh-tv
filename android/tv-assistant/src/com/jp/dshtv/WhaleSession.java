package com.jp.dshtv;

import android.app.Dialog;
import android.content.Context;
import android.os.Bundle;
import android.service.voice.VoiceInteractionSession;
import android.graphics.Color;
import android.graphics.drawable.ColorDrawable;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;

/** The overlay the mic button opens: whale art + a speech bubble. */
public class WhaleSession extends VoiceInteractionSession {

    private View root;
    private WhaleUi ui;

    public WhaleSession(Context context) {
        super(context);
    }

    @Override
    public View onCreateContentView() {
        root = getLayoutInflater().inflate(R.layout.whale_session, null);
        return root;
    }

    @Override
    public void onShow(Bundle args, int showFlags) {
        super.onShow(args, showFlags);
        setUiEnabled(true);
        try {
            Dialog dialog = getWindow();
            Window window = dialog == null ? null : dialog.getWindow();
            if (window != null) {
                window.setBackgroundDrawable(new ColorDrawable(Color.TRANSPARENT));
                window.addFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND);
                window.addFlags(WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN);
                window.setDimAmount(0.28f);
            }
        } catch (Throwable ignored) {
            // window tweaks are best-effort; the transparent theme is the main lever
        }
        if (ui == null) {
            ui = new WhaleUi(getContext(), root, new Runnable() {
                @Override
                public void run() {
                    try {
                        hide();
                    } catch (Throwable ignored) {
                    }
                }
            });
        }
        ui.listen();
    }

    @Override
    public void onHide() {
        if (ui != null) {
            ui.stop();
        }
        super.onHide();
    }

    @Override
    public void onDestroy() {
        if (ui != null) {
            ui.shutdown();
        }
        super.onDestroy();
    }
}
