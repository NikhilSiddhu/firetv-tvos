#!/usr/bin/env python3
"""Draw the Web Tiles banner and icon in an Apple TV-ish style.

Outputs:
  banner.png  1280x720  (Android TV banner, shown as the tile art on the launcher)
  icon.png     512x512  (app icon)

Run with the project venv:  ./.imgvenv/bin/python tools/make_webtiles_art.py
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "web-tiles", "app", "src", "main", "res", "drawable")
os.makedirs(OUT, exist_ok=True)

FONT = "/System/Library/Fonts/Avenir Next.ttc"
FONT_BOLD_IDX = 0  # Avenir Next Regular is index 0; bold below
try:
    F_TITLE = ImageFont.truetype(FONT, 104, index=0)
    F_SMALL = ImageFont.truetype(FONT, 34, index=0)
except Exception:
    F_TITLE = ImageFont.load_default()
    F_SMALL = F_TITLE

BG_TOP = (10, 10, 14)
BG_BOTTOM = (22, 27, 38)
BLUE_TOP = (10, 132, 255)
BLUE_BOTTOM = (0, 78, 200)
WHITE = (255, 255, 255)
GREY = (150, 158, 172)


def vertical_gradient(size, top, bottom):
    w, h = size
    img = Image.new("RGB", (1, h))
    px = img.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        px[0, y] = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
    return img.resize((w, h))


def rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255)
    return m


def draw_globe(d, cx, cy, r, colour=WHITE, width=8):
    """A clean globe: outline, two meridians and two latitude arcs."""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=colour, width=width)
    # meridians
    d.ellipse([cx - r * 0.48, cy - r, cx + r * 0.48, cy + r], outline=colour, width=width)
    # equator + tropics
    for f, w in ((0.0, width), (-0.5, max(2, width - 3)), (0.5, max(2, width - 3))):
        yy = cy + f * r
        half = (r * r - (yy - cy) ** 2) ** 0.5
        d.line([cx - half, yy, cx + half, yy], fill=colour, width=w)


def spaced_text(d, xy, text, font, fill, tracking):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + tracking
    return x


def make_banner():
    W, H = 1280, 720
    img = vertical_gradient((W, H), BG_TOP, BG_BOTTOM)
    d = ImageDraw.Draw(img)

    # subtle blue wash in the top-right, like the launcher's ambient glow
    glow = Image.new("RGB", (W, H), BG_BOTTOM)
    gd = ImageDraw.Draw(glow)
    for i in range(200):
        a = i / 200
        rr = 700 - i * 3
        gd.ellipse([W - 320 - rr, -200 - rr, W - 320 + rr, -200 + rr],
                   fill=(int(8 + 34 * a), int(50 + 58 * a), int(104 + 86 * a)))
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    img = Image.blend(img, glow, 0.35)
    d = ImageDraw.Draw(img)

    # the tile
    TS = 300
    tx, ty = 130, (H - TS) // 2
    tile = vertical_gradient((TS, TS), BLUE_TOP, BLUE_BOTTOM)
    img.paste(tile, (tx, ty), rounded_mask((TS, TS), 70))

    d = ImageDraw.Draw(img)
    draw_globe(d, tx + TS // 2, ty + TS // 2, int(TS * 0.28), WHITE, 9)

    # wordmark, centred against the tile
    spaced_text(d, (tx + TS + 66, ty + 42), "WEB", F_TITLE, WHITE, 10)
    spaced_text(d, (tx + TS + 66, ty + 148), "TILES", F_TITLE, WHITE, 10)
    d.text((tx + TS + 72, ty + 274), "your links, on the TV", font=F_SMALL, fill=GREY)

    img.save(os.path.join(OUT, "webtiles_banner.png"))
    print("banner.png ->", os.path.join(OUT, "webtiles_banner.png"))


def make_icon():
    S = 512
    img = vertical_gradient((S, S), BG_TOP, BG_BOTTOM)
    TS = 400
    tx = ty = (S - TS) // 2
    tile = vertical_gradient((TS, TS), BLUE_TOP, BLUE_BOTTOM)
    img.paste(tile, (tx, ty), rounded_mask((TS, TS), 92))
    d = ImageDraw.Draw(img)
    draw_globe(d, S // 2, S // 2, int(TS * 0.29), WHITE, 12)
    img.save(os.path.join(OUT, "webtiles_icon.png"))
    print("icon.png ->", os.path.join(OUT, "webtiles_icon.png"))


if __name__ == "__main__":
    make_banner()
    make_icon()
