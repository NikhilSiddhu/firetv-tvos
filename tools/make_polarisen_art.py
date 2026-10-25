#!/usr/bin/env python3
"""Grade 15 photographs into the Polarisen-style cinematic backdrop set (1280x720).

Polarisen (the Apple-TV-style base) rotates 15 full-bleed pictures behind a glass dock, with a
baked glass band (dock_*) and a blurred variant (grid_*) per picture so nothing has to blur live
on a weak GPU. This replaces the polar-bear set with film-poster-like stills in each streaming
service's palette. 1280x720 keeps textures half the size of 1080p for a 1 GB Stick.
"""
import glob
import os
import random

from PIL import Image, ImageEnhance, ImageFilter, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "polarisen", "launcher", "app", "src", "main", "res", "drawable-nodpi")
os.makedirs(OUT, exist_ok=True)

W, H = 1280, 720
# The dock band in design space (the glass sits at y 610..722 of 720).
DOCK = (40, 610, 1240, 722)


def find(pool, i):
    for cand in (f"cand_{i:02d}.jpg", "cand_00.jpg"):
        p = os.path.join(pool, cand)
        if os.path.exists(p):
            return p
    g = sorted(glob.glob(os.path.join(pool, "cand_*.jpg")))
    return g[-1] if g else None


def crop(im, zoom=1.0, focus=(0.5, 0.5)):
    w, h = im.size
    t = 16 / 9
    cw, ch = (h * t, h) if w / h > t else (w, w / t)
    cw, ch = cw / zoom, ch / zoom
    cx = min(max(w * focus[0], cw / 2), w - cw / 2)
    cy = min(max(h * focus[1], ch / 2), h - ch / 2)
    return im.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))).resize((W, H), Image.LANCZOS)


def grade(im, lift, gain, gamma=1.0, sat=1.0, con=1.08, bright=1.0):
    im = ImageEnhance.Color(im).enhance(sat)
    im = ImageEnhance.Contrast(im).enhance(con)
    im = ImageEnhance.Brightness(im).enhance(bright)
    px = im.load()
    for y in range(H):
        for x in range(0, W, 2):
            r, g, b = px[x, y]
            lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
            k = lum ** gamma
            px[x, y] = (
                max(0, min(255, int(r + (lift[0] - 128) * (1 - k) * 0.5 + (gain[0] - 128) * k * 0.3))),
                max(0, min(255, int(g + (lift[1] - 128) * (1 - k) * 0.5 + (gain[1] - 128) * k * 0.3))),
                max(0, min(255, int(b + (lift[2] - 128) * (1 - k) * 0.5 + (gain[2] - 128) * k * 0.3))),
            )
    return im


def vignette(im, strength=0.5):
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).ellipse([-W * 0.25, -H * 0.35, W * 1.25, H * 1.35], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(W * 0.10))
    inv = Image.eval(m, lambda v: int(v * (1 - strength)))
    im.paste(Image.new("RGB", (W, H), (0, 0, 0)), (0, 0), inv)
    return im


def grain(im, amount=3):
    rnd = random.Random(7)
    px = im.load()
    for y in range(0, H, 2):
        for x in range(0, W, 2):
            n = rnd.randint(-amount, amount)
            r, g, b = px[x, y]
            px[x, y] = (max(0, min(255, r + n)), max(0, min(255, g + n)), max(0, min(255, b + n)))
    return im


def glass_band(im):
    """Blur + tint the dock band exactly as Polarisen's glass would sit over it, baked."""
    b = im.convert("RGB")
    x0, y0, x1, y1 = DOCK
    region = b.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(3))
    b.paste(region, (x0, y0))
    # white top highlight line + tint to lift the band like Liquid Glass
    d = ImageDraw.Draw(b)
    d.rectangle([x0, y0, x1, y0 + 3], fill=(235, 235, 235))
    for _ in range(2):
        top = Image.new("RGB", (x1 - x0, 12), (255, 255, 255))
        mask = Image.new("L", (x1 - x0, 12), 0)
        ImageDraw.Draw(mask).rectangle([0, 0, x1 - x0, 12], fill=28)
        top = top.filter(ImageFilter.GaussianBlur(6))
        b.paste(top, (x0, y0), mask)
    return b


def blur_full(im):
    g = im.filter(ImageFilter.GaussianBlur(11))
    shade = Image.new("RGB", (W, H), (18, 20, 26))
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).rectangle([0, 0, W, H], fill=70)
    m = m.filter(ImageFilter.GaussianBlur(90))
    g.paste(shade, (0, 0), m)
    return g


# slot -> (pool, palette). PALETTES: (lift, gain, gamma, sat)
PAL = {
    "red":    ((34, 8, 12),  (210, 150, 138), 0.92, 0.95),   # Netflix drama
    "teal":   ((6, 20, 32),  (140, 200, 210), 1.00, 1.05),   # Prime night city
    "indigo": ((26, 8, 36),  (215, 150, 200), 0.95, 1.15),   # Hotstar big night
    "neon":   ((10, 22, 30), (235, 170, 120), 0.95, 1.10),   # SonyLIV neon street
    "warm":   ((28, 12, 14), (235, 180, 150), 0.92, 0.95),   # YouTube creator studio
}
T = "/tmp/commons"
SLOTS = [
    (f"{T}/dark_corridor_red_light", "red", 1.10, (0.5, 0.55)),
    (f"{T}/dark_corridor_red_light", "red", 1.18, (0.45, 0.5)),
    (f"{T}/night_city_skyline", "teal", 1.05, (0.4, 0.45)),
    (f"{T}/night_city_skyline", "teal", 1.10, (0.6, 0.5)),
    (f"{T}/night_city_skyline", "teal", 1.0, (0.5, 0.4)),
    (f"{T}/cricket_stadium_night", "indigo", 1.0, (0.5, 0.52)),
    (f"{T}/cricket_stadium_night", "indigo", 1.08, (0.35, 0.42)),
    (f"{T}/cricket_stadium_night", "indigo", 1.05, (0.65, 0.5)),
    (f"{T}/neon_street_rain", "neon", 1.1, (0.5, 0.5)),
    (f"{T}/video_camera_tripod_studio", "neon", 1.1, (0.5, 0.45)),
    (f"{T}/video_studio_camera", "warm", 1.05, (0.5, 0.45)),
    (f"{T}/video_studio_camera", "warm", 1.12, (0.4, 0.5)),
    (f"{T}/podcast_studio_microphone", "warm", 1.05, (0.55, 0.5)),
    (f"{T}/podcast_studio_microphone", "warm", 1.1, (0.45, 0.45)),
    (f"{T}/streaming_setup_desk", "warm", 1.0, (0.5, 0.55)),
]

if __name__ == "__main__":
    for i, (pool, pal, zoom, focus) in enumerate(SLOTS):
        src = find(pool, i)
        if not src:
            print(f"{i:02d} MISSING {pool}"); continue
        im = Image.open(src)
        if im.width / im.height < 1.2 and not (pool.endswith("neon_street_rain")):
            im = im.rotate(-90, expand=True) if im.height > im.width else im
        lift, gain, gamma, sat = PAL[pal]
        bg = vignette(grain(grade(crop(im, zoom, focus), lift, gain, gamma, sat).filter(ImageFilter.GaussianBlur(0.5))))
        bg.save(os.path.join(OUT, f"bg_{i:02d}.jpg"), quality=86, optimize=True)
        glass_band(bg).save(os.path.join(OUT, f"dock_{i:02d}.jpg"), quality=86, optimize=True)
        blur_full(bg).save(os.path.join(OUT, f"grid_{i:02d}.jpg"), quality=84, optimize=True)
        print(f"{i:02d} {os.path.basename(src)} ({pal})")