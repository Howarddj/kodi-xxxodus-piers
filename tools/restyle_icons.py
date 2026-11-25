#!/usr/bin/env python3
"""
Restyle XXX-O-DUS menu icons: smaller, centred, rounded corners, transparent surround.

Kodi skins decide where an icon box sits and how big it is; an add-on only supplies the image.
Putting each icon on a transparent square canvas, scaled down and centred, makes it render
smaller and centred (horizontally and vertically) inside whatever box the skin uses.

    python3 tools/restyle_icons.py [--scale 0.70] [--radius 0.14] [--size 512] DIR [...]
    python3 tools/restyle_icons.py --preview out.png DIR       # contact sheet only, no changes

--scale   fraction of the canvas the icon's longest side may occupy
--radius  corner radius as a fraction of the icon's shorter side
"""
import argparse, os, sys
from PIL import Image, ImageDraw

SS = 4  # supersampling for smooth anti-aliased corners


def rounded_mask(size, radius):
    w, h = size
    big = Image.new('L', (w * SS, h * SS), 0)
    ImageDraw.Draw(big).rounded_rectangle((0, 0, w * SS - 1, h * SS - 1), radius=radius * SS, fill=255)
    return big.resize((w, h), Image.LANCZOS)


def restyle(img, canvas=512, scale=0.70, radius=0.14):
    img = img.convert('RGBA')
    box = int(round(canvas * scale))
    ratio = min(box / img.width, box / img.height)
    w, h = max(1, int(round(img.width * ratio))), max(1, int(round(img.height * ratio)))
    icon = img.resize((w, h), Image.LANCZOS)
    mask = rounded_mask((w, h), int(round(min(w, h) * radius)))
    alpha = Image.composite(icon.getchannel('A'), Image.new('L', (w, h), 0), mask)  # keep existing transparency
    icon.putalpha(alpha)
    out = Image.new('RGBA', (canvas, canvas), (0, 0, 0, 0))
    out.paste(icon, ((canvas - w) // 2, (canvas - h) // 2), icon)
    return out


def files(roots):
    for root in roots:
        for dp, _, fs in os.walk(root):
            for f in sorted(fs):
                if f.lower().endswith('.png'):
                    yield os.path.join(dp, f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dirs', nargs='+')
    ap.add_argument('--scale', type=float, default=0.70)
    ap.add_argument('--radius', type=float, default=0.14)
    ap.add_argument('--size', type=int, default=512)
    ap.add_argument('--preview')
    a = ap.parse_args()
    paths = list(files(a.dirs))
    if a.preview:
        sample = paths[:: max(1, len(paths) // 12)][:12]
        cell = 220
        sheet = Image.new('RGB', (cell * len(sample), cell * 2), (0, 0, 0))
        for i, p in enumerate(sample):
            out = restyle(Image.open(p), a.size, a.scale, a.radius).resize((cell, cell), Image.LANCZOS)
            for row, bg in enumerate(((30, 30, 30), (200, 200, 200))):
                tile = Image.new('RGBA', (cell, cell), bg + (255,)); tile.alpha_composite(out)
                sheet.paste(tile.convert('RGB'), (i * cell, row * cell))
        sheet.save(a.preview)
        print('preview of %d icons -> %s' % (len(sample), a.preview))
        return
    for p in paths:
        restyle(Image.open(p), a.size, a.scale, a.radius).save(p, optimize=True)
    print('restyled %d icons' % len(paths))


if __name__ == '__main__':
    main()
