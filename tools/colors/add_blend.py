"""Add a chip blend to the visualizer from The Coating Crew's own swatch photo.

Their newer swatch photos are closer shots than the older ones, so the chips look bigger. This script measures
the chip size against a reference swatch in the same capture, shrinks the photo so the chips match the other
blends, and then lays that sample out into the three images the site uses:
  img/colors/<slug>.jpg     260 px swatch
  img/colors/s/<slug>.webp  160 px thumbnail for the sample board
  img/colors/l/<slug>.webp  160 px close-up for the loupe
  img/colors/tex/<slug>.jpg 1024 px floor texture that repeats without visible seams
Colors are not changed. The larger images are built by placing pieces of the sample side by side.

Usage: python3 tools/colors/add_blend.py <capture.png> <name> [chip size ratio]
The capture holds the new swatch in its left square and a reference swatch (Domino) in its right square.
The measured ratio is a starting point; Nightfall was set by eye to 1.9, comparing chips against Domino and Gunflint.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def chip_size(im):
    """How big the chips are, in pixels: the image is cut to its light, middle and dark chips, and the
    typical run of one tone along rows and columns is measured."""
    g = np.asarray(im.convert('L').filter(ImageFilter.GaussianBlur(1.2))).astype(float)
    q = np.digitize(g, np.percentile(g, [33, 66]))
    runs = []
    for arr in (q, q.T):
        change = np.diff(arr, axis=1) != 0
        runs.append(arr.shape[1] / (change.sum(axis=1) + 1))
    return float(np.median(np.concatenate(runs)))


def quilt(sample, size, cell, seed):
    """Fill a size x size image with irregular pieces of the sample, each turned or flipped at random.
    Every piece is taken whole from inside the sample, and the layout wraps around the edges, so the
    result repeats without a seam."""
    rng = np.random.default_rng(seed)
    src = np.asarray(sample); side = src.shape[0]
    variants = [np.rot90(src, k) for k in range(4)] + [np.rot90(src[:, ::-1], k) for k in range(4)]
    n = max(6, round((size / cell) ** 2))
    # seeds on a jittered grid, so no piece grows larger than the sample
    k = int(np.ceil(np.sqrt(n))); step = size / k
    pts = np.array([[(i + .5 + rng.uniform(-.3, .3)) * step, (j + .5 + rng.uniform(-.3, .3)) * step] for i in range(k) for j in range(k)])
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)

    def noise(scale):
        z = rng.normal(size=(size // scale + 2, size // scale + 2)).astype(np.float32)
        return np.asarray(Image.fromarray(z).resize((size, size), Image.BICUBIC))
    wx, wy = xx + noise(20) * step * .10, yy + noise(20) * step * .10   # wobble the borders between pieces
    best = np.full((size, size), 1e12, np.float32); label = np.zeros((size, size), np.int32)
    for i, (px, py) in enumerate(pts):
        dx = np.abs(wx - px); dx = np.minimum(dx, size - dx)
        dy = np.abs(wy - py); dy = np.minimum(dy, size - dy)
        d = dx * dx + dy * dy
        m = d < best; best[m] = d[m]; label[m] = i
    out = np.zeros((size, size, 3), np.uint8)
    for i, (px, py) in enumerate(pts):
        ys, xs = np.nonzero(label == i)
        if not len(ys):
            continue
        rx = ((xs - px + size / 2) % size - size / 2); ry = ((ys - py + size / 2) % size - size / 2)
        rx = np.round(rx - rx.min()).astype(int); ry = np.round(ry - ry.min()).astype(int)
        w, h = rx.max() + 1, ry.max() + 1
        ox = rng.integers(0, max(1, side - w + 1)); oy = rng.integers(0, max(1, side - h + 1))
        v = variants[rng.integers(8)]
        out[ys, xs] = v[np.minimum(ry + oy, side - 1), np.minimum(rx + ox, side - 1)]
    return Image.fromarray(out)


def main(capture, name, scale=None):
    slug = name.lower().replace(' ', '-')
    cap = Image.open(capture).convert('RGB'); h = cap.height
    new, ref = cap.crop((0, 0, h, h)), cap.crop((cap.width - h, 0, cap.width, h))
    ratio = float(scale) if scale else chip_size(new) / chip_size(ref)
    # the reference swatch is 260 px wide on the site; shrink the new photo so its chips are the same size
    side = max(64, round(260 / ratio))
    sample = new.resize((side, side), Image.LANCZOS)
    print(f'chips are {ratio:.2f}x the reference; sample {side}px')
    cell = side * 0.5
    swatch = quilt(sample, 260, cell, 7)
    swatch.save(os.path.join(ROOT, 'img/colors', slug + '.jpg'), 'JPEG', quality=90)
    swatch.resize((160, 160), Image.LANCZOS).save(os.path.join(ROOT, 'img/colors/s', slug + '.webp'), 'WEBP', quality=82, method=6)
    swatch.crop((50, 50, 210, 210)).save(os.path.join(ROOT, 'img/colors/l', slug + '.webp'), 'WEBP', quality=86, method=6)
    quilt(sample, 1024, cell, 11).save(os.path.join(ROOT, 'img/colors/tex', slug + '.jpg'), 'JPEG', quality=86)
    a = np.asarray(sample).reshape(-1, 3).mean(0)
    print('mean color', a.round(1), 'lightness', round(float(a @ [0.2126, 0.7152, 0.0722]), 1))


if __name__ == '__main__':
    main(*sys.argv[1:4])
