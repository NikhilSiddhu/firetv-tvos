package com.firetv.webtiles;

/** One web shortcut on the home screen. */
public class Tile {
    public String name;
    public String url;
    public String iconUrl; // optional; when empty the site's favicon is used

    public Tile() {
    }

    public Tile(String name, String url, String iconUrl) {
        this.name = name;
        this.url = url;
        this.iconUrl = iconUrl;
    }

    public boolean isAddPlaceholder() {
        return url == null || url.isEmpty();
    }
}
