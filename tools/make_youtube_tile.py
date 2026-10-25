#!/usr/bin/env python3
"""Make a canvasOS home tile: SmartTube wearing the YouTube brand.

canvasOS draws each dock tile as 16:9 art read from
/sdcard/Android/data/com.getisolated.canvasos/files/tiles/<package>.jpg
so the app keeps its own identity (and its self-updates) while the tile shows
the YouTube lockup, like the Netflix, Kodi and VLC tiles next to it.

Run: ./.imgvenv/bin/python tools/make_youtube_tile.py
"""
from PIL import Image

BRAND = "tools/brand/youtube_full_trans.png"
OUT = "dist/youtube-tile-org.smarttube.stable.jpg"

W, H = 800, 450
CARD = (255, 255, 255)
LOGO_W = 700  # same visual weight as the Netflix / Kodi wordmarks

logo = Image.open(BRAND).convert("RGBA")
h = round(logo.height * LOGO_W / logo.width)
logo = logo.resize((LOGO_W, h), Image.LANCZOS)

card = Image.new("RGB", (W, H), CARD)
card.paste(logo, ((W - LOGO_W) // 2, (H - h) // 2), logo)
card.save(OUT, "JPEG", quality=93, subsampling=0)
print(f"{OUT} {W}x{H} logo={LOGO_W}x{h}")
