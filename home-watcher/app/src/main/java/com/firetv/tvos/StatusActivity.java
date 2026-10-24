package com.firetv.tvos;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.provider.Settings;
import android.view.Gravity;
import android.widget.LinearLayout;
import android.widget.TextView;

/**
 * A minimal status screen: says whether the watcher is enabled and whether the
 * target launcher is installed. No AndroidX, no network, no permissions.
 */
public class StatusActivity extends Activity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setPadding(48, 48, 48, 48);

        TextView title = new TextView(this);
        title.setText("TV Home Watcher");
        title.setTextSize(28f);
        title.setGravity(Gravity.CENTER);

        TextView body = new TextView(this);
        body.setTextSize(16f);
        body.setGravity(Gravity.CENTER);
        body.setPadding(0, 32, 0, 0);
        body.setText(statusText());

        root.addView(title);
        root.addView(body);
        setContentView(root);
    }

    private String statusText() {
        boolean serviceOn = isServiceEnabled();
        boolean targetOn = isTargetInstalled();
        return "Watcher service: " + (serviceOn ? "ENABLED" : "not enabled")
                + "\nTarget launcher (com.gathin.tvhome): " + (targetOn ? "installed" : "NOT installed")
                + "\n\nEnable with:\nsettings put secure enabled_accessibility_services "
                + getPackageName() + "/.HomeWatcherService"
                + "\nsettings put secure accessibility_enabled 1";
    }

    private boolean isServiceEnabled() {
        String enabled = Settings.Secure.getString(
                getContentResolver(), Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES);
        if (enabled == null) return false;
        return enabled.toLowerCase().contains(
                (getPackageName() + "/.HomeWatcherService").toLowerCase())
                || enabled.toLowerCase().contains(getPackageName().toLowerCase());
    }

    private boolean isTargetInstalled() {
        try {
            getPackageManager().getPackageInfo(HomeWatcherService.TARGET_PACKAGE, 0);
            return true;
        } catch (Exception e) {
            return false;
        }
    }

    @SuppressWarnings("unused")
    private void openAccessibilitySettings(Context ctx) {
        Intent i = new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS);
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        ctx.startActivity(i);
    }

    @SuppressWarnings("unused")
    private ComponentName self() {
        return new ComponentName(this, HomeWatcherService.class);
    }
}
