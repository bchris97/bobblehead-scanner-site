"""Regenerate assets/logo-head.png and assets/logo-body.png from the app icon.

The hero shows the app's own logo with the head bobbing on its spring. That
needs the artwork as two layers, and the icon ships only as a flat PNG, so this
splits it: the head/cap components end at y=440 in the source, exactly where the
spring coils begin, which is why the cut is invisible.

Run from anywhere:  python3 assets/split-logo.py
Requires nothing but the standard library.
"""

import struct, zlib


def read_png(path):
    data = open(path, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a png"
    pos, idat, hdr = 8, [], None
    while pos < len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            hdr = struct.unpack(">IIBBBBB", body)
        elif typ == b"IDAT":
            idat.append(body)
        elif typ == b"IEND":
            break
        pos += 12 + ln
    w, h, depth, ctype, comp, filt, inter = hdr
    assert depth == 8 and inter == 0, (depth, inter)
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    raw = zlib.decompress(b"".join(idat))
    bpp, stride = channels, w * channels
    out = bytearray(h * stride)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        f = raw[p]; p += 1
        line = bytearray(raw[p:p + stride]); p += stride
        if f == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 255
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif f == 3:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                c = prev[i - bpp] if i >= bpp else 0
                b = prev[i]
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return w, h, channels, out


def write_gray_alpha(path, w, h, ga):
    """Colour type 4 (grey+alpha): the art is pure white, so only coverage
    varies and half the bytes of RGBA are needed.

    Filter type 0 (None) on every row, deliberately. This image is mostly empty,
    and its compression comes from long runs of identical bytes; the spec's
    adaptive heuristic picks Sub/Paeth to minimise delta magnitude, which breaks
    those runs. Benchmarked on the body layer: None 70,291 bytes vs adaptive
    83,565 vs the old RGBA+None 79,539. Do not "improve" this to adaptive.
    """
    stride = w * 2
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += ga[y * stride:(y + 1) * stride]

    def chunk(t, d):
        c = t + d
        return struct.pack(">I", len(d)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 4, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
           + chunk(b"IEND", b""))
    open(path, "wb").write(png)


import os
from collections import deque

# Resolved relative to this file so the script carries no absolute local paths
# (this repo is public). Override the source with BOBBLEHEAD_ICON if the app
# repo lives somewhere other than a sibling directory.
OUT = os.path.dirname(os.path.abspath(__file__))
SRC = os.environ.get(
    "BOBBLEHEAD_ICON",
    os.path.normpath(os.path.join(
        OUT, "..", "..", "bobblehead-scanner", "bobblehead-app", "assets", "icon.png")),
)
if not os.path.exists(SRC):
    raise SystemExit(
        "Source icon not found at %s\n"
        "Set BOBBLEHEAD_ICON to the app's assets/icon.png." % SRC)

BG_R, SPAN = 87, 168.0          # flat background red channel -> white
HEAD_MAX_Y = 439                # spring coils begin at 440
HEAD_X0, HEAD_X1 = 372, 700     # excludes the baseball (<=358) and brackets
X0, Y0, W, H = 275, 136, 475, 696   # figure bbox, brackets excluded

w, h, ch, px = read_png(SRC)

# Continuous alpha keeps the anti-aliased edges instead of a hard threshold.
alpha = [0.0] * (w * h)
for i in range(w * h):
    a = (px[i * ch] - BG_R) / SPAN
    alpha[i] = 0.0 if a < 0 else (1.0 if a > 1 else a)

# Label components on a binary mask so the four corner brackets can be dropped.
mask = [1 if a > 0.35 else 0 for a in alpha]
seen = bytearray(w * h)
bracket = bytearray(w * h)
for sy in range(h):
    for sx in range(w):
        s = sy * w + sx
        if not mask[s] or seen[s]:
            continue
        q, cells = deque([s]), []
        seen[s] = 1
        x0 = y0 = 10 ** 9
        x1 = y1 = -1
        while q:
            j = q.popleft()
            cells.append(j)
            jy, jx = divmod(j, w)
            x0, x1 = min(x0, jx), max(x1, jx)
            y0, y1 = min(y0, jy), max(y1, jy)
            for k in (j - 1, j + 1, j - w, j + w):
                if 0 <= k < w * h and mask[k] and not seen[k] and abs(divmod(k, w)[1] - jx) <= 1:
                    seen[k] = 1
                    q.append(k)
        # Corner brackets: compact L-shapes parked in the outer corners.
        if len(cells) > 150 and (x1 < 340 or x0 > 688) and (y1 < 266 or y0 > 716):
            for j in cells:
                bracket[j] = 1

# Grey/alpha pairs. Grey is 255 only where the art actually is; fully
# transparent pixels are left as 0,0 so empty regions stay long runs of zeros,
# which is what compresses. (Filling grey=255 everywhere costs ~4KB.)
head = bytearray(W * H * 2)
body = bytearray(W * H * 2)
for y in range(H):
    sy = Y0 + y
    for x in range(W):
        sx = X0 + x
        s = sy * w + sx
        if bracket[s]:
            continue
        a = int(round(alpha[s] * 255))
        if a == 0:
            continue
        is_head = sy <= HEAD_MAX_Y and HEAD_X0 <= sx <= HEAD_X1
        buf = head if is_head else body
        d = (y * W + x) * 2
        buf[d] = 255
        buf[d + 1] = a

write_gray_alpha(OUT + "/logo-head.png", W, H, head)
write_gray_alpha(OUT + "/logo-body.png", W, H, body)

pivot = (509 - X0, 478 - Y0)   # base of the spring, in canvas coords
print("canvas %dx%d  pivot=%s" % (W, H, pivot))
print("head px:", sum(1 for i in range(W * H) if head[i * 2 + 1]))
print("body px:", sum(1 for i in range(W * H) if body[i * 2 + 1]))
