#!/usr/bin/env python3
"""Search Wikimedia Commons for a photo, download the 1920px thumbnail, and build a contact sheet.

Usage: commons_photo.py "search terms" out.jpg [--pick N]
Prints the candidate titles, licences and URLs.
"""
import json
import os
import sys
import urllib.parse
import urllib.request

UA = {"User-Agent": "firetv-theme/1.0 (personal, offline TV theme)"}


def search(term, limit=12):
    q = urllib.parse.urlencode({
        "action": "query", "format": "json", "generator": "search",
        "gsrsearch": f"filetype:bitmap {term}", "gsrnamespace": "6", "gsrlimit": str(limit),
        "prop": "imageinfo", "iiprop": "url|mime|extmetadata", "iiurlwidth": "1920",
    })
    req = urllib.request.Request("https://commons.wikimedia.org/w/api.php?" + q, headers=UA)
    d = json.load(urllib.request.urlopen(req, timeout=30))
    out = []
    for p in (d.get("query", {}).get("pages", {}) or {}).values():
        ii = p.get("imageinfo", [{}])[0]
        meta = ii.get("extmetadata", {})
        lic = meta.get("LicenseShortName", {}).get("value", "?")
        artist = meta.get("Artist", {}).get("value", "?")
        out.append({
            "title": p["title"],
            "url": ii.get("thumburl") or ii.get("url"),
            "licence": lic,
            "artist": artist,
        })
    return out


def fetch(url, path):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r, open(path, "wb") as f:
        f.write(r.read())


if __name__ == "__main__":
    term = sys.argv[1]
    outdir = sys.argv[2] if len(sys.argv) > 2 else "."
    os.makedirs(outdir, exist_ok=True)
    for i, c in enumerate(search(term)):
        print(f"{i:2d}  {c['title']}\n    {c['licence']} | {c['artist'][:80]}\n    {c['url']}")
        if i < 6 and c["url"]:
            try:
                fetch(c["url"], os.path.join(outdir, f"cand_{i:02d}.jpg"))
            except Exception as e:
                print("    download failed:", e)
