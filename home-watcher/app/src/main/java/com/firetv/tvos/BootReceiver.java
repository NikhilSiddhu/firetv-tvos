package com.firetv.tvos;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.util.Log;

/**
 * Starts the Apple TV-style home right after the TV boots, so it does not sit on Amazon's
 * launcher until the first Home press.
 *
 * A single launch is not enough in practice: at BOOT_COMPLETED the canvasOS process is often
 * still starting, and Fire OS is bringing its own launcher up at the same time, so the first
 * intent can be dropped or overtaken. Two follow-up launches are scheduled through
 * AlarmManager, which system_server performs (exempt from the post-boot app-switch throttle
 * that would otherwise delay a plain startActivity), and are harmless if the first one landed:
 * the flags re-order the already running activity to the front.
 */
public class BootReceiver extends BroadcastReceiver {

    private static final String TAG = "HomeWatcher";

    /** Waits that cover a slow canvasOS start; the last one also covers a slow Wi-Fi wake. */
    private static final long[] RETRY_MS = {6_000L, 15_000L};

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
        for (long ms : RETRY_MS) schedule(context, ms);
    }

    private void schedule(Context context, long delayMs) {
        try {
            Intent i = target(context);
            int flags = PendingIntent.FLAG_UPDATE_CURRENT;
            if (Build.VERSION.SDK_INT >= 31) flags |= PendingIntent.FLAG_IMMUTABLE;
            PendingIntent pi = PendingIntent.getActivity(context, (int) delayMs, i, flags);
            AlarmManager am = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
            if (am == null) return;
            am.setExactAndAllowWhileIdle(
                    AlarmManager.RTC_WAKEUP, System.currentTimeMillis() + delayMs, pi);
        } catch (Exception e) {
            Log.w(TAG, "boot retry " + delayMs + "ms could not be scheduled", e);
        }
    }

    private Intent target(Context context) {
        Intent i = new Intent(Intent.ACTION_MAIN);
        i.addCategory(Intent.CATEGORY_HOME);
        i.setComponent(new ComponentName(
                HomeWatcherService.TARGET_PACKAGE, HomeWatcherService.TARGET_ACTIVITY));
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK
                | Intent.FLAG_ACTIVITY_REORDER_TO_FRONT
                | Intent.FLAG_ACTIVITY_NO_ANIMATION);
        return i;
    }
}
