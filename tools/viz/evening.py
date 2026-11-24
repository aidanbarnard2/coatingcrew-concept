"""Relight a daytime room photo as evening: daylight gone, the room's own fixtures on, warm color."""
import numpy as np
from build import poly_mask

WARM = np.array([1.0, 0.80, 0.58])


def gauss(W, H, x0, y0, sx, sy):
    y, x = np.mgrid[0:H, 0:W].astype(float)
    return np.exp(-(((x - x0) / sx) ** 2 + ((y - y0) / sy) ** 2) / 2)


def make(R, lin, shade, gloss):
    E, W, H = R['eve'], R['W'], R['H']
    L = np.full((H, W), E['amb'])
    for l in E['lights']:
        L += l['k'] * gauss(W, H, l['x'], l['y'], l['sx'], l['sy'])
    # gentle vignette, like a dim room photographed with the lights on
    y, x = np.mgrid[0:H, 0:W].astype(float)
    r = np.hypot((x - W / 2) / (W / 2), (y - H / 2) / (H / 2))
    L *= 1 - E.get('vig', 0.25) * np.clip(r - 0.35, 0, 1) ** 1.5
    Lc = L[..., None] * WARM
    bg = lin * Lc
    for w in E.get('windows', []):
        m = poly_mask(W, H, [w['poly']])[..., None]
        night = lin * 0.05 + np.array(w.get('night', (0.004, 0.007, 0.016)))
        bg = bg * (1 - m) + night * m
    glow = np.zeros((H, W))
    for b in E.get('bulbs', []):
        glow += b['k'] * gauss(W, H, b['x'], b['y'], b['r'], b['r'])
    bg = bg + glow[..., None] * np.array([1.0, 0.86, 0.66])
    sh = shade * Lc
    gl = gloss * L[..., None] * WARM * E.get('gloss_keep', 0.8)
    for s in E.get('spots', []):  # reflections of the lit fixtures in the clear coat
        gl += (s['k'] * gauss(W, H, s['x'], s['y'], s['sx'], s['sy']))[..., None] * np.array([1.0, 0.86, 0.66])
    return dict(bg=bg, shade=sh, gloss=gl)
