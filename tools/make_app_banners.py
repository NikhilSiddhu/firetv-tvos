#!/usr/bin/env python3
"""Draw the dock tiles in the shape and style Apple TV gives these apps.

Fire OS hands the launcher each app's own banner: a square logo on black, a postage stamp in the
corner, or nothing at all. tvOS draws a 5:3 tile instead, in the app's own colour, with the real
brand mark centred on it. The launcher lets a theme swap a tile's artwork for a `banner_*` drawable
bundled in the APK (`app_banners`), so these are drawn here from the official logos in `brand/`
and copied into the launcher's res/drawable-nodpi.

Outputs (640x384 PNG, 5:3):
  banner_netflix.png    the red N on black, as Netflix's own icon
  banner_prime.png      the 2024 prime video wordmark on Amazon's dark blue
  banner_hotstar.png    the star and wordmark in white on the JioHotstar indigo-to-violet
  banner_sonyliv.png    the SonyLIV app icon on black
  banner_youtube.png    the full-colour YouTube logo on white, as the YouTube app icon

The brand files are from Wikimedia Commons; their titles and licences are in CREDITS.md.
"""
import os

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
BRAND = os.path.join(HERE, "brand")
OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "cleanyourtv-latest", "launcher",
                   "app", "src", "main", "res", "drawable-nodpi")
os.makedirs(OUT, exist_ok=True)

W, H = 640, 384


def vgrad(top, bottom, size=(W, H)):
    w, h = size
    strip = Image.new("RGB", (1, h))
    px = strip.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        px[0, y] = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
    return strip.resize((w, h))


def diagonal(stops, size=(W, H)):
    """A 45-degree gradient across the tile, from the top-left corner's stop to the bottom-right's."""
    w, h = size
    small = Image.new("RGB", (64, 64))
    px = small.load()
    for y in range(64):
        for x in range(64):
            t = (x + y) / 126
            for i in range(len(stops) - 1):
                p0, c0 = stops[i]
                p1, c1 = stops[i + 1]
                if p0 <= t <= p1:
                    k = (t - p0) / max(p1 - p0, 1e-6)
                    px[x, y] = tuple(int(c0[j] + (c1[j] - c0[j]) * k) for j in range(3))
                    break
    return small.resize((w, h), Image.BICUBIC)


def logo(name, width=None, height=None):
    """One brand file, trimmed to its visible pixels, scaled to the asked size (aspect kept)."""
    im = Image.open(os.path.join(BRAND, name)).convert("RGBA")
    box = im.split()[3].getbbox()
    if box:
        im = im.crop(box)
    if width:
        height = round(im.height * width / im.width)
    else:
        width = round(im.width * height / im.height)
    return im.resize((width, height), Image.LANCZOS)


def glow(img, centre, radius, colour, strength=0.5):
    layer = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(layer)
    for i in range(28, 0, -1):
        r = radius * i / 28
        d.ellipse([centre[0] - r, centre[1] - r, centre[0] + r, centre[1] + r],
                  fill=int(255 * strength * (1 - i / 28) ** 1.6))
    layer = layer.filter(ImageFilter.GaussianBlur(radius * 0.05))
    img.paste(Image.new("RGB", img.size, colour), (0, 0), layer)


def place(img, mark, cy=None, scale=1.0):
    x = (W - mark.width) // 2
    y = (H - mark.height) // 2 if cy is None else round(cy - mark.height / 2)
    img.paste(mark, (x, y), mark)


def save(img, name):
    img.convert("RGB").save(os.path.join(OUT, name), optimize=True)
    print(name)


def netflix():
    # Netflix's icon is the red N on its own black square, so the square is the tile.
    img = Image.new("RGB", (W, H), (0, 0, 0))
    place(img, logo("netflix_n_trans.png", height=H))
    save(img, "banner_netflix.png")


def prime():
    img = vgrad((16, 24, 32), (5, 9, 13))
    place(img, logo("prime_video_trans.png", width=round(W * 0.62)))
    save(img, "banner_prime.png")


def hotstar():
    img = diagonal([(0.0, (18, 16, 62)), (0.55, (44, 26, 102)), (1.0, (94, 42, 142))])
    glow(img, (W * 0.5, H * 0.5), W * 0.42, (120, 90, 200), 0.35)
    mark = logo("jiohotstar.png", width=round(W * 0.70))
    # The Commons file is black on transparent: recolour it white, as the app's own icon has it.
    white = Image.new("RGBA", mark.size, (255, 255, 255, 255))
    white.putalpha(mark.split()[3])
    place(img, white)
    save(img, "banner_hotstar.png")


def sonyliv():
    img = Image.new("RGB", (W, H), (4, 4, 6))
    glow(img, (W * 0.5, H * 0.5), W * 0.36, (60, 30, 90), 0.5)
    place(img, logo("sonyliv.png", height=round(H * 0.80)))
    save(img, "banner_sonyliv.png")


def youtube():
    img = vgrad((255, 255, 255), (244, 244, 246))
    place(img, logo("youtube_full_trans.png", width=round(W * 0.66)))
    save(img, "banner_youtube.png")


if __name__ == "__main__":
    netflix()
    prime()
    hotstar()
    sonyliv()
    youtube()
