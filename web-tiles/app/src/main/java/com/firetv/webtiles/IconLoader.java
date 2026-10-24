package com.firetv.webtiles;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.util.Log;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.security.MessageDigest;
import java.util.Locale;

/**
 * Downloads and caches a tile's artwork.
 *
 * Order of preference:
 *   1. the icon URL the user gave, if any;
 *   2. the site's own /favicon.ico;
 *   3. Google's favicon service, which returns a sensible icon for most sites.
 *
 * Files land in the app's files dir, named after the URL, so the fetch happens once.
 */
public class IconLoader {

    private static final String TAG = "WebTiles";
    private static final int TIMEOUT_MS = 8000;

    public static File iconFileFor(Context ctx, Tile tile) {
        String key = tile.iconUrl != null && !tile.iconUrl.isEmpty()
                ? tile.iconUrl
                : TileStore.hostOf(tile.url);
        File dir = new File(ctx.getFilesDir(), "icons");
        if (!dir.exists()) dir.mkdirs();
        return new File(dir, sha1(key) + ".img");
    }

    /** Blocking; call off the main thread. Returns the cached file, or null. */
    public static File fetch(Context ctx, Tile tile) {
        File out = iconFileFor(ctx, tile);
        if (out.exists() && out.length() > 0) return out;

        String host = TileStore.hostOf(tile.url);
        String[] candidates = new String[]{
                (tile.iconUrl != null && !tile.iconUrl.isEmpty()) ? TileStore.normaliseUrl(tile.iconUrl) : null,
                host.isEmpty() ? null : "https://" + host + "/favicon.ico",
                host.isEmpty() ? null : "https://www.google.com/s2/favicons?sz=128&domain=" + host
        };

        for (String url : candidates) {
            if (url == null) continue;
            if (download(url, out)) return out;
        }
        Log.w(TAG, "no icon found for " + tile.url);
        return null;
    }

    private static boolean download(String url, File out) {
        HttpURLConnection conn = null;
        try {
            conn = (HttpURLConnection) new URL(url).openConnection();
            conn.setConnectTimeout(TIMEOUT_MS);
            conn.setReadTimeout(TIMEOUT_MS);
            conn.setInstanceFollowRedirects(true);
            conn.setRequestProperty("User-Agent", "Mozilla/5.0 (Android) WebTiles/1.0");
            int code = conn.getResponseCode();
            if (code < 200 || code >= 300) return false;

            try (InputStream in = conn.getInputStream()) {
                byte[] data = readFully(in, 512 * 1024);
                if (data == null || data.length < 64) return false;

                // Only keep it if it really decodes as an image.
                Bitmap probe = BitmapFactory.decodeByteArray(data, 0, data.length);
                if (probe == null) return false;
                probe.recycle();

                try (FileOutputStream fos = new FileOutputStream(out)) {
                    fos.write(data);
                }
                return true;
            }
        } catch (Exception e) {
            Log.w(TAG, "icon download failed: " + url + " (" + e.getMessage() + ")");
            return false;
        } finally {
            if (conn != null) conn.disconnect();
        }
    }

    private static byte[] readFully(InputStream in, int max) throws Exception {
        java.io.ByteArrayOutputStream bos = new java.io.ByteArrayOutputStream();
        byte[] buf = new byte[8192];
        int n;
        while ((n = in.read(buf)) > 0) {
            bos.write(buf, 0, n);
            if (bos.size() > max) return null;
        }
        return bos.toByteArray();
    }

    private static String sha1(String s) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-1");
            byte[] d = md.digest(s.getBytes("UTF-8"));
            StringBuilder sb = new StringBuilder();
            for (byte b : d) sb.append(String.format(Locale.US, "%02x", b));
            return sb.toString();
        } catch (Exception e) {
            return String.valueOf(s.hashCode());
        }
    }
}
