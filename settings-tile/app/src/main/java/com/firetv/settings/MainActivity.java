package com.firetv.settings;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Intent;
import android.os.Bundle;
import android.widget.Toast;

/**
 * A one-trick tile: it opens the TV's real Settings screen and disappears.
 *
 * On Fire OS the standard android.settings.SETTINGS action is answered by a stub in
 * com.amazon.tv.settings.v2 (its activities are all CTSDummy*), so the real menu has to be started
 * by component. On this build that is com.amazon.tv.launcher/.ui.MainSettingsActivity - the Amazon
 * launcher package hosts it.
 *
 * The candidates below are tried in order; the first one that resolves is used. If none do, the
 * standard action is sent as a last resort.
 */
public class MainActivity extends Activity {

    /** Real Settings screens, best first. */
    private static final String[][] CANDIDATES = {
            {"com.amazon.tv.launcher", "com.amazon.tv.launcher.ui.MainSettingsActivity"},
            {"com.amazon.tv.settings.v2", "com.amazon.tv.settings.v2.tv.device.DeviceActivity"},
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        if (openFirstWorking()) {
            finish();
            return;
        }

        // Nothing matched: send the plain intent and let the system decide.
        try {
            Intent fallback = new Intent(android.provider.Settings.ACTION_SETTINGS);
            fallback.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(fallback);
        } catch (Exception e) {
            Toast.makeText(this, R.string.no_settings, Toast.LENGTH_LONG).show();
        }
        finish();
    }

    private boolean openFirstWorking() {
        for (String[] c : CANDIDATES) {
            Intent intent = new Intent(Intent.ACTION_MAIN);
            intent.setComponent(new ComponentName(c[0], c[1]));
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            if (intent.resolveActivity(getPackageManager()) == null) continue;
            try {
                startActivity(intent);
                return true;
            } catch (Exception ignored) {
                // Try the next one.
            }
        }
        return false;
    }
}
