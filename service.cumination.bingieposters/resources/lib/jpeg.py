# Minimal pure-Python JPEG reader/writer (Kodi ships no image library).
# Reads baseline, extended and progressive Huffman JPEGs (greyscale or YCbCr, any sampling, restart markers).
# Writes baseline 4:4:4 JPEGs with the standard tables.
import math
import struct

SIG = b'\xff\xd8'


class JPEGError(Exception):
    pass


ZIGZAG = [0, 1, 8, 16, 9, 2, 3, 10, 17, 24, 32, 25, 18, 11, 4, 5, 12, 19, 26, 33, 40, 48, 41, 34, 27, 20, 13, 6, 7,
          14, 21, 28, 35, 42, 49, 56, 57, 50, 43, 36, 29, 22, 15, 23, 30, 37, 44, 51, 58, 59, 52, 45, 38, 31, 39, 46,
          53, 60, 61, 54, 47, 55, 62, 63]

# 8x8 DCT basis: COS[x][u] = c(u)/2 * cos((2x+1) u pi / 16)
COS = [[(math.sqrt(0.5) if u == 0 else 1.0) / 2 * math.cos((2 * x + 1) * u * math.pi / 16) for u in range(8)]
       for x in range(8)]


# ---------------------------------------------------------------------------------------------- decoding
class _Huffman(object):
    def __init__(self, bits, vals):
        self.lookup = {}                        # (length, code) -> value
        code = k = 0
        for length in range(1, 17):
            for _ in range(bits[length - 1]):
                self.lookup[(length, code)] = vals[k]
                code += 1
                k += 1
            code <<= 1


class _Bits(object):
    """Bit reader over one scan's entropy-coded data (byte stuffing and RST markers handled)."""

    def __init__(self, data, start, end):
        self.data, self.pos, self.end = data, start, end
        self.acc = self.n = 0

    def _byte(self):
        if self.pos >= self.end:
            return 0
        b = self.data[self.pos]
        if b == 0xFF:
            nxt = self.data[self.pos + 1] if self.pos + 1 < self.end else 0
            if nxt == 0:
                self.pos += 2
                return 0xFF
            return 0                            # a marker: feed zeros until the restart
        self.pos += 1
        return b

    def bit(self):
        if not self.n:
            self.acc, self.n = self._byte(), 8
        self.n -= 1
        return (self.acc >> self.n) & 1

    def bits(self, count):
        v = 0
        for _ in range(count):
            v = (v << 1) | self.bit()
        return v

    def huff(self, table):
        code = 0
        lookup = table.lookup
        for length in range(1, 17):
            code = (code << 1) | self.bit()
            v = lookup.get((length, code))
            if v is not None:
                return v
        raise JPEGError('bad Huffman code')

    def receive_extend(self, s):
        if not s:
            return 0
        v = self.bits(s)
        return v if v >= 1 << (s - 1) else v - (1 << s) + 1

    def restart(self):
        self.n = 0
        while self.pos + 1 < self.end:
            if self.data[self.pos] == 0xFF and 0xD0 <= self.data[self.pos + 1] <= 0xD7:
                self.pos += 2
                return
            self.pos += 1


def _scan_end(data, pos):
    while True:
        pos = data.find(b'\xff', pos)
        if pos < 0 or pos + 1 >= len(data):
            return len(data)
        nxt = data[pos + 1]
        if nxt == 0 or 0xD0 <= nxt <= 0xD7 or nxt == 0xFF:
            pos += 1
            continue
        return pos


def _idct(coef, q):
    """Dequantise + inverse DCT one block (natural order) -> 64 samples 0..255."""
    f = [coef[i] * q[i] for i in range(64)]
    if not any(f[1:]):
        v = int(round(f[0] / 8.0 + 128))
        return [0 if v < 0 else 255 if v > 255 else v] * 64
    tmp = [[0.0] * 8 for _ in range(8)]        # tmp[v][x]: rows transformed
    for v in range(8):
        row = f[v * 8:v * 8 + 8]
        nz = [(u, row[u]) for u in range(8) if row[u]]
        if not nz:
            continue
        t = tmp[v]
        for x in range(8):
            c = COS[x]
            t[x] = sum(c[u] * val for u, val in nz)
    out = [0] * 64
    rows = [(v, tmp[v]) for v in range(8) if any(tmp[v])]
    for y in range(8):
        c = COS[y]
        for x in range(8):
            s = 128.5
            for v, t in rows:
                s += c[v] * t[x]
            s = int(s) if s >= 0 else -1
            out[y * 8 + x] = 0 if s < 0 else 255 if s > 255 else s
    return out


def read(data):
    """bytes -> (width, height, bytearray RGBA)."""
    if data[:2] != SIG:
        raise JPEGError('not a JPEG')
    qt = {}
    dc_tables, ac_tables = {}, {}
    frame = None
    comps = []
    restart_interval = 0
    adobe_transform = None
    progressive = False
    eobrun = [0]
    pos = 2
    while pos < len(data):
        if data[pos] != 0xFF:
            pos += 1
            continue
        marker = data[pos + 1]
        if marker == 0xFF:
            pos += 1
            continue
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            pos += 2
            continue
        if marker == 0xD9:
            break
        length, = struct.unpack('>H', data[pos + 2:pos + 4])
        body = data[pos + 4:pos + 2 + length]
        pos += 2 + length
        if marker == 0xDB:
            i = 0
            while i < len(body):
                prec, tid = body[i] >> 4, body[i] & 15
                if prec:
                    vals = struct.unpack('>64H', body[i + 1:i + 129]); i += 129
                else:
                    vals = body[i + 1:i + 65]; i += 65
                q = [0] * 64
                for k in range(64):
                    q[ZIGZAG[k]] = vals[k]
                qt[tid] = q
        elif marker == 0xC4:
            i = 0
            while i < len(body):
                tc, th = body[i] >> 4, body[i] & 15
                bits = list(body[i + 1:i + 17])
                n = sum(bits)
                table = _Huffman(bits, list(body[i + 17:i + 17 + n]))
                (ac_tables if tc else dc_tables)[th] = table
                i += 17 + n
        elif marker == 0xDD:
            restart_interval, = struct.unpack('>H', body[:2])
        elif marker == 0xEE and body[:5] == b'Adobe' and len(body) >= 12:
            adobe_transform = body[11]
        elif marker in (0xC0, 0xC1, 0xC2):
            progressive = marker == 0xC2
            prec, h, w, nc = struct.unpack('>BHHB', body[:6])
            if prec != 8:
                raise JPEGError('%d-bit JPEG' % prec)
            if not w or not h:
                raise JPEGError('no image size')
            for c in range(nc):
                cid, hv, tq = body[6 + c * 3:9 + c * 3]
                comps.append({'id': cid, 'h': hv >> 4, 'v': hv & 15, 'tq': tq})
            hmax = max(c['h'] for c in comps)
            vmax = max(c['v'] for c in comps)
            mcusx = (w + 8 * hmax - 1) // (8 * hmax)
            mcusy = (h + 8 * vmax - 1) // (8 * vmax)
            for c in comps:
                c['bpl'] = mcusx * c['h']                       # blocks per line (padded)
                c['bpc'] = mcusy * c['v']
                cw = (w * c['h'] + hmax - 1) // hmax            # component's real size
                chh = (h * c['v'] + vmax - 1) // vmax
                c['bw'] = (cw + 7) // 8
                c['bh'] = (chh + 7) // 8
                c['blocks'] = [[0] * 64 for _ in range(c['bpl'] * c['bpc'])]
                c['pred'] = 0
            frame = (w, h, hmax, vmax, mcusx, mcusy)
        elif marker in (0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            raise JPEGError('unsupported JPEG type (SOF%d)' % (marker - 0xC0))
        elif marker == 0xDA:
            if frame is None:
                raise JPEGError('scan before frame')
            ns = body[0]
            scomps = []
            for i in range(ns):
                cid, t = body[1 + i * 2:3 + i * 2]
                c = next(c for c in comps if c['id'] == cid)
                c['dc'], c['ac'] = dc_tables.get(t >> 4), ac_tables.get(t & 15)
                scomps.append(c)
            ss, se, a = body[1 + ns * 2:4 + ns * 2]
            ah, al = a >> 4, a & 15
            end = _scan_end(data, pos)
            _decode_scan(_Bits(data, pos, end), frame, scomps, progressive, ss, se, ah, al,
                         restart_interval, eobrun)
            pos = end
    if frame is None:
        raise JPEGError('no frame')
    return _to_rgba(frame, comps, qt, adobe_transform)


def _decode_scan(r, frame, scomps, progressive, ss, se, ah, al, ri, eobrun):
    w, h, hmax, vmax, mcusx, mcusy = frame
    for c in scomps:
        c['pred'] = 0
    eobrun[0] = 0

    if not progressive:
        def decode(c, blk):
            t = r.huff(c['dc'])
            c['pred'] += r.receive_extend(t)
            blk[0] = c['pred']
            k = 1
            ac = c['ac']
            while k < 64:
                rs = r.huff(ac)
                s, run = rs & 15, rs >> 4
                if not s:
                    if run != 15:
                        break
                    k += 16
                    continue
                k += run
                if k > 63:
                    break
                blk[ZIGZAG[k]] = r.receive_extend(s)
                k += 1
    elif ss == 0:
        if ah == 0:
            def decode(c, blk):
                c['pred'] += r.receive_extend(r.huff(c['dc']))
                blk[0] = c['pred'] << al
        else:
            def decode(c, blk):
                if r.bit():
                    blk[0] |= 1 << al
    elif ah == 0:
        def decode(c, blk):
            if eobrun[0]:
                eobrun[0] -= 1
                return
            k = ss
            ac = c['ac']
            while k <= se:
                rs = r.huff(ac)
                s, run = rs & 15, rs >> 4
                if not s:
                    if run < 15:
                        eobrun[0] = (1 << run) - 1
                        if run:
                            eobrun[0] += r.bits(run)
                        break
                    k += 16
                    continue
                k += run
                if k > 63:
                    break
                blk[ZIGZAG[k]] = r.receive_extend(s) * (1 << al)
                k += 1
    else:
        p1, m1 = 1 << al, -1 << al

        def decode(c, blk):
            k = ss
            if not eobrun[0]:
                ac = c['ac']
                while k <= se:
                    rs = r.huff(ac)
                    s, run = rs & 15, rs >> 4
                    if s:
                        s = p1 if r.bit() else m1
                    elif run != 15:
                        eobrun[0] = 1 << run
                        if run:
                            eobrun[0] += r.bits(run)
                        break
                    while k <= se:
                        z = ZIGZAG[k]
                        if blk[z]:
                            if r.bit() and not blk[z] & p1:
                                blk[z] += p1 if blk[z] >= 0 else m1
                        else:
                            run -= 1
                            if run < 0:
                                break
                        k += 1
                    if s and k <= se:
                        blk[ZIGZAG[k]] = s
                    k += 1
            if eobrun[0]:
                while k <= se:
                    z = ZIGZAG[k]
                    if blk[z] and r.bit() and not blk[z] & p1:
                        blk[z] += p1 if blk[z] >= 0 else m1
                    k += 1
                eobrun[0] -= 1

    for c in scomps:
        if c['dc'] is None and (not progressive or ss == 0) and not (progressive and ah):
            raise JPEGError('missing DC table')
        if c['ac'] is None and (not progressive or ss > 0):
            raise JPEGError('missing AC table')

    def restart():
        r.restart()
        for c in scomps:
            c['pred'] = 0
        eobrun[0] = 0

    n = 0
    if len(scomps) == 1:                        # non-interleaved: the component's own block grid
        c = scomps[0]
        blocks, bpl = c['blocks'], c['bpl']
        for by in range(c['bh']):
            for bx in range(c['bw']):
                if ri and n and n % ri == 0:
                    restart()
                decode(c, blocks[by * bpl + bx])
                n += 1
    else:
        for my in range(mcusy):
            for mx in range(mcusx):
                if ri and n and n % ri == 0:
                    restart()
                for c in scomps:
                    blocks, bpl = c['blocks'], c['bpl']
                    for v in range(c['v']):
                        for u in range(c['h']):
                            decode(c, blocks[(my * c['v'] + v) * bpl + mx * c['h'] + u])
                n += 1


def _to_rgba(frame, comps, qt, adobe_transform):
    w, h, hmax, vmax = frame[:4]
    if len(comps) not in (1, 3):
        raise JPEGError('%d-component JPEG' % len(comps))
    planes = []
    for c in comps:
        q = qt.get(c['tq'])
        if q is None:
            raise JPEGError('missing quantisation table')
        pw = c['bpl'] * 8
        plane = bytearray(pw * c['bpc'] * 8)
        bpl = c['bpl']
        for by in range(min(c['bh'], c['bpc'])):
            for bx in range(min(c['bw'], bpl)):
                samples = _idct(c['blocks'][by * bpl + bx], q)
                base = by * 8 * pw + bx * 8
                for y in range(8):
                    plane[base + y * pw:base + y * pw + 8] = bytes(samples[y * 8:y * 8 + 8])
        planes.append((plane, pw, hmax // c['h'], vmax // c['v']))
    out = bytearray(w * h * 4)
    ycc = len(comps) == 3 and adobe_transform != 0
    if len(comps) == 1:
        plane, pw, sx, sy = planes[0]
        o = 0
        for y in range(h):
            row = (y // sy) * pw
            for x in range(w):
                v = plane[row + x // sx]
                out[o:o + 4] = bytes((v, v, v, 255))
                o += 4
        return w, h, out
    p0, p1, p2 = [_upsample(plane, pw, sx, sy, w, h) for plane, pw, sx, sy in planes]
    o = 0
    for i in range(w * h):
        a, b, c = p0[i], p1[i], p2[i]
        if ycc:
            cb, cr = b - 128, c - 128
            rr = int(a + 1.402 * cr + 0.5)
            gg = int(a - 0.344136 * cb - 0.714136 * cr + 0.5)
            bb = int(a + 1.772 * cb + 0.5)
            a = 0 if rr < 0 else 255 if rr > 255 else rr
            b = 0 if gg < 0 else 255 if gg > 255 else gg
            c = 0 if bb < 0 else 255 if bb > 255 else bb
        out[o] = a; out[o + 1] = b; out[o + 2] = c; out[o + 3] = 255
        o += 4
    return w, h, out


def _taps(n, scale, size):
    """For each output position: (i0, i1, weight of i1), sampling sites centred like libjpeg's fancy upsampling."""
    taps = []
    for x in range(n):
        f = (x + 0.5) / scale - 0.5
        i0 = int(math.floor(f))
        t = f - i0
        taps.append((min(max(i0, 0), size - 1), min(max(i0 + 1, 0), size - 1), t))
    return taps


def _upsample(plane, pw, sx, sy, w, h):
    """Component plane -> w*h samples, smoothly interpolated when the component is subsampled."""
    if sx == 1 and sy == 1:
        out = bytearray(w * h)
        for y in range(h):
            out[y * w:(y + 1) * w] = plane[y * pw:y * pw + w]
        return out
    cw, ch = (w + sx - 1) // sx, (h + sy - 1) // sy
    xt, yt = _taps(w, sx, cw), _taps(h, sy, ch)
    rows = []
    for y in range(ch):                         # horizontal pass
        base = y * pw
        rows.append([plane[base + a] * (1 - t) + plane[base + b] * t for a, b, t in xt])
    out = bytearray(w * h)
    o = 0
    for a, b, t in yt:                          # vertical pass
        ra, rb = rows[a], rows[b]
        for x in range(w):
            v = int(ra[x] * (1 - t) + rb[x] * t + 0.5)
            out[o] = 255 if v > 255 else v
            o += 1
    return out


# ---------------------------------------------------------------------------------------------- encoding
_Q_LUMA = [16, 11, 12, 14, 12, 10, 16, 14, 13, 14, 18, 17, 16, 19, 24, 40, 26, 24, 22, 22, 24, 49, 35, 37, 29, 40,
           58, 51, 61, 60, 57, 51, 56, 55, 64, 72, 92, 78, 64, 68, 87, 69, 55, 56, 80, 109, 81, 87, 95, 98, 103,
           104, 103, 62, 77, 113, 121, 112, 100, 120, 92, 101, 103, 99]          # zigzag order
_Q_CHROMA = [17, 18, 18, 24, 21, 24, 47, 26, 26, 47, 99, 66, 56, 66] + [99] * 50
_DC_LUMA = ([0, 1, 5, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0], list(range(12)))
_DC_CHROMA = ([0, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0], list(range(12)))
_AC_LUMA = ([0, 2, 1, 3, 3, 2, 4, 3, 5, 5, 4, 4, 0, 0, 1, 125], [
    1, 2, 3, 0, 4, 17, 5, 18, 33, 49, 65, 6, 19, 81, 97, 7, 34, 113, 20, 50, 129, 145, 161, 8, 35, 66, 177, 193, 21,
    82, 209, 240, 36, 51, 98, 114, 130, 9, 10, 22, 23, 24, 25, 26, 37, 38, 39, 40, 41, 42, 52, 53, 54, 55, 56, 57,
    58, 67, 68, 69, 70, 71, 72, 73, 74, 83, 84, 85, 86, 87, 88, 89, 90, 99, 100, 101, 102, 103, 104, 105, 106, 115,
    116, 117, 118, 119, 120, 121, 122, 131, 132, 133, 134, 135, 136, 137, 138, 146, 147, 148, 149, 150, 151, 152,
    153, 154, 162, 163, 164, 165, 166, 167, 168, 169, 170, 178, 179, 180, 181, 182, 183, 184, 185, 186, 194, 195,
    196, 197, 198, 199, 200, 201, 202, 210, 211, 212, 213, 214, 215, 216, 217, 218, 225, 226, 227, 228, 229, 230,
    231, 232, 233, 234, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250])
_AC_CHROMA = ([0, 2, 1, 2, 4, 4, 3, 4, 7, 5, 4, 4, 0, 1, 2, 119], [
    0, 1, 2, 3, 17, 4, 5, 33, 49, 6, 18, 65, 81, 7, 97, 113, 19, 34, 50, 129, 8, 20, 66, 145, 161, 177, 193, 9, 35,
    51, 82, 240, 21, 98, 114, 209, 10, 22, 36, 52, 225, 37, 241, 23, 24, 25, 26, 38, 39, 40, 41, 42, 53, 54, 55, 56,
    57, 58, 67, 68, 69, 70, 71, 72, 73, 74, 83, 84, 85, 86, 87, 88, 89, 90, 99, 100, 101, 102, 103, 104, 105, 106,
    115, 116, 117, 118, 119, 120, 121, 122, 130, 131, 132, 133, 134, 135, 136, 137, 138, 146, 147, 148, 149, 150,
    151, 152, 153, 154, 162, 163, 164, 165, 166, 167, 168, 169, 170, 178, 179, 180, 181, 182, 183, 184, 185, 186,
    194, 195, 196, 197, 198, 199, 200, 201, 202, 210, 211, 212, 213, 214, 215, 216, 217, 218, 226, 227, 228, 229,
    230, 231, 232, 233, 234, 242, 243, 244, 245, 246, 247, 248, 249, 250])


def _codes(spec):
    bits, vals = spec
    table, code, k = {}, 0, 0
    for length in range(1, 17):
        for _ in range(bits[length - 1]):
            table[vals[k]] = (code, length)
            code += 1
            k += 1
        code <<= 1
    return table


def _scaled(base, quality):
    scale = 5000 // quality if quality < 50 else 200 - quality * 2
    return [min(255, max(1, (b * scale + 50) // 100)) for b in base]


class _Writer(object):
    def __init__(self):
        self.out = bytearray()
        self.acc = self.n = 0

    def put(self, code, length):
        self.acc = (self.acc << length) | code
        self.n += length
        while self.n >= 8:
            self.n -= 8
            b = (self.acc >> self.n) & 255
            self.out.append(b)
            if b == 255:
                self.out.append(0)
        self.acc &= (1 << self.n) - 1

    def flush(self):
        if self.n:
            self.put((1 << (8 - self.n)) - 1, 8 - self.n)


def _magnitude(v):
    a = -v if v < 0 else v
    s = a.bit_length()
    return s, (v if v >= 0 else v + (1 << s) - 1)


def write_rgb(w, h, rgb, quality=92):
    """Encode a flat RGB bytearray as a baseline 4:4:4 JPEG."""
    qz = [_scaled(_Q_LUMA, quality), _scaled(_Q_CHROMA, quality)]
    qn = []                                      # natural-order divisors
    for t in qz:
        n = [0] * 64
        for k in range(64):
            n[ZIGZAG[k]] = t[k]
        qn.append(n)
    dc = [_codes(_DC_LUMA), _codes(_DC_CHROMA)]
    ac = [_codes(_AC_LUMA), _codes(_AC_CHROMA)]

    def seg(marker, body):
        return b'\xff' + bytes((marker,)) + struct.pack('>H', len(body) + 2) + body

    def dht(tc, th, spec):
        return bytes((tc << 4 | th,)) + bytes(spec[0]) + bytes(spec[1])

    head = bytearray(SIG)
    head += seg(0xE0, b'JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00')
    head += seg(0xDB, b'\x00' + bytes(qz[0]) + b'\x01' + bytes(qz[1]))
    head += seg(0xC0, struct.pack('>BHHB', 8, h, w, 3) + b'\x01\x11\x00\x02\x11\x01\x03\x11\x01')
    head += seg(0xC4, dht(0, 0, _DC_LUMA) + dht(1, 0, _AC_LUMA) + dht(0, 1, _DC_CHROMA) + dht(1, 1, _AC_CHROMA))
    head += seg(0xDA, b'\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00')

    # colour conversion to Y, Cb, Cr planes (level-shifted)
    n = w * h
    planes = ([0.0] * n, [0.0] * n, [0.0] * n)
    py, pb, pr = planes
    for i in range(n):
        r, g, b = rgb[i * 3], rgb[i * 3 + 1], rgb[i * 3 + 2]
        py[i] = 0.299 * r + 0.587 * g + 0.114 * b - 128
        pb[i] = -0.168736 * r - 0.331264 * g + 0.5 * b
        pr[i] = 0.5 * r - 0.418688 * g - 0.081312 * b

    wr = _Writer()
    pred = [0, 0, 0]
    for by in range(0, h, 8):
        for bx in range(0, w, 8):
            for ci in range(3):
                plane = planes[ci]
                t = 0 if ci == 0 else 1
                blk = []
                for y in range(8):
                    row = min(by + y, h - 1) * w
                    for x in range(8):
                        blk.append(plane[row + min(bx + x, w - 1)])
                coef = _fdct(blk)
                q = qn[t]
                zz = [int(round(coef[ZIGZAG[k]] / q[ZIGZAG[k]])) for k in range(64)]
                diff = zz[0] - pred[ci]
                pred[ci] = zz[0]
                s, bits = _magnitude(diff)
                code, length = dc[t][s]
                wr.put(code, length)
                if s:
                    wr.put(bits, s)
                run = 0
                act = ac[t]
                for k in range(1, 64):
                    v = zz[k]
                    if not v:
                        run += 1
                        continue
                    while run > 15:
                        code, length = act[0xF0]
                        wr.put(code, length)
                        run -= 16
                    s, bits = _magnitude(v)
                    code, length = act[(run << 4) | s]
                    wr.put(code, length)
                    wr.put(bits, s)
                    run = 0
                if run:
                    code, length = act[0]
                    wr.put(code, length)
    wr.flush()
    return bytes(head + wr.out + b'\xff\xd9')


def _fdct(blk):
    first = blk[0]
    if all(v == first for v in blk):            # flat block (the poster card): DC only
        return [8.0 * first] + [0.0] * 63
    tmp = [0.0] * 64                             # tmp[y*8+u]: rows transformed
    for y in range(8):
        row = blk[y * 8:y * 8 + 8]
        for u in range(8):
            tmp[y * 8 + u] = sum(row[x] * COS[x][u] for x in range(8))
    out = [0.0] * 64
    for v in range(8):
        for u in range(8):
            out[v * 8 + u] = sum(tmp[y * 8 + u] * COS[y][v] for y in range(8))
    return out
