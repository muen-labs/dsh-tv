package com.jp.dshtv;

import android.content.Context;
import android.net.nsd.NsdManager;
import android.net.nsd.NsdServiceInfo;
import android.util.Log;

/**
 * Best-effort mDNS advertisement of the bridge as _dshtv._tcp so the Mac
 * can discover the TV. Every failure is logged and ignored: mDNS is optional
 * and the server works fine with a hard-coded IP.
 */
public final class NsdHelper {

    private static final String TAG = "DshtvBridge";
    private static final String SERVICE_TYPE = "_dshtv._tcp";
    private static final String SERVICE_NAME = "DSH TV Bridge";

    private final Context ctx;
    private NsdManager manager;
    private NsdManager.RegistrationListener listener;
    private boolean registered;

    public NsdHelper(Context ctx) {
        this.ctx = ctx.getApplicationContext();
    }

    public void start(int port) {
        try {
            manager = (NsdManager) ctx.getSystemService(Context.NSD_SERVICE);
            if (manager == null) {
                Log.i(TAG, "NsdManager unavailable");
                return;
            }
            NsdServiceInfo info = new NsdServiceInfo();
            info.setServiceName(SERVICE_NAME);
            info.setServiceType(SERVICE_TYPE);
            info.setPort(port);
            listener = new NsdManager.RegistrationListener() {
                @Override
                public void onServiceRegistered(NsdServiceInfo serviceInfo) {
                    Log.i(TAG, "mDNS registered: " + serviceInfo.getServiceName()
                            + " " + SERVICE_TYPE + ":" + serviceInfo.getPort());
                }

                @Override
                public void onRegistrationFailed(NsdServiceInfo serviceInfo, int errorCode) {
                    Log.i(TAG, "mDNS registration failed: " + errorCode);
                }

                @Override
                public void onServiceUnregistered(NsdServiceInfo serviceInfo) {
                    Log.i(TAG, "mDNS unregistered");
                }

                @Override
                public void onUnregistrationFailed(NsdServiceInfo serviceInfo, int errorCode) {
                    Log.i(TAG, "mDNS unregistration failed: " + errorCode);
                }
            };
            manager.registerService(info, NsdManager.PROTOCOL_DNS_SD, listener);
            registered = true;
        } catch (Throwable t) {
            registered = false;
            Log.i(TAG, "mDNS start failed: " + t);
        }
    }

    public void stop() {
        if (!registered || manager == null || listener == null) {
            registered = false;
            return;
        }
        try {
            manager.unregisterService(listener);
        } catch (Throwable t) {
            Log.i(TAG, "mDNS stop failed: " + t);
        }
        registered = false;
    }
}
