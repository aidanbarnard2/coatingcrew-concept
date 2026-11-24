"""Pack rendered light passes for the site.

    python3 encode.py SRC_DIR OUT_DIR room [room ...]

Per room it writes:
  {room}-bg0.jpg   sun_am / sun_noon / sun_pm stacked top to bottom (each pass is (v/scale)^(1/2.2))
  {room}-bg1.jpg   sky / ceiling / lamps
  {room}-gl0.jpg, {room}-gl1.jpg   clear-coat reflections, same layout, floor crop only
  {room}-mask.png  floor coverage
  {room}-poster.jpg, {room}-thumb.jpg   a bright-afternoon Domino mix for first paint and the room button
and rooms.json with scales, crop, the floor matrix and light statistics the page needs.
"""
import json
import sys

import cv2
import numpy as np

import mix

GROUPS = mix.GROUPS
LUM = mix.LUM


def enc(p, scale):
    return np.clip((np.clip(p, 0, None) / scale) ** (1 / 2.2) * 255 + 0.5, 0, 255).astype(np.uint8)


def pass_scale(p):
    m = p.max(axis=2)
    v = float(np.percentile(m, 99.6))
    return max(v, 1e-6)


def main():
    src, out, rooms = sys.argv[1], sys.argv[2], sys.argv[3:]
    data = []
    for room in rooms:
        A = mix.read(f'{src}/{room}_A.exr')
        B = mix.read(f'{src}/{room}_B.exr')
        meta = json.load(open(f'{src}/{room}_meta.json'))
        H, W = A['floor'].shape
        f = A['floor'] > 0.01
        ys, xs = np.where(f)
        x0 = max(0, xs.min() - 4); y1 = min(H, ys.max() + 1 + 4)
        gh, gw = B[GROUPS[0]].shape[:2]
        y0 = y1 - gh
        crop = [x0, y0, x0 + gw, y1]
        bs, gs, means, rgb = [], [], [], []
        bgimgs, glimgs = [], []
        for g in GROUPS:
            a = A[g][..., :3]
            s = pass_scale(a)
            bs.append(s)
            bgimgs.append(enc(a, s))
            means.append(float((a @ LUM).mean()))
            rgb.append([float(v) for v in a.reshape(-1, 3).mean(0)])
            b = B[g][..., :3]
            sg = pass_scale(b)
            gs.append(sg)
            glimgs.append(enc(b, sg))
        q = [int(cv2.IMWRITE_JPEG_QUALITY), 88, int(cv2.IMWRITE_JPEG_PROGRESSIVE), 1]
        cv2.imwrite(f'{out}/{room}-bg0.jpg', np.vstack(bgimgs[:3])[:, :, ::-1], q)
        cv2.imwrite(f'{out}/{room}-bg1.jpg', np.vstack(bgimgs[3:])[:, :, ::-1], q)
        cv2.imwrite(f'{out}/{room}-gl0.jpg', np.vstack(glimgs[:3])[:, :, ::-1], q)
        cv2.imwrite(f'{out}/{room}-gl1.jpg', np.vstack(glimgs[3:])[:, :, ::-1], q)
        cv2.imwrite(f'{out}/{room}-mask.png', (np.clip(A['floor'], 0, 1) * 255 + 0.5).astype(np.uint8), [cv2.IMWRITE_PNG_COMPRESSION, 9])
        poster = mix.mix(room, src, 'bright_afternoon', 'domino')
        cv2.imwrite(f'{out}/{room}-poster.jpg', poster[:, :, ::-1], [int(cv2.IMWRITE_JPEG_QUALITY), 84, int(cv2.IMWRITE_JPEG_PROGRESSIVE), 1])
        th = cv2.resize(poster, (270, 180), interpolation=cv2.INTER_AREA)
        cv2.imwrite(f'{out}/{room}-thumb.jpg', th[:, :, ::-1], [int(cv2.IMWRITE_JPEG_QUALITY), 82])
        Mf = np.array(meta['floor'])
        data.append(dict(key=room, name=meta['name'], ceiling=meta['ceiling'], lamps=meta['lamps'], W=W, H=H,
                         floor=[float(v) for v in Mf], tile=2.6, crop=crop, bgScale=bs, glScale=gs,
                         mean=means, meanRGB=rgb))
        print(room, 'scales', [round(v, 4) for v in bs], 'crop', crop)
    json.dump(data, open(f'{out}/rooms.json', 'w'), indent=1)


if __name__ == '__main__':
    main()
