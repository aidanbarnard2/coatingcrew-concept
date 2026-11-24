"""Mix rendered light passes the same way the site will (used to tune presets and to check renders).

    python3 mix.py ROOM DIR OUT.png PRESET [BLEND]
"""
import json
import math
import sys

import cv2
import numpy as np
import OpenEXR

GROUPS = ['sun_am', 'sun_noon', 'sun_pm', 'sky', 'ceiling', 'lamps']
LUM = np.array([0.2126, 0.7152, 0.0722])


def kelvin(k):
    """Approximate blackbody color, normalized to luminance 1."""
    t = k / 100.0
    r = 255 if t <= 66 else 329.698727446 * (t - 60) ** -0.1332047592
    g = 99.4708025861 * math.log(t) - 161.1195681661 if t <= 66 else 288.1221695283 * (t - 60) ** -0.0755148492
    b = 255 if t >= 66 else (0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307)
    c = np.clip(np.array([r, g, b]) / 255.0, 0, 1) ** 2.2
    return c / (c @ LUM)


def col(rgb):
    c = np.array(rgb, float)
    return c / (c @ LUM)


SUN_AM, SUN_NOON, SUN_PM = col((1.0, 0.86, 0.68)), col((1.0, 0.96, 0.9)), col((1.0, 0.62, 0.32))
SKY_DAY, SKY_GOLD, SKY_DUSK, SKY_NIGHT = col((0.78, 0.87, 1.0)), col((0.85, 0.8, 0.9)), col((0.52, 0.56, 0.95)), col((0.42, 0.47, 0.7))

# time of day: weights for sun_am, sun_noon, sun_pm, sky (intensity, color)
TIMES = {
    'morning': dict(sun=(9, 0, 0), suncol=SUN_AM, sky=(0.8, SKY_DAY)),
    'midday': dict(sun=(0, 12, 0), suncol=SUN_NOON, sky=(1.0, SKY_DAY)),
    'golden': dict(sun=(0, 0, 7), suncol=SUN_PM, sky=(0.5, SKY_GOLD)),
    'dusk': dict(sun=(0, 0, 0), suncol=SUN_PM, sky=(0.035, SKY_DUSK)),
    'night': dict(sun=(0, 0, 0), suncol=SUN_PM, sky=(0.0012, SKY_NIGHT)),
}
PRESETS = {
    'sunny_morning': ('morning', 0, 0, 3000),
    'bright_afternoon': ('midday', 0, 0, 4000),
    'showroom': ('midday', 1.0, 1.0, 5000),
    'golden_hour': ('golden', 0.6, 0.6, 2700),
    'evening_warm': ('dusk', 1.0, 1.0, 2700),
    'night_cool': ('night', 1.0, 0.0, 5000),
    'night_warm': ('night', 1.0, 1.0, 2700),
    'lights_off': ('night', 0.0, 0.0, 3000),
    'cloudy': ('midday', 0, 0, 4000),
}


def weights(preset):
    tod, ceil, lamps, K = PRESETS[preset]
    t = TIMES[tod]
    w = []
    sunk = (0, 0, 0) if preset == 'cloudy' else t['sun']
    for i in range(3):
        w.append(sunk[i] * t['suncol'])
    skyI = t['sky'][0] * (1.8 if preset == 'cloudy' else 1.0)
    w.append(skyI * (col((0.8, 0.85, 0.95)) if preset == 'cloudy' else t['sky'][1]))
    bulb = kelvin(K)
    w.append(ceil * bulb)
    w.append(lamps * bulb)
    return np.array(w)


def read(path):
    f = OpenEXR.File(path, separate_channels=True)
    out = {}
    for p in f.parts:
        ch = p.channels
        names = {k.split('.')[0] for k in ch}
        for n in names:
            if n + '.R' in ch:
                out[n] = np.dstack([ch[n + '.R'].pixels, ch[n + '.G'].pixels, ch[n + '.B'].pixels]).astype(np.float32)
            elif n + '.V' in ch:
                out[n] = ch[n + '.V'].pixels.astype(np.float32)
    return out


def aces(x):
    a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
    return np.clip((x * (a * x + b)) / (x * (c * x + d) + e), 0, 1)


def srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * x ** (1 / 2.4) - 0.055)


def chip_albedo(meta, blend, H, W, tile_ft=2.6):
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    tex = cv2.imread(os.path.join(here, '..', '..', 'img', 'colors', 'tex', f'{blend}.jpg'))[:, :, ::-1].astype(np.float32) / 255
    tex = tex ** 2.2
    M = np.array(meta['floor']).reshape(3, 3)
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32) + 0.5
    P = np.stack([xs, ys, np.ones_like(xs)], -1) @ M.T
    u = P[..., 0] / P[..., 2] / tile_ft
    v = P[..., 1] / P[..., 2] / tile_ft
    T = tex.shape[0]
    mx = (u % 1) * T
    my = (v % 1) * T
    small = cv2.resize(tex, (256, 256), interpolation=cv2.INTER_AREA)
    far = cv2.remap(small, (mx / 4).astype(np.float32), (my / 4).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    near = cv2.remap(tex, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    # crude mip choice by distance from camera (rows near the top are far away)
    k = np.clip((np.abs(P[..., 2]) / np.abs(P[..., 2]).max()), 0, 1)[..., None]
    return near * k + far * (1 - k)


def mix(room, d, preset, blend='domino', gloss=True, stats=None):
    A = read(f'{d}/{room}_A.exr')
    meta = json.load(open(f'{d}/{room}_meta.json'))
    H, W = A['floor'].shape
    w = weights(preset)
    bg = sum(w[i] * A[g] for i, g in enumerate(GROUPS))
    out = bg.copy()
    cover = np.clip(A['floor'], 0, 1)[..., None]
    if blend:
        alb = chip_albedo(meta, blend, H, W)
        shade = sum(w[i] * A[g] for i, g in enumerate(GROUPS)) / 0.5
        fl = alb * shade
        try:
            B = read(f'{d}/{room}_B.exr')
        except Exception:
            B = None
        out = bg * (1 - cover) + fl * cover
    means = stats or {g: float((A[g] @ LUM).mean()) for g in GROUPS}
    # put the indoor lights on a sensible scale: full ceiling lights ~ 45% of a bright afternoon,
    # full lamps ~ 20% (so they read as accents)
    day = sum(float(v @ LUM) * means[g] for v, g in zip(weights('bright_afternoon'), GROUPS))
    unit = {g: 1.0 for g in GROUPS}
    unit['ceiling'] = 0.45 * day / max(means['ceiling'], 1e-9)
    unit['lamps'] = 0.2 * day / max(means['lamps'], 1e-9)
    w = np.array([w[i] * unit[g] for i, g in enumerate(GROUPS)])
    bg = sum(w[i] * A[g] for i, g in enumerate(GROUPS))
    if blend:
        shade = bg / 0.5
        fl = alb * shade
        try:
            gl = sum(w[i] * B[g] for i, g in enumerate(GROUPS))
            full = np.zeros_like(bg)
            f = A['floor'] > 0.01
            ys, xs = np.where(f)
            x0 = max(0, xs.min() - 4); y1 = min(H, ys.max() + 1 + 4)
            y0 = y1 - gl.shape[0]
            full[y0:y1, x0:x0 + gl.shape[1]] = gl
            fl = fl + full
        except Exception as e:
            print('no gloss', e)
        out = bg * (1 - cover) + fl * cover
    else:
        out = bg
    L = sum(float(w[i] @ LUM) * means[g] for i, g in enumerate(GROUPS))
    Lref = day
    lr = max(L / Lref, 1e-7)
    adapt = lr ** 0.75 if lr >= 0.05 else 0.05 ** 0.75 * (lr / 0.05) ** 0.35
    exp = 0.46 / adapt / Lref
    # camera-style white balance that removes about 60% of the light's color cast
    crgb = {g: (A[g].reshape(-1, 3).mean(0)) for g in GROUPS}
    cav = sum(w[i] * crgb[g] for i, g in enumerate(GROUPS))
    cav = cav / max(cav @ LUM, 1e-9)
    wb = 1.0 / np.maximum(cav, 1e-4) ** 0.6
    wb = wb / (wb @ LUM)
    img = srgb(aces(out * exp * wb))
    return (img * 255).astype(np.uint8)


if __name__ == '__main__':
    room, d, outp, preset = sys.argv[1:5]
    blend = sys.argv[5] if len(sys.argv) > 5 else 'domino'
    img = mix(room, d, preset, None if blend == 'none' else blend)
    cv2.imwrite(outp, img[:, :, ::-1])
