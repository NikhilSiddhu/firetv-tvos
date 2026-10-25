#!/usr/bin/env python3
"""Draw the Liquid Glass wallpapers for the launcher theme.

tvOS 26 introduced the Liquid Glass design language and tvOS 27 keeps it: deep near-black
backgrounds, large fluid glass forms with a bright specular rim, and soft chromatic light
blooming out of them. Nothing is drawn in the middle-left of the frame, where the launcher's
clock, the focused app's name and the dock live, so the picture never fights the UI.

Outputs three 1920x1080 JPEGs into themes/liquidglass/wallpapers/:

  morning.jpg   cool daylight glass, pale blue and mint
  evening.jpg   warm glass, amber and rose, a low sun
  night.jpg     the default: violet and electric blue on black

The pictures stay dark and carry a little grain, because the launcher decodes wallpapers in
RGB_565 on a 1 GB stick and smooth dark gradients band in 16-bit colour; the grain dithers it.
"""
from PIL import Image, ImageDraw, ImageFilter
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "themes", "liquidglass", "wallpapers")
os.makedirs(OUT, exist_ok=True)

W, H = 1920, 1080


# ---------------------------------------------------------------- helpers


def vertical_gradient(size, top, bottom):
    w, h = size
    strip = Image.new("RGB", (1, h))
    px = strip.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        px[0, y] = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
    return strip.resize((w, h))


def radial_light(size, centre, radius, colour, strength=1.0):
    """A soft round light: opaque at the centre, fading to nothing at `radius`."""
    w, h = size
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    steps = 48
    for i in range(steps, 0, -1):
        t = i / steps                      # 1 at the rim, 0 at the centre
        r = radius * t
        alpha = int(255 * strength * (1 - t) ** 2.2)
        if alpha <= 0:
            continue
        d.ellipse([centre[0] - r, centre[1] - r, centre[0] + r, centre[1] + r],
                  fill=colour + (alpha,))
    return layer.filter(ImageFilter.GaussianBlur(radius * 0.16))


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def glass_form(size, centre, radius, tilt, rim_colour, fill_top, fill_bottom, sheen,
               rim_colour2=None):
    """A liquid-glass disc: dark refractive body, iridescent rim, and a specular crescent.

    It is built as an ellipse squashed on one axis (the `tilt`), so it reads as a pane seen at
    an angle rather than a flat circle. The rim's colour runs around the edge from `rim_colour`
    to `rim_colour2` and back, which is what makes an edge look like glass instead of a stroke,
    and a soft caustic sits on the lower inside edge where the light comes through.
    """
    w, h = size
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rim_colour2 = rim_colour2 or rim_colour

    ry = radius * tilt
    # body: a vertical gradient clipped to the ellipse
    body = vertical_gradient((int(radius * 2), int(ry * 2)), fill_top, fill_bottom).convert("RGBA")
    mask = Image.new("L", body.size, 0)
    ImageDraw.Draw(mask).ellipse([0, 0, body.size[0] - 1, body.size[1] - 1], fill=255)
    body.putalpha(mask)
    layer.alpha_composite(body, (int(centre[0] - radius), int(centre[1] - ry)))

    # rim: concentric ellipses, brightest just inside the edge, hue turning around the circle
    for i in range(24):
        t = i / 23
        rx = radius * (1 - t * 0.05)
        ry2 = ry * (1 - t * 0.05)
        alpha = int(180 * (1 - t) ** 2)
        if alpha <= 0:
            continue
        for deg in range(0, 360, 6):
            # two turns of the hue around the rim: bright at both top-left and bottom-right
            k = 0.5 - 0.5 * math.cos(math.radians(deg * 2 - 140))
            d.arc([centre[0] - rx, centre[1] - ry2, centre[0] + rx, centre[1] + ry2],
                  start=deg - 1, end=deg + 7,
                  fill=mix(rim_colour, rim_colour2, k) + (alpha,), width=3)

    # specular crescent: an offset ellipse of light near the top-left of the form
    spec = Image.new("RGBA", size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(spec)
    sd.ellipse([centre[0] - radius * 0.78, centre[1] - ry * 0.86,
                centre[0] + radius * 0.10, centre[1] + ry * 0.06],
               fill=sheen + (52,))
    spec = spec.filter(ImageFilter.GaussianBlur(radius * 0.09))
    layer.alpha_composite(spec)

    # caustic: the light that came through the glass, pooled on the lower inside edge
    caustic = Image.new("RGBA", size, (0, 0, 0, 0))
    cd = ImageDraw.Draw(caustic)
    cd.arc([centre[0] - radius * 0.86, centre[1] - ry * 0.86,
            centre[0] + radius * 0.86, centre[1] + ry * 0.86],
           start=26, end=154, fill=sheen + (66,), width=int(max(3, radius * 0.035)))
    caustic = caustic.filter(ImageFilter.GaussianBlur(radius * 0.07))
    layer.alpha_composite(caustic)

    # clip the crescent to the disc so it does not wash outside
    clip = Image.new("L", size, 0)
    ImageDraw.Draw(clip).ellipse([centre[0] - radius, centre[1] - ry,
                                  centre[0] + radius, centre[1] + ry], fill=255)
    clip = clip.filter(ImageFilter.GaussianBlur(2))
    layer.putalpha(Image.composite(layer.getchannel("A"), Image.new("L", size, 0), clip))
    return layer


def grain(img, amount=5):
    """A little noise, to stop 16-bit dark gradients banding."""
    noise = Image.effect_noise(img.size, amount * 4).convert("L")
    noise = noise.filter(ImageFilter.GaussianBlur(0.4))
    return Image.blend(img, Image.merge("RGB", (noise, noise, noise)), amount / 100.0)


def save(img, name, quality=86):
    path = os.path.join(OUT, name)
    img.convert("RGB").save(path, "JPEG", quality=quality, optimize=True, progressive=True)
    print(f"{name:14s} {os.path.getsize(path) / 1024:6.1f} KB")


# ---------------------------------------------------------------- the three moods


def build(name, base, lights, forms, quality=86):
    img = vertical_gradient((W, H), base[0], base[1]).convert("RGBA")
    for spec in lights:
        img.alpha_composite(radial_light((W, H), **spec))
    for spec in forms:
        img.alpha_composite(glass_form((W, H), **spec))
    out = grain(img.convert("RGB"), 4.5)
    save(out, name, quality)


def night():
    build(
        "night.jpg",
        base=((4, 5, 10), (9, 8, 18)),
        lights=[
            dict(centre=(1460, 300), radius=900, colour=(58, 84, 210), strength=0.55),
            dict(centre=(1720, 760), radius=720, colour=(120, 62, 210), strength=0.42),
            dict(centre=(240, 940), radius=620, colour=(24, 92, 140), strength=0.30),
            dict(centre=(980, 120), radius=520, colour=(40, 60, 150), strength=0.22),
        ],
        forms=[
            dict(centre=(1450, 430), radius=330, tilt=0.92,
                 rim_colour=(178, 198, 255), fill_top=(28, 34, 66), fill_bottom=(10, 12, 26),
                 sheen=(210, 224, 255)),
            dict(centre=(1700, 830), radius=190, tilt=0.86,
                 rim_colour=(150, 130, 235), fill_top=(38, 28, 70), fill_bottom=(14, 10, 28),
                 sheen=(226, 214, 255)),
        ],
    )


def morning():
    build(
        "morning.jpg",
        base=((5, 8, 12), (12, 16, 22)),
        lights=[
            dict(centre=(1520, 240), radius=1000, colour=(96, 170, 210), strength=0.5),
            dict(centre=(1180, 900), radius=760, colour=(70, 180, 160), strength=0.34),
            dict(centre=(300, 200), radius=620, colour=(150, 190, 220), strength=0.22),
        ],
        forms=[
            dict(centre=(1440, 470), radius=310, tilt=0.94,
                 rim_colour=(198, 232, 246), fill_top=(26, 48, 58), fill_bottom=(10, 18, 24),
                 sheen=(226, 246, 252)),
            dict(centre=(1130, 800), radius=165, tilt=0.84,
                 rim_colour=(150, 216, 205), fill_top=(22, 56, 54), fill_bottom=(10, 22, 22),
                 sheen=(214, 246, 240)),
        ],
    )


def evening():
    build(
        "evening.jpg",
        base=((9, 5, 6), (16, 9, 10)),
        lights=[
            dict(centre=(1500, 620), radius=1000, colour=(214, 116, 62), strength=0.46),
            dict(centre=(1240, 260), radius=820, colour=(186, 74, 108), strength=0.38),
            dict(centre=(520, 940), radius=680, colour=(96, 52, 120), strength=0.30),
            dict(centre=(300, 160), radius=560, colour=(70, 40, 90), strength=0.20),
        ],
        forms=[
            dict(centre=(1430, 520), radius=320, tilt=0.9,
                 rim_colour=(255, 206, 172), fill_top=(62, 34, 30), fill_bottom=(20, 11, 12),
                 sheen=(255, 228, 200)),
            dict(centre=(1660, 850), radius=180, tilt=0.86,
                 rim_colour=(226, 150, 168), fill_top=(58, 26, 44), fill_bottom=(18, 10, 16),
                 sheen=(255, 214, 222)),
        ],
    )


if __name__ == "__main__":
    night()
    morning()
    evening()
