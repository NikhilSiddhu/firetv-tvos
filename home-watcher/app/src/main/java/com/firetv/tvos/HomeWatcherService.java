package com.firetv.tvos;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.AccessibilityServiceInfo;
import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.PixelFormat;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.util.Log;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.View;
import android.view.WindowManager;
import android.view.accessibility.AccessibilityEvent;

/**
 * HomeWatcherService - the Fire OS HOME redirect.
 *
 * Fire OS 7 protects com.amazon.tv.launcher and com.amazon.firehomestarter, so a third-party
 * launcher can never become the system Home through pm/cmd, and the HOME key is handled by the
 * system before any accessibility key filter runs. The route that is left:
 *
 *   1. Watch for Amazon's home window reaching the foreground.
 *   2. Cover it with a black overlay immediately, so the Amazon home screen is not seen.
 *   3. Schedule an AlarmManager alarm. The alarm fires from system_server, which is EXEMPT
 *      from the ~5 s APP_SWITCH_DELAY_TIME hold Fire OS applies to launches after HOME,
 *      and starts our launcher.
 *   4. Lift the cover a moment later.
 *
 * Without step 3 the launch is throttled to about 5 seconds - the "app-switch lock" every other
 * Fire OS 7 launcher replacement runs into. With it, and with
 * `settings put global alarm_manager_constants min_futurity=0`, the switch measures about 0.2 s
 * from a light app.
 *
 * If a launch does not land (coming out of a heavy app such as Netflix, the first attempt can be
 * queued behind its teardown), Amazon's home fires another window event and the whole redirect
 * runs again until it does.
 */
public class HomeWatcherService extends AccessibilityService {

    private static final String TAG = "HomeWatcher";

    /** The Apple TV-style launcher (cleanyourtv reference launcher). */
    public static final String TARGET_PACKAGE = "com.gathin.tvhome";
    public static final String TARGET_ACTIVITY = "com.gathin.tvhome.MainActivity";

    /** Packages that mean "Amazon's home is taking over". */
    private static final String[] WATCHED = {
            "com.amazon.tv.launcher",
            "com.amazon.firehomestarter"
    };

    /**
     * Only the launcher's *home* screens are redirected.
     *
     * The Amazon launcher package also hosts the TV's real Settings screen
     * (com.amazon.tv.launcher.ui.SettingsActivity) and a few dialogs. Redirecting those would make
     * the TV's own settings unreachable, so anything whose class name does not look like a home
     * screen is left alone.
     */
    private static final String[] HOME_CLASS_HINTS = {
            "HomeActivity",
            "FireHomeStarter",
            "HomeStarter"
    };

    /** Minimum gap between redirects, to avoid a fight loop. */
    private static final long DEBOUNCE_MS = 600L;

    /** How long the cover stays up after a launch is fired. Measured: the launcher's window is
     *  created in ~250 ms but does not reach the front until roughly 800 ms, so the cover has to
     *  outlast the whole transition or Amazon's home shows through. */
    private static final long COVER_HIDE_AFTER_LAUNCH_MS = 800L;

    /** Absolute backstop: never hold the cover longer than this. */
    private static final long COVER_MAX_MS = 2500L;

    private long lastLaunchAt = 0L;
    private boolean targetInstalled = false;

    private WindowManager windowManager;
    private View cover;

    private final Handler mainHandler = new Handler(Looper.getMainLooper());
    private final Runnable coverTimeout = new Runnable() {
        @Override
        public void run() {
            if (cover != null) hideCover();
        }
    };

    /** The running service, so LaunchReceiver can lift the cover after a launch. */
    private static HomeWatcherService instance;

    @Override
    protected void onServiceConnected() {
        super.onServiceConnected();
        refreshTargetInstalled();
        windowManager = (WindowManager) getSystemService(Context.WINDOW_SERVICE);
        instance = this;

        AccessibilityServiceInfo info = getServiceInfo();
        if (info != null) {
            info.eventTypes = AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED
                    | AccessibilityEvent.TYPE_WINDOWS_CHANGED;
            info.feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC;
            info.notificationTimeout = 0;
            info.flags |= AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS;
            info.flags |= AccessibilityServiceInfo.FLAG_REQUEST_FILTER_KEY_EVENTS;
            setServiceInfo(info);
        }
        Log.i(TAG, "connected; target installed = " + targetInstalled);
    }

    @Override
    public void onDestroy() {
        hideCover();
        if (instance == this) instance = null;
        super.onDestroy();
    }

    /** Best-effort fast path: if Fire OS ever hands us HOME, take it. */
    @Override
    protected boolean onKeyEvent(KeyEvent event) {
        if (event == null) return false;
        if (event.getKeyCode() != KeyEvent.KEYCODE_HOME) return false;
        if (event.getAction() != KeyEvent.ACTION_DOWN) return true;

        if (ready() && cover == null) {
            lastLaunchAt = SystemClock.uptimeMillis();
            Log.i(TAG, "HOME filtered; redirecting");
            redirect();
        }
        return true;
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        if (event == null) return;

        final int type = event.getEventType();
        if (type != AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED
                && type != AccessibilityEvent.TYPE_WINDOWS_CHANGED) {
            return;
        }

        CharSequence pkgCs = event.getPackageName();
        if (pkgCs == null) return;
        final String pkg = pkgCs.toString();

        if (TARGET_PACKAGE.equals(pkg)) {
            hideCover();
            return;
        }
        if (!isWatched(pkg)) return;

        // Leave the TV's own screens alone: the Amazon launcher package also hosts Settings.
        CharSequence clsCs = event.getClassName();
        String cls = clsCs == null ? "" : clsCs.toString();
        Log.i(TAG, "candidate: pkg=" + pkg + " cls=" + cls);
        if (!looksLikeHome(cls)) {
            Log.i(TAG, "ignoring non-home window");
            return;
        }

        long now = SystemClock.uptimeMillis();
        if (now - lastLaunchAt < DEBOUNCE_MS) return;
        if (cover != null) return; // a redirect is already in flight
        if (!ready()) return;

        lastLaunchAt = now;
        Log.i(TAG, "watched package foreground (" + pkg + "); redirecting");
        redirect();
    }

    private void redirect() {
        showCover();
        scheduleTargetLaunch();
        // Lift the cover on a short timer. An overlay sits above app windows and suppresses the
        // launcher's own window event, so waiting for that event would leave the screen black.
        // If the launch did not land, Amazon's home fires another event and we retry.
        mainHandler.removeCallbacks(coverTimeout);
        mainHandler.postDelayed(coverTimeout, COVER_HIDE_AFTER_LAUNCH_MS);
    }

    private boolean ready() {
        if (!targetInstalled) refreshTargetInstalled();
        return targetInstalled;
    }

    private boolean isWatched(String pkg) {
        for (String w : WATCHED) {
            if (w.equals(pkg)) return true;
        }
        return false;
    }

    private boolean looksLikeHome(String className) {
        if (className == null || className.isEmpty()) return true; // no class info: assume home
        for (String hint : HOME_CLASS_HINTS) {
            if (className.contains(hint)) return true;
        }
        return false;
    }

    private void refreshTargetInstalled() {
        try {
            getPackageManager().getPackageInfo(TARGET_PACKAGE, 0);
            targetInstalled = true;
        } catch (PackageManager.NameNotFoundException e) {
            targetInstalled = false;
        }
    }

    /** Black cover over Amazon's home while the switch happens. */
    private void showCover() {
        if (cover != null) return;
        if (windowManager == null) {
            windowManager = (WindowManager) getSystemService(Context.WINDOW_SERVICE);
            if (windowManager == null) return;
        }
        try {
            View v = new View(this);
            v.setBackgroundColor(Color.BLACK);

            int type = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                    ? WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
                    : WindowManager.LayoutParams.TYPE_SYSTEM_ALERT;

            WindowManager.LayoutParams lp = new WindowManager.LayoutParams(
                    WindowManager.LayoutParams.MATCH_PARENT,
                    WindowManager.LayoutParams.MATCH_PARENT,
                    type,
                    WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
                            | WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE
                            | WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
                    PixelFormat.OPAQUE);
            lp.gravity = Gravity.TOP | Gravity.START;

            windowManager.addView(v, lp);
            cover = v;

            // Absolute backstop in case every other path is missed.
            mainHandler.removeCallbacks(coverTimeout);
            mainHandler.postDelayed(coverTimeout, COVER_MAX_MS);
        } catch (Exception e) {
            cover = null;
            Log.w(TAG, "cover unavailable", e);
        }
    }

    private void hideCover() {
        mainHandler.removeCallbacks(coverTimeout);
        if (cover == null) return;
        try {
            windowManager.removeView(cover);
        } catch (Exception ignored) {
            // Already gone.
        }
        cover = null;
    }

    /**
     * Fire the launch straight from AlarmManager.
     *
     * The PendingIntent must be an *activity* PendingIntent, not a broadcast one. A broadcast would
     * wake our own process and the startActivity would be attributed to our uid, which puts it back
     * under Fire OS's ~5 s post-HOME app-switch hold. An activity PendingIntent is started by
     * system_server itself, which is exempt, and the launch lands in a few hundred milliseconds.
     */
    private void scheduleTargetLaunch() {
        try {
            AlarmManager am = (AlarmManager) getSystemService(Context.ALARM_SERVICE);
            if (am == null) {
                launchTargetNow(this);
                return;
            }

            Intent intent = new Intent(Intent.ACTION_MAIN);
            intent.addCategory(Intent.CATEGORY_HOME);
            intent.setComponent(new ComponentName(TARGET_PACKAGE, TARGET_ACTIVITY));
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK
                    | Intent.FLAG_ACTIVITY_REORDER_TO_FRONT
                    | Intent.FLAG_ACTIVITY_NO_ANIMATION);

            int flags = PendingIntent.FLAG_UPDATE_CURRENT;
            if (Build.VERSION.SDK_INT >= 31) flags |= PendingIntent.FLAG_IMMUTABLE;

            PendingIntent pi = PendingIntent.getActivity(this, 1001, intent, flags);

            long when = System.currentTimeMillis();
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                am.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, when, pi);
            } else {
                am.setExact(AlarmManager.RTC_WAKEUP, when, pi);
            }
        } catch (Exception e) {
            Log.w(TAG, "alarm failed, falling back to direct launch", e);
            launchTargetNow(this);
        }
    }

    /** Called by LaunchReceiver after the alarm starts the launcher. */
    static void hideCoverAfterLaunch() {
        HomeWatcherService svc = instance;
        if (svc == null) return;
        svc.mainHandler.removeCallbacks(svc.coverTimeout);
        svc.mainHandler.postDelayed(svc.coverTimeout, COVER_HIDE_AFTER_LAUNCH_MS);
    }

    /** Direct launch, used by the alarm receiver, boot receiver and as a fallback. */
    static void launchTargetNow(Context context) {
        try {
            Intent intent = new Intent(Intent.ACTION_MAIN);
            intent.addCategory(Intent.CATEGORY_HOME);
            intent.setComponent(new ComponentName(TARGET_PACKAGE, TARGET_ACTIVITY));
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK
                    | Intent.FLAG_ACTIVITY_REORDER_TO_FRONT
                    | Intent.FLAG_ACTIVITY_NO_ANIMATION);
            context.startActivity(intent);
        } catch (Exception e) {
            Log.w(TAG, "could not start target launcher", e);
        }
    }

    @Override
    public void onInterrupt() {
        // Nothing to clean up.
    }
}
