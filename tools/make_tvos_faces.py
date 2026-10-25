#!/usr/bin/env python3
"""tvOS-27-style 16:9 faces for canvasOS.

canvasOS reads a tile's art from
  /sdcard/Android/data/com.getisolated.canvasos/files/tiles/<package>.jpg
and otherwise falls back to whatever the APK declares (a banner, or a bare icon
on a flat gradient — which is what makes some tiles look unfinished).

This draws the tiles Apple's own home screen uses: one deep glass card, a soft
top light, the brand artwork centred, and nothing else. All faces share the same
geometry, so a grid of them reads as one system instead of nine unrelated logos.

  ./.imgvenv/bin/python tools/make_tvos_faces.py --out dist/faces <apk-dir>

For each APK in <apk-dir> it reads the package name, the label and the best
available artwork (banner first, then the largest icon), draws the face, and
names it <package>.jpg.
"""
import argparse
import os
import re
import subprocess
import zipfile

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 800, 450
FONT_PATH = "app/src/main/assets/inter.ttf"  # shipped inside canvasOS
AAPT = "/Users/nikhilsiddhu/Android/sdk/build-tools/36.0.0/aapt"

# Apple-ish card: near-black, a touch cooler at the top, never flat.
TOP = (26, 26, 30)
BOTTOM = (10, 10, 12)
TEXT = (255, 255, 255)


def badging(apk):
    out = subprocess.run([AAPT, "dump", "badging", apk], capture_output=True, text=True).stdout
    pkg = re.search(r"package: name='([^']+)'", out)
    label = re.search(r"application-label:'([^']*)'", out)
    banner = re.search(r"application:banner='([^']+)'", out)
    icons = dict(
        (int(m.group(1)), m.group(2))
        for m in re.finditer(r"application-icon-(\d+):'([^']+)'", out)
    )
    return (
        pkg.group(1) if pkg else None,
        label.group(1) if label else None,
        banner.group(1) if banner else None,
        icons.get(max(icons)) if icons else None,
    )


def extract(apk, member):
    with zipfile.ZipFile(apk) as z:
        try:
            data = z.read(member)
        except KeyError:
            return None
    from io import BytesIO

    try:
        return Image.open(BytesIO(data)).convert("RGBA")
    except Exception:
        return None


def card():
    img = Image.new("RGB", (W, H), BOTTOM)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        d.line(
            [(0, y), (W, y)],
            fill=(
                round(TOP[0] + (BOTTOM[0] - TOP[0]) * t),
                round(TOP[1] + (BOTTOM[1] - TOP[1]) * t),
                round(TOP[2] + (BOTTOM[2] - TOP[2]) * t),
            ),
        )
    # Soft light from the top edge, the way an Apple tile catches the room.
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse(
        (-W // 3, -H, W + W // 3, H // 2), fill=46
    )
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    img = Image.composite(Image.new("RGB", (W, H), (70, 70, 78)), img, glow)
    return img


def face(art, label, banner_art):
    img = card()
    if art is None:
        return img

    # Banner art already carries its own background: use it nearly full-bleed so
    # the branded tiles (Netflix, Prime, VLC) keep their identity.
    if banner_art:
        w = 720
        a = art.resize((w, round(art.height * w / art.width)), Image.LANCZOS)
        if a.height > 405:
            w2 = round(art.width * 405 / art.height)
            a = art.resize((w2, 405), Image.LANCZOS)
        img.paste(a, ((W - a.width) // 2, (H - a.height) // 2), a)
        return img

    # Icon-only apps get the icon and its name, centred, like a tvOS system app.
    h = 200
    a = art.resize((round(art.width * h / art.height), h), Image.LANCZOS)
    top = (H - h) // 2 - 34
    img.paste(a, ((W - a.width) // 2, top), a)

    if label:
        size = 44
        try:
            font = ImageFont.truetype(FONT_PATH, size)
        except Exception:
            font = ImageFont.load_default()
        d = ImageDraw.Draw(img)
        tw = d.textlength(label, font=font)
        while tw > W - 120 and size > 24:
            size -= 2
            font = ImageFont.truetype(FONT_PATH, size)
            tw = d.textlength(label, font=font)
        d.text(((W - tw) / 2, top + h + 34), label, font=font, fill=TEXT)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("apk_dir")
    ap.add_argument("--out", default="dist/faces")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    made = 0
    for name in sorted(os.listdir(args.apk_dir)):
        if not name.endswith(".apk"):
            continue
        path = os.path.join(args.apk_dir, name)
        pkg, label, banner, icon = badging(path)
        if not pkg:
            print(f"skip {name}: no package")
            continue
        art, is_banner = None, False
        if banner:
            art = extract(path, banner)
            is_banner = art is not None
        if art is None and icon:
            art = extract(path, icon)
        if art is None:
            print(f"skip {pkg}: no artwork")
            continue
        out = os.path.join(args.out, f"{pkg}.jpg")
        face(art, label, is_banner).save(out, "JPEG", quality=93, subsampling=0)
        print(f"{pkg:42s} {'banner' if is_banner else 'icon  '}  {label}")
        made += 1
    print(f"\n{made} faces -> {args.out}")


if __name__ == "__main__":
    main()
