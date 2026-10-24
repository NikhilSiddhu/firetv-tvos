package com.firetv.tvos;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

/**
 * Starts the Apple TV-style home right after the TV boots, so it does not sit on Amazon's
 * launcher until the first Home press.
 *
 * The accessibility service alone already redirects on boot (Amazon's home fires a window
 * event), but this makes the first frame land on our launcher without the brief cover.
 */
public class BootReceiver extends BroadcastReceiver {

    private static final String TAG = "HomeWatcher";

    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent == null) return;
        String action = intent.getAction();
        if (action == null) return;
        if (!Intent.ACTION_BOOT_COMPLETED.equals(action)
                && !"android.intent.action.QUICKBOOT_POWERON".equals(action)) {
            return;
        }
        Log.i(TAG, "boot: starting target launcher");
        HomeWatcherService.launchTargetNow(context);
    }
}
