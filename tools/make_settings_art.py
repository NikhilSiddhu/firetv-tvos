#!/usr/bin/env python3
"""Draw the Settings tile's banner and icon in the same Apple TV-ish style.

Outputs into settings-tile/app/src/main/res/drawable/:
  settings_banner.png  1280x720
  settings_icon.png     512x512
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "settings-tile", "app", "src", "main", "res", "drawable")
os.makedirs(OUT, exist_ok=True)

FONT = "/System/Library/Fonts/Avenir Next.ttc"
F_TITLE = ImageFont.truetype(FONT, 104, index=0)
F_SMALL = ImageFont.truetype(FONT, 34, index=0)

BG_TOP = (10, 10, 14)
BG_BOTTOM = (24, 26, 34)
STEEL_TOP = (86, 92, 104)
STEEL_BOTTOM = (44, 48, 58)
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
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255)
    return m


def draw_gear(d, cx, cy, r, colour=WHITE, teeth=8, tooth=0.30, hole=0.34):
    """A clean gear: an outer ring with teeth, plus a centre hole."""
    pts = []
    steps = teeth * 4
    for i in range(steps):
        a = (i / steps) * 2 * math.pi - math.pi / 2
        seg = i % 4
        rad = r * (1 + tooth) if seg in (1, 2) else r
        pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
    d.polygon(pts, fill=colour)
    hr = r * hole
    d.ellipse([cx - hr, cy - hr, cx + hr, cy + hr], fill=(0, 0, 0, 0))


def draw_gear_on(img, cx, cy, r, colour=WHITE):
    """Draw the gear with a transparent centre punched out against the tile."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    pts = []
    teeth, tooth, steps = 8, 0.30, 32
    for i in range(steps):
        a = (i / steps) * 2 * math.pi - math.pi / 2
        seg = i % 4
        rad = r * (1 + tooth) if seg in (1, 2) else r
        pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
    ld.polygon(pts, fill=colour + (255,))
    hr = r * 0.34
    ld.ellipse([cx - hr, cy - hr, cx + hr, cy + hr], fill=(0, 0, 0, 0))
    img.alpha_composite(layer)


def spaced_text(d, xy, text, font, fill, tracking):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + tracking


def make_banner():
    W, H = 1280, 720
    base = vertical_gradient((W, H), BG_TOP, BG_BOTTOM).convert("RGBA")

    glow = Image.new("RGB", (W, H), BG_BOTTOM)
    gd = ImageDraw.Draw(glow)
    for i in range(200):
        a = i / 200
        rr = 700 - i * 3
        gd.ellipse([W - 320 - rr, -200 - rr, W - 320 + rr, -200 + rr],
                   fill=(int(20 + 30 * a), int(24 + 34 * a), int(34 + 44 * a)))
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    base = Image.blend(base.convert("RGB"), glow, 0.35).convert("RGBA")

    TS = 300
    tx, ty = 130, (H - TS) // 2
    tile = vertical_gradient((TS, TS), STEEL_TOP, STEEL_BOTTOM).convert("RGBA")
    base.paste(tile, (tx, ty), rounded_mask((TS, TS), 70))

    draw_gear_on(base, tx + TS // 2, ty + TS // 2, int(TS * 0.30), WHITE)

    d = ImageDraw.Draw(base)
    spaced_text(d, (tx + TS + 66, ty + 80), "SETTINGS", F_TITLE, WHITE, 8)
    d.text((tx + TS + 72, ty + 200), "Fire TV settings", font=F_SMALL, fill=GREY)

    base.convert("RGB").save(os.path.join(OUT, "settings_banner.png"))
    print("settings_banner.png")


def make_icon():
    S = 512
    base = vertical_gradient((S, S), BG_TOP, BG_BOTTOM).convert("RGBA")
    TS = 400
    tx = ty = (S - TS) // 2
    tile = vertical_gradient((TS, TS), STEEL_TOP, STEEL_BOTTOM).convert("RGBA")
    base.paste(tile, (tx, ty), rounded_mask((TS, TS), 92))
    draw_gear_on(base, S // 2, S // 2, int(TS * 0.30), WHITE)
    base.convert("RGB").save(os.path.join(OUT, "settings_icon.png"))
    print("settings_icon.png")


if __name__ == "__main__":
    make_banner()
    make_icon()
