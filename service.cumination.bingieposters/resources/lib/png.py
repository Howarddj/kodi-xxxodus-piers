# Minimal pure-Python PNG reader/writer (Kodi ships no image library).
# Reads 8-bit grey/RGB/palette/grey+alpha/RGBA and 1/2/4-bit palette or grey, non-interlaced.
# Everything is returned as a flat bytearray of RGBA pixels.
import struct
import zlib

SIG = b'\x89PNG\r\n\x1a\n'


class PNGError(Exception):
    pass


def _chunks(data):
    pos = 8
    while pos < len(data):
        length, = struct.unpack('>I', data[pos:pos + 4])
        ctype = data[pos + 4:pos + 8]
        yield ctype, data[pos + 8:pos + 8 + length]
        pos += 12 + length


def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def read(data):
    """bytes -> (width, height, bytearray RGBA)."""
    if data[:8] != SIG:
        raise PNGError('not a PNG')
    ihdr = None
    palette = b''
    trns = None
    idat = []
    for ctype, body in _chunks(data):
        if ctype == b'IHDR':
            ihdr = struct.unpack('>IIBBBBB', body)
        elif ctype == b'PLTE':
            palette = body
        elif ctype == b'tRNS':
            trns = body
        elif ctype == b'IDAT':
            idat.append(body)
        elif ctype == b'IEND':
            break
    if not ihdr:
        raise PNGError('no IHDR')
    w, h, depth, ctype, _comp, _filt, interlace = ihdr
    if interlace:
        raise PNGError('interlaced PNG not supported')
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(ctype)
    if channels is None:
        raise PNGError('colour type %d' % ctype)
    if depth == 16 or (depth != 8 and ctype not in (0, 3)):
        raise PNGError('bit depth %d for colour type %d' % (depth, ctype))
    raw = zlib.decompress(b''.join(idat))
    bits = depth * channels
    bpp = max(1, bits // 8)                      # bytes per complete pixel, for filtering
    stride = (w * bits + 7) // 8
    out = bytearray(w * h * 4)
    prev = bytearray(stride)
    pos = 0
    for y in range(h):
        ftype = raw[pos]
        line = bytearray(raw[pos + 1:pos + 1 + stride])
        pos += 1 + stride
        if ftype == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 255
        elif ftype == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif ftype == 3:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 255
        elif ftype == 4:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                upleft = prev[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + _paeth(left, prev[i], upleft)) & 255
        elif ftype != 0:
            raise PNGError('bad filter %d' % ftype)
        prev = line
        o = y * w * 4
        if depth < 8:                            # 1/2/4-bit palette or grey
            per = 8 // depth
            mask = (1 << depth) - 1
            for x in range(w):
                v = (line[x // per] >> (8 - depth * (x % per + 1))) & mask
                if ctype == 3:
                    r, g, b = palette[v * 3:v * 3 + 3]
                    a = trns[v] if trns and v < len(trns) else 255
                else:
                    r = g = b = v * 255 // mask
                    a = 0 if trns and len(trns) >= 2 and v == struct.unpack('>H', trns[:2])[0] else 255
                out[o:o + 4] = bytes((r, g, b, a))
                o += 4
            continue
        if ctype == 6:
            out[o:o + w * 4] = line
        elif ctype == 2:
            key = struct.unpack('>HHH', trns[:6]) if trns and len(trns) >= 6 else None
            for x in range(w):
                r, g, b = line[x * 3:x * 3 + 3]
                a = 0 if key and (r, g, b) == key else 255
                out[o:o + 4] = bytes((r, g, b, a))
                o += 4
        elif ctype == 3:
            for x in range(w):
                v = line[x]
                r, g, b = palette[v * 3:v * 3 + 3]
                a = trns[v] if trns and v < len(trns) else 255
                out[o:o + 4] = bytes((r, g, b, a))
                o += 4
        elif ctype == 4:
            for x in range(w):
                v, a = line[x * 2], line[x * 2 + 1]
                out[o:o + 4] = bytes((v, v, v, a))
                o += 4
        else:                                    # grey
            key = struct.unpack('>H', trns[:2])[0] if trns and len(trns) >= 2 else None
            for x in range(w):
                v = line[x]
                out[o:o + 4] = bytes((v, v, v, 0 if v == key else 255))
                o += 4
    return w, h, out


def write_rgb(w, h, rgb):
    """Encode a flat RGB bytearray as an 8-bit RGB PNG (filter 'none', zlib level 9)."""
    rows = bytearray()
    stride = w * 3
    for y in range(h):
        rows.append(0)
        rows += rgb[y * stride:(y + 1) * stride]

    def chunk(t, body):
        return struct.pack('>I', len(body)) + t + body + struct.pack('>I', zlib.crc32(t + body) & 0xffffffff)
    return (SIG + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(bytes(rows), 9)) + chunk(b'IEND', b''))
