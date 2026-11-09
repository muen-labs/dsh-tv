package com.jp.dshtv;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.IBinder;
import android.util.Log;

import java.io.BufferedOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.SocketTimeoutException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.RejectedExecutionException;

/**
 * Foreground service that runs the LAN HTTP API the Mac mini drives the TV
 * with. One thread accepts connections, a small fixed pool serves them.
 */
public class BridgeService extends Service {

    public static final String TAG = "DshtvBridge";
    public static final String PREFS = "dshtv";
    public static final String KEY_TOKEN = "token";
    public static final String KEY_PORT = "port";
    public static final int DEFAULT_PORT = 8765;

    private static final int NOTIFICATION_ID = 1;
    private static final String CHANNEL_ID = "dshtv";
    private static final int SOCKET_TIMEOUT_MS = 10000;
    private static final int THREADS = 8;

    private static volatile boolean running;
    private static volatile long startedAtMs;

    private ServerSocket serverSocket;
    private Thread acceptThread;
    private ExecutorService pool;
    private NsdHelper nsd;

    public static boolean isRunning() {
        return running;
    }

    public static long uptimeMs() {
        return running ? System.currentTimeMillis() - startedAtMs : 0;
    }

    public static SharedPreferences prefs(Context ctx) {
        return ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public static String token(Context ctx) {
        String t = prefs(ctx).getString(KEY_TOKEN, "");
        return t != null ? t.trim() : "";
    }

    public static int port(Context ctx) {
        int p = prefs(ctx).getInt(KEY_PORT, DEFAULT_PORT);
        return (p > 0 && p < 65536) ? p : DEFAULT_PORT;
    }

    @Override
    public void onCreate() {
        super.onCreate();
        createChannel();
        startForeground(NOTIFICATION_ID, buildNotification());
        Log.i(TAG, "BridgeService created");
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        // Keep the notification in place even after a sticky restart.
        startForeground(NOTIFICATION_ID, buildNotification());
        if (!running) {
            startServer();
        }
        return START_STICKY;
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public void onDestroy() {
        Log.i(TAG, "BridgeService destroying");
        stopServer();
        Tts.shutdown();
        super.onDestroy();
    }

    private synchronized void startServer() {
        final int port = port(this);
        try {
            serverSocket = new ServerSocket();
            serverSocket.setReuseAddress(true);
            serverSocket.bind(new InetSocketAddress("0.0.0.0", port));
            pool = Executors.newFixedThreadPool(THREADS);
            running = true;
            startedAtMs = System.currentTimeMillis();
            acceptThread = new Thread(new Runnable() {
                @Override
                public void run() {
                    acceptLoop();
                }
            }, "dshtv-accept");
            acceptThread.start();
            try {
                nsd = new NsdHelper(this);
                nsd.start(port);
            } catch (Throwable t) {
                Log.i(TAG, "mDNS setup failed: " + t);
            }
            Log.i(TAG, "HTTP server listening on 0.0.0.0:" + port);
        } catch (Throwable t) {
            running = false;
            Log.i(TAG, "HTTP server failed to start on port " + port + ": " + t);
            closeServerSocket();
            shutdownPool();
        }
    }

    private synchronized void stopServer() {
        running = false;
        closeServerSocket();
        shutdownPool();
        if (nsd != null) {
            try {
                nsd.stop();
            } catch (Throwable ignored) {
            }
            nsd = null;
        }
        Log.i(TAG, "HTTP server stopped");
    }

    private void closeServerSocket() {
        ServerSocket socket = serverSocket;
        serverSocket = null;
        if (socket != null) {
            try {
                socket.close();
            } catch (Throwable ignored) {
            }
        }
    }

    private void shutdownPool() {
        ExecutorService p = pool;
        pool = null;
        if (p != null) {
            p.shutdownNow();
        }
    }

    private void acceptLoop() {
        while (running) {
            Socket socket = null;
            try {
                ServerSocket server = serverSocket;
                if (server == null) {
                    break;
                }
                socket = server.accept();
                final Socket accepted = socket;
                pool.execute(new Connection(accepted));
            } catch (IOException e) {
                if (running) {
                    Log.i(TAG, "accept failed: " + e);
                }
                closeQuietly(socket);
                break;
            } catch (RejectedExecutionException e) {
                closeQuietly(socket);
                break;
            } catch (Throwable t) {
                closeQuietly(socket);
                if (running) {
                    Log.i(TAG, "accept error: " + t);
                }
                break;
            }
        }
    }

    /** Serve one client connection. */
    private final class Connection implements Runnable {
        private final Socket socket;

        Connection(Socket socket) {
            this.socket = socket;
        }

        @Override
        public void run() {
            try {
                socket.setSoTimeout(SOCKET_TIMEOUT_MS);
                InputStream in = socket.getInputStream();
                Http.Request request = Http.parse(in);
                if (request == null) {
                    return;
                }
                Log.i(TAG, "request " + request.method + " " + request.path
                        + (request.rawQuery != null ? "?" + request.rawQuery : ""));
                Http.Response response = handleRequest(request);
                OutputStream out = new BufferedOutputStream(socket.getOutputStream());
                writeResponse(out, response);
                out.flush();
            } catch (SocketTimeoutException e) {
                Log.i(TAG, "connection timed out");
            } catch (Throwable t) {
                Log.i(TAG, "connection error: " + t);
            } finally {
                closeQuietly(socket);
            }
        }
    }

    private Http.Response handleRequest(Http.Request request) {
        try {
            if (!"GET".equals(request.method)) {
                return Http.Response.error(405, "method_not_allowed");
            }
            String required = token(this);
            if (required.length() > 0) {
                String given = request.header("x-dsh-token");
                if (given == null) {
                    given = request.q("token");
                }
                if (given == null) {
                    given = "";
                }
                if (!required.equals(given.trim())) {
                    Log.i(TAG, "unauthorized request: " + request.path);
                    return Http.Response.error(401, "unauthorized");
                }
            }
            return ApiHandler.handle(this, request);
        } catch (Throwable t) {
            Log.i(TAG, "handler error: " + t);
            return Http.Response.error(500, "internal_error");
        }
    }

    private void writeResponse(OutputStream out, Http.Response response) throws IOException {
        byte[] body = response.body != null ? response.body : new byte[0];
        StringBuilder head = new StringBuilder(256);
        head.append("HTTP/1.1 ").append(response.status)
                .append(' ').append(Http.reason(response.status)).append("\r\n");
        head.append("Content-Type: ").append(response.contentType).append("\r\n");
        head.append("Content-Length: ").append(body.length).append("\r\n");
        head.append("Connection: close\r\n");
        head.append("Access-Control-Allow-Origin: *\r\n");
        head.append("Cache-Control: no-store\r\n");
        head.append("\r\n");
        out.write(head.toString().getBytes(Http.UTF8));
        out.write(body);
    }

    private void createChannel() {
        try {
            NotificationManager manager = (NotificationManager)
                    getSystemService(Context.NOTIFICATION_SERVICE);
            if (manager == null) {
                return;
            }
            NotificationChannel channel = new NotificationChannel(CHANNEL_ID,
                    "DSH TV Bridge", NotificationManager.IMPORTANCE_LOW);
            channel.setDescription("Background LAN bridge server status");
            channel.setShowBadge(false);
            manager.createNotificationChannel(channel);
        } catch (Throwable t) {
            Log.i(TAG, "createChannel failed: " + t);
        }
    }

    private Notification buildNotification() {
        Intent open = new Intent(this, MainActivity.class);
        int pendingFlags = PendingIntent.FLAG_UPDATE_CURRENT;
        if (android.os.Build.VERSION.SDK_INT >= 23) {
            pendingFlags |= PendingIntent.FLAG_IMMUTABLE;
        }
        PendingIntent contentIntent = PendingIntent.getActivity(this, 1, open, pendingFlags);
        Notification.Builder builder = new Notification.Builder(this, CHANNEL_ID);
        builder.setSmallIcon(R.drawable.ic_launcher);
        builder.setContentTitle("DSH TV Bridge");
        builder.setContentText("HTTP server on port " + port(this));
        builder.setOngoing(true);
        builder.setCategory(Notification.CATEGORY_SERVICE);
        builder.setContentIntent(contentIntent);
        return builder.build();
    }

    private static void closeQuietly(Socket socket) {
        if (socket == null) {
            return;
        }
        try {
            socket.close();
        } catch (Throwable ignored) {
        }
    }
}
