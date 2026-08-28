#!/usr/bin/env python3
"""Derives the web logo from the client's master artwork.

    python3 tools/make-logo.py

Reads images/PowderTec-Logo.png (1697x700 master, transparent background),
trims the empty margin and box-downsamples it to images/powdertec-logo.png,
which is what the header and footer actually load. Pure stdlib on purpose —
the rest of the repo has no dependencies either.

Re-run this if the client sends new artwork; then rebuild the pages so the
width/height attributes match:

    python3 tools/make-logo.py && python3 tools/build.py
"""

import os
import struct
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER = os.path.join(ROOT, "images", "PowderTec-Logo.png")
OUT = os.path.join(ROOT, "images", "powdertec-logo.png")

OUT_WIDTH = 560   # covers the 76px footer mark at 3x on the widest breakpoint
PAD = 4           # transparent breathing room kept around the trimmed art


def read_rgba(path):
    """Decodes a non-interlaced 8-bit PNG to (width, height, RGBA bytearray)."""
    data = open(path, "rb").read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit("%s is not a PNG" % path)

    pos, idat, ihdr, plte, trns = 8, [], None, None, None
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        if kind == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", chunk)
        elif kind == b"IDAT":
            idat.append(chunk)
        elif kind == b"PLTE":
            plte = chunk
        elif kind == b"tRNS":
            trns = chunk
        pos += 12 + length

    w, h, depth, color, _, _, interlace = ihdr
    if depth != 8 or interlace:
        raise SystemExit("only 8-bit non-interlaced PNGs are supported")
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color]

    raw = zlib.decompress(b"".join(idat))
    stride = w * channels
    flat = bytearray(h * stride)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        ftype = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        if ftype == 1:
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 255
        elif ftype == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif ftype == 3:
            for i in range(stride):
                left = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 255
        elif ftype == 4:
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                b = prev[i]
                c = prev[i - channels] if i >= channels else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pred) & 255
        flat[y * stride:(y + 1) * stride] = line
        prev = line

    rgba = bytearray(w * h * 4)
    for i in range(w * h):
        if color == 6:
            rgba[i * 4:i * 4 + 4] = flat[i * 4:i * 4 + 4]
        elif color == 2:
            rgba[i * 4:i * 4 + 3] = flat[i * 3:i * 3 + 3]
            rgba[i * 4 + 3] = 255
        elif color == 0:
            v = flat[i]
            rgba[i * 4:i * 4 + 4] = bytes((v, v, v, 255))
        elif color == 4:
            v, a = flat[i * 2], flat[i * 2 + 1]
            rgba[i * 4:i * 4 + 4] = bytes((v, v, v, a))
        else:
            idx = flat[i]
            rgba[i * 4:i * 4 + 3] = plte[idx * 3:idx * 3 + 3]
            rgba[i * 4 + 3] = trns[idx] if trns and idx < len(trns) else 255
    return w, h, rgba


def _filter(w, h, rgba):
    """Per-scanline filter selection (the usual minimum-sum-of-absolutes rule).

    Worth the extra pass: the artwork is half photograph, and picking a filter
    per row rather than storing raw scanlines takes ~15% off the file.
    """
    out = bytearray()
    prev = bytearray(w * 4)
    for y in range(h):
        line = rgba[y * w * 4:(y + 1) * w * 4]
        best = None
        for ftype in range(5):
            enc = bytearray(w * 4)
            for i in range(w * 4):
                a = line[i - 4] if i >= 4 else 0
                b = prev[i]
                c = prev[i - 4] if i >= 4 else 0
                if ftype == 0:
                    v = line[i]
                elif ftype == 1:
                    v = line[i] - a
                elif ftype == 2:
                    v = line[i] - b
                elif ftype == 3:
                    v = line[i] - ((a + b) >> 1)
                else:
                    pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                    v = line[i] - (a if (pa <= pb and pa <= pc) else (b if pb <= pc else c))
                enc[i] = v & 255
            score = sum(min(v, 256 - v) for v in enc)
            if best is None or score < best[0]:
                best = (score, ftype, enc)
        out.append(best[1])
        out += best[2]
        prev = line
    return out


def write_rgba(path, w, h, rgba):
    scanlines = _filter(w, h, rgba)

    def chunk(kind, payload):
        return (struct.pack(">I", len(payload)) + kind + payload
                + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff))

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(scanlines), 9))
    png += chunk(b"IEND", b"")
    open(path, "wb").write(png)


def content_box(w, h, rgba, pad):
    """Tightest box holding every pixel that is not effectively transparent."""
    x0, y0, x1, y1 = w, h, -1, -1
    for y in range(h):
        row = y * w * 4
        for x in range(w):
            if rgba[row + x * 4 + 3] > 8:
                if x < x0: x0 = x
                if x > x1: x1 = x
                if y < y0: y0 = y
                if y > y1: y1 = y
    return (max(0, x0 - pad), max(0, y0 - pad),
            min(w, x1 + 1 + pad), min(h, y1 + 1 + pad))


def resample(w, h, rgba, box, out_w):
    """Box filter over premultiplied alpha, so edges do not pick up black fringe."""
    x0, y0, x1, y1 = box
    src_w, src_h = x1 - x0, y1 - y0
    out_h = max(1, round(out_w * src_h / src_w))
    out = bytearray(out_w * out_h * 4)

    spans_x = [(x0 + x * src_w // out_w, x0 + max(x * src_w // out_w + 1, (x + 1) * src_w // out_w))
               for x in range(out_w)]
    spans_y = [(y0 + y * src_h // out_h, y0 + max(y * src_h // out_h + 1, (y + 1) * src_h // out_h))
               for y in range(out_h)]

    for oy, (sy0, sy1) in enumerate(spans_y):
        for ox, (sx0, sx1) in enumerate(spans_x):
            r = g = b = a = n = 0
            for y in range(sy0, sy1):
                base = y * w * 4
                for x in range(sx0, sx1):
                    i = base + x * 4
                    alpha = rgba[i + 3]
                    r += rgba[i] * alpha
                    g += rgba[i + 1] * alpha
                    b += rgba[i + 2] * alpha
                    a += alpha
                    n += 1
            o = (oy * out_w + ox) * 4
            if a:
                out[o] = min(255, r // a)
                out[o + 1] = min(255, g // a)
                out[o + 2] = min(255, b // a)
            out[o + 3] = a // n
    return out_w, out_h, out


def main():
    w, h, rgba = read_rgba(MASTER)
    box = content_box(w, h, rgba, PAD)
    out_w, out_h, small = resample(w, h, rgba, box, OUT_WIDTH)
    write_rgba(OUT, out_w, out_h, small)
    print("%s  %dx%d  %.1f KB  (master %dx%d, trimmed to %s)"
          % (os.path.relpath(OUT, ROOT), out_w, out_h,
             os.path.getsize(OUT) / 1024.0, w, h, box))


if __name__ == "__main__":
    main()
