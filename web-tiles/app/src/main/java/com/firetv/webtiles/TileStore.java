package com.firetv.webtiles;

import android.content.Context;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.io.FileInputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

/**
 * Stores the tiles as JSON in the app's external files directory:
 *
 *   /sdcard/Android/data/com.firetv.webtiles/files/tiles.json
 *
 * Because it is a plain file on shared storage it can also be written over ADB, so a script or a
 * home server can add tiles without touching the TV's remote:
 *
 *   adb push tiles.json /sdcard/Android/data/com.firetv.webtiles/files/tiles.json
 */
public class TileStore {

    private static final String TAG = "WebTiles";
    private static final String FILE_NAME = "tiles.json";

    public static File file(Context ctx) {
        File dir = ctx.getExternalFilesDir(null);
        if (dir == null) dir = ctx.getFilesDir();
        return new File(dir, FILE_NAME);
    }

    public static List<Tile> load(Context ctx) {
        List<Tile> out = new ArrayList<>();
        File f = file(ctx);
        if (!f.exists()) return out;
        try {
            String json = readAll(f);
            JSONArray arr = new JSONArray(json);
            for (int i = 0; i < arr.length(); i++) {
                JSONObject o = arr.getJSONObject(i);
                Tile t = new Tile();
                t.name = o.optString("name", "");
                t.url = o.optString("url", "");
                t.iconUrl = o.optString("icon", "");
                if (!t.name.isEmpty() && !t.url.isEmpty()) out.add(t);
            }
        } catch (Exception e) {
            Log.w(TAG, "could not read tiles.json", e);
        }
        return out;
    }

    public static void save(Context ctx, List<Tile> tiles) {
        try {
            JSONArray arr = new JSONArray();
            for (Tile t : tiles) {
                if (t.isAddPlaceholder()) continue;
                JSONObject o = new JSONObject();
                o.put("name", t.name);
                o.put("url", t.url);
                o.put("icon", t.iconUrl == null ? "" : t.iconUrl);
                arr.put(o);
            }
            File f = file(ctx);
            File parent = f.getParentFile();
            if (parent != null && !parent.exists()) parent.mkdirs();
            try (FileOutputStream fos = new FileOutputStream(f)) {
                fos.write(arr.toString(2).getBytes(StandardCharsets.UTF_8));
            }
        } catch (Exception e) {
            Log.w(TAG, "could not write tiles.json", e);
        }
    }

    private static String readAll(File f) throws Exception {
        try (FileInputStream in = new FileInputStream(f)) {
            byte[] buf = new byte[(int) f.length()];
            int n = in.read(buf);
            return new String(buf, 0, Math.max(n, 0), StandardCharsets.UTF_8);
        }
    }

    /** Adds a scheme when the user typed a bare domain. */
    public static String normaliseUrl(String raw) {
        String u = raw == null ? "" : raw.trim();
        if (u.isEmpty()) return "";
        if (!u.matches("(?i)^[a-z][a-z0-9+.-]*://.*")) u = "https://" + u;
        return u;
    }

    public static String hostOf(String url) {
        try {
            String u = normaliseUrl(url);
            int i = u.indexOf("://");
            String rest = i >= 0 ? u.substring(i + 3) : u;
            int slash = rest.indexOf('/');
            if (slash >= 0) rest = rest.substring(0, slash);
            int colon = rest.indexOf(':');
            if (colon >= 0) rest = rest.substring(0, colon);
            return rest;
        } catch (Exception e) {
            return "";
        }
    }
}
