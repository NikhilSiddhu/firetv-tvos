#!/usr/bin/env python3
"""Grade five photographs into the cinematic backdrops the dock apps show behind the glass.

Apple TV's home screen puts the focused app's top-shelf artwork behind everything. This stick has
no network and the launcher is not allowed one, so the stills are graded here and bundled in the
APK instead. Each is a real photograph from Wikimedia Commons, cropped to 16:9, colour-graded to
that service's palette, vignetted and lightly grained so it reads as a film still at ten feet.

Sources and licences are in CREDITS.md beside this script. Output goes to the launcher's
res/drawable-nodpi as 1280x720 JPEGs.

    tools/make_cinematic_backdrops.py <photo-folder>

The photo folder holds netflix.jpg, prime.jpg, hotstar.jpg, sonyliv.jpg and youtube.jpg.
"""
import os
import random
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "cleanyourtv-latest", "launcher",
                   "app", "src", "main", "res", "drawable-nodpi")
os.makedirs(OUT, exist_ok=True)

W, H = 1280, 720


def crop_16_9(im, zoom=1.0, focus=(0.5, 0.5)):
    w, h = im.size
    target = 16 / 9
    # the largest 16:9 box inside the picture, then zoom in a little
    if w / h > target:
        ch, cw = h, h * target
    else:
        cw, ch = w, w / target
    cw, ch = cw / zoom, ch / zoom
    cx = min(max(w * focus[0], cw / 2), w - cw / 2)
    cy = min(max(h * focus[1], ch / 2), h - ch / 2)
    box = (int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))
    return im.crop(box).resize((W, H), Image.LANCZOS)


def grade(im, lift, gain, gamma=1.0, saturation=1.0, contrast=1.0, brightness=1.0):
    """A simple three-way grade: lift the shadows toward `lift`, tint the highlights `gain`."""
    im = ImageEnhance.Color(im).enhance(saturation)
    im = ImageEnhance.Contrast(im).enhance(contrast)
    im = ImageEnhance.Brightness(im).enhance(brightness)
    px = im.load()
    for y in range(H):
        for x in range(W):
            r, g, b = px[x, y]
            lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
            k = lum ** gamma
            # shadows take the lift colour, highlights the gain colour
            nr = r + (lift[0] - 128) * (1 - k) * 0.55 + (gain[0] - 128) * k * 0.35
            ng = g + (lift[1] - 128) * (1 - k) * 0.55 + (gain[1] - 128) * k * 0.35
            nb = b + (lift[2] - 128) * (1 - k) * 0.55 + (gain[2] - 128) * k * 0.35
            px[x, y] = (max(0, min(255, int(nr))), max(0, min(255, int(ng))), max(0, min(255, int(nb))))
    return im


def vignette(im, strength=0.6):
    w, h = im.size
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).ellipse([-w * 0.2, -h * 0.3, w * 1.2, h * 1.3], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(w * 0.10))
    dark = Image.new("RGB", (w, h), (0, 0, 0))
    inv = Image.eval(mask, lambda v: int(v * (1 - strength)))
    im.paste(dark, (0, 0), inv)
    return im


def grain(im, amount=4):
    px = im.load()
    rnd = random.Random(11)
    for y in range(0, H, 2):
        for x in range(0, W, 2):
            n = rnd.randint(-amount, amount)
            r, g, b = px[x, y]
            px[x, y] = (max(0, min(255, r + n)), max(0, min(255, g + n)), max(0, min(255, b + n)))
    return im


def soften(im, radius=0.8):
    return im.filter(ImageFilter.GaussianBlur(radius))


def save(im, name):
    im.save(os.path.join(OUT, name), quality=84, optimize=True)
    print(name)


def netflix(src):
    im = crop_16_9(Image.open(src).convert("RGB"), zoom=1.15, focus=(0.5, 0.55))
    im = grade(im, lift=(30, 6, 10), gain=(200, 150, 140), gamma=0.9,
               saturation=0.9, contrast=1.15, brightness=0.78)
    im = vignette(im, 0.72)
    save(grain(soften(im, 0.7)), "backdrop_netflix.jpg")


def prime(src):
    im = crop_16_9(Image.open(src).convert("RGB"), zoom=1.1, focus=(0.5, 0.45))
    im = grade(im, lift=(4, 18, 30), gain=(150, 200, 215), gamma=1.0,
               saturation=1.05, contrast=1.12, brightness=0.80)
    im = vignette(im, 0.62)
    save(grain(soften(im, 0.6)), "backdrop_prime.jpg")


def hotstar(src):
    im = crop_16_9(Image.open(src).convert("RGB"), zoom=1.0, focus=(0.5, 0.5))
    im = grade(im, lift=(24, 6, 34), gain=(210, 160, 200), gamma=0.95,
               saturation=1.15, contrast=1.10, brightness=0.86)
    im = vignette(im, 0.58)
    save(grain(soften(im, 0.8)), "backdrop_hotstar.jpg")


def sonyliv(src):
    im = crop_16_9(Image.open(src).convert("RGB"), zoom=1.1, focus=(0.5, 0.5))
    im = grade(im, lift=(6, 24, 30), gain=(230, 180, 130), gamma=0.95,
               saturation=1.10, contrast=1.15, brightness=0.80)
    im = vignette(im, 0.68)
    save(grain(soften(im, 0.9)), "backdrop_sonyliv.jpg")


def youtube(src):
    im = crop_16_9(Image.open(src).convert("RGB"), zoom=1.05, focus=(0.5, 0.45))
    im = grade(im, lift=(26, 8, 10), gain=(240, 170, 150), gamma=0.92,
               saturation=0.95, contrast=1.12, brightness=0.72)
    im = vignette(im, 0.70)
    save(grain(soften(im, 0.7)), "backdrop_youtube.jpg")


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "backdrop_src")
    netflix(os.path.join(folder, "netflix.jpg"))
    prime(os.path.join(folder, "prime.jpg"))
    hotstar(os.path.join(folder, "hotstar.jpg"))
    sonyliv(os.path.join(folder, "sonyliv.jpg"))
    youtube(os.path.join(folder, "youtube.jpg"))
