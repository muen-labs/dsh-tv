package com.jp.dshtv;

import android.content.Context;
import android.util.Log;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;

/** Talks to the whale-voice daemon on the Mac mini (STT, then DSH). */
public final class WhaleClient {

    public static final class Stt {
        public String text = "";
        public String error;
    }

    public static final class Answer {
        public String reply = "";
        public String error;
    }

    private WhaleClient() {
    }

    /** Speech-to-text only: fast, so the bubble can show what was heard first. */
    public static Stt transcribe(Context ctx, byte[] wav) {
        Stt out = new Stt();
        String body = post(ctx, "/stt", "audio/wav", wav);
        try {
            JSONObject j = new JSONObject(body);
            if (!j.optBoolean("ok")) {
                out.error = j.optString("error", "stt error");
            } else {
                out.text = j.optString("transcript", "");
            }
        } catch (Throwable t) {
            out.error = String.valueOf(t.getMessage());
            Log.w("WhaleClient", "stt failed", t);
        }
        return out;
    }

    /** DSH turn for an already-transcribed utterance. */
    public static Answer ask(Context ctx, String text) {
        Answer out = new Answer();
        try {
            JSONObject request = new JSONObject();
            request.put("text", text);
            String body = post(ctx, "/ask", "application/json; charset=utf-8",
                    request.toString().getBytes("UTF-8"));
            JSONObject j = new JSONObject(body);
            if (!j.optBoolean("ok")) {
                out.error = j.optString("error", "brain error");
            } else {
                out.reply = j.optString("reply", "");
            }
        } catch (Throwable t) {
            out.error = String.valueOf(t.getMessage());
            Log.w("WhaleClient", "ask failed", t);
        }
        return out;
    }

    private static String post(Context ctx, String path, String contentType, byte[] payload) {
        HttpURLConnection c = null;
        try {
            URL url = new URL("http://" + WhaleConfig.host(ctx)
                    + ":" + WhaleConfig.port(ctx) + path);
            c = (HttpURLConnection) url.openConnection();
            c.setRequestMethod("POST");
            c.setConnectTimeout(5000);
            c.setReadTimeout(180000);
            c.setDoOutput(true);
            c.setFixedLengthStreamingMode(payload.length);
            c.setRequestProperty("Content-Type", contentType);
            c.setRequestProperty("X-Whale-Token", WhaleConfig.token(ctx));
            OutputStream os = c.getOutputStream();
            os.write(payload);
            os.close();
            int code = c.getResponseCode();
            InputStream is = code >= 400 ? c.getErrorStream() : c.getInputStream();
            return readAll(is);
        } catch (Throwable t) {
            Log.w("WhaleClient", "post " + path + " failed", t);
            return "{\"ok\":false,\"error\":\"" + String.valueOf(t.getMessage()).replace('"', ' ')
                    + "\"}";
        } finally {
            if (c != null) {
                c.disconnect();
            }
        }
    }

    private static String readAll(InputStream is) throws Exception {
        if (is == null) {
            return "";
        }
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] buf = new byte[4096];
        int n;
        while ((n = is.read(buf)) > 0) {
            out.write(buf, 0, n);
        }
        is.close();
        return new String(out.toByteArray(), "UTF-8");
    }
}
