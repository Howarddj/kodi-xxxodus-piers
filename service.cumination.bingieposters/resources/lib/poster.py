# Turn a wide site logo into a 2:3 poster for skins like Bingie that fit poster art into a fixed frame.
#
# The logo is centred on a full-bleed card and kept inside the poster's central 16:9 band, so views that
# crop the same image to landscape or square (aspectratio "scale") still show the whole logo.
#   - logo with a solid background: the card takes the logo's own edge colour, so it reads as one image
#   - transparent logo: a dark card for light lettering, a light card for dark lettering
LOGO_WIDTH = 0.80      # logo may use this share of the poster width
BAND_HEIGHT = 0.78     # ...and this share of the central 16:9 band's height
MIN_LOGO_WIDTH = 260   # small logos are upscaled (bilinear) to about this width
DARK_CARD = (24, 24, 24)
LIGHT_CARD = (236, 236, 236)


def _trim(w, h, px):
    """Crop fully transparent margins."""
    xs, ys = [], []
    for y in range(h):
        row = y * w * 4
        for x in range(w):
            if px[row + x * 4 + 3] > 8:
                xs.append(x); ys.append(y)
                break
        else:
            continue
        for x in range(w - 1, -1, -1):
            if px[row + x * 4 + 3] > 8:
                xs.append(x)
                break
    if not xs:
        return w, h, px
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    if (x0, y0, x1, y1) == (0, 0, w - 1, h - 1):
        return w, h, px
    nw, nh = x1 - x0 + 1, y1 - y0 + 1
    out = bytearray(nw * nh * 4)
    for y in range(nh):
        s = ((y0 + y) * w + x0) * 4
        out[y * nw * 4:(y + 1) * nw * 4] = px[s:s + nw * 4]
    return nw, nh, out


def _border(w, h, px):
    pts = [(x, 0) for x in range(w)] + [(x, h - 1) for x in range(w)] + \
          [(0, y) for y in range(h)] + [(w - 1, y) for y in range(h)]
    return [tuple(px[(y * w + x) * 4:(y * w + x) * 4 + 4]) for x, y in pts]


def card_colour(w, h, px):
    border = _border(w, h, px)
    opaque = [p for p in border if p[3] > 200]
    if len(opaque) >= 0.9 * len(border):
        counts = {}
        for r, g, b, _a in opaque:
            k = (r // 8, g // 8, b // 8)
            counts[k] = counts.get(k, 0) + 1
        k = max(counts, key=counts.get)
        sel = [p for p in opaque if (p[0] // 8, p[1] // 8, p[2] // 8) == k]
        return tuple(sum(p[i] for p in sel) // len(sel) for i in range(3))
    # transparent logo: judge the lettering's brightness, weighted by opacity
    tot = lum = 0.0
    for i in range(0, len(px), 4):
        a = px[i + 3]
        if a > 32:
            tot += a
            lum += a * (0.2126 * px[i] + 0.7152 * px[i + 1] + 0.0722 * px[i + 2]) / 255.0
    return LIGHT_CARD if tot and lum / tot < 0.45 else DARK_CARD


def _resize(w, h, px, nw, nh):
    """Bilinear resize on premultiplied alpha."""
    out = bytearray(nw * nh * 4)
    sx = (w - 1) / float(max(nw - 1, 1))
    sy = (h - 1) / float(max(nh - 1, 1))
    for y in range(nh):
        fy = y * sy; y0 = int(fy); y1 = min(y0 + 1, h - 1); dy = fy - y0
        for x in range(nw):
            fx = x * sx; x0 = int(fx); x1 = min(x0 + 1, w - 1); dx = fx - x0
            acc = [0.0, 0.0, 0.0, 0.0]
            for (xx, yy, wt) in ((x0, y0, (1 - dx) * (1 - dy)), (x1, y0, dx * (1 - dy)),
                                 (x0, y1, (1 - dx) * dy), (x1, y1, dx * dy)):
                i = (yy * w + xx) * 4
                a = px[i + 3] * wt
                acc[0] += px[i] * a; acc[1] += px[i + 1] * a; acc[2] += px[i + 2] * a; acc[3] += a
            o = (y * nw + x) * 4
            if acc[3] > 0:
                out[o] = min(255, int(acc[0] / acc[3] + 0.5))
                out[o + 1] = min(255, int(acc[1] / acc[3] + 0.5))
                out[o + 2] = min(255, int(acc[2] / acc[3] + 0.5))
                out[o + 3] = min(255, int(acc[3] + 0.5))
    return out


def _feather(w, h, px, card):
    """Fade an opaque logo's outer edge into the card when its background is close to the card colour
    (soft vignettes and gradients would otherwise show a hard box)."""
    border = _border(w, h, px)
    if any(p[3] < 250 for p in border):
        return px
    dist = sum(abs(p[0] - card[0]) + abs(p[1] - card[1]) + abs(p[2] - card[2]) for p in border) / float(len(border))
    if dist > 45:
        return px                               # busy edge (a picture): keep it crisp
    n = max(2, min(16, w // 12, h // 6))
    px = bytearray(px)
    for y in range(h):
        ey = min(y, h - 1 - y)
        for x in range(w):
            e = min(x, w - 1 - x, ey)
            if e >= n:
                continue
            i = (y * w + x) * 4 + 3
            px[i] = px[i] * (e + 1) // (n + 1)
    return px


def make(w, h, px):
    """RGBA logo -> (width, height, RGB bytearray) 2:3 poster."""
    w, h, px = _trim(w, h, px)
    card = card_colour(w, h, px)
    px = _feather(w, h, px, card)
    if w < MIN_LOGO_WIDTH:
        nw = MIN_LOGO_WIDTH
        nh = max(1, int(round(h * nw / float(w))))
        px, w, h = _resize(w, h, px, nw, nh), nw, nh
    if w < 1.4 * h:
        # near-square pictures (Cumination's own menu art), not logos: fill the poster width
        cw = int(w / 0.96 + 0.5)
    else:
        cw = int(w / LOGO_WIDTH + 0.5)
        if h > BAND_HEIGHT * cw * 9 / 16.0:      # tall logos: widen so they still fit the 16:9 band
            cw = int(h / BAND_HEIGHT * 16 / 9.0 + 0.5)
    if h > 0.96 * cw * 1.5:                      # portrait pictures: the poster must fit the height too
        cw = int(h / 0.96 / 1.5 + 0.999)
    cw += cw % 2
    ch = cw * 3 // 2
    out = bytearray(bytes(card) * (cw * ch))
    ox, oy = (cw - w) // 2, (ch - h) // 2
    for y in range(h):
        for x in range(w):
            i = (y * w + x) * 4
            a = px[i + 3]
            if not a:
                continue
            o = ((oy + y) * cw + ox + x) * 3
            if a == 255:
                out[o:o + 3] = px[i:i + 3]
            else:
                for c in range(3):
                    out[o + c] = (px[i + c] * a + out[o + c] * (255 - a)) // 255
    return cw, ch, out
