"""Bake the data the browser needs to re-coat a real room photo.

For each room this writes (to OUT):
  <key>-day.jpg      the original photo
  <key>-eve.jpg      the same photo relit for evening (lights on, daylight gone)
  <key>-mask.png     R = how much of the pixel is coated floor/wall, G = which surface (0/1/2)
  <key>-light.jpg    R,G,B = the room's light on the floor in daylight (divided out of the old floor color)
  <key>-light-eve.jpg  same, evening
  <key>-gloss.jpg    R = reflections in the clear coat by day, G = by evening
and returns the per-surface matrices (pixel -> feet) for the page.
"""
import json, sys
import numpy as np
import cv2
from PIL import Image, ImageDraw

OUT = sys.argv[1] if len(sys.argv) > 1 else 'out'
LIGHT_SCALE = 2.5   # light map stores shade/LIGHT_SCALE with a 1/2.2 curve
GLOSS_SCALE = 1.0


def srgb_to_lin(a):
    a = a / 255.0
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(a):
    a = np.clip(a, 0, 1)
    return np.where(a <= 0.0031308, a * 12.92, 1.055 * a ** (1 / 2.4) - 0.055) * 255.0


def poly_mask(W, H, polys, ss=4):
    img = Image.new('L', (W * ss, H * ss), 0)
    d = ImageDraw.Draw(img)
    for p in polys:
        d.polygon([(x * ss, y * ss) for x, y in p], fill=255)
    return np.asarray(img.resize((W, H), Image.LANCZOS), float) / 255.0


def masked_blur(img, m, sigma):
    num = cv2.GaussianBlur(img * m[..., None] if img.ndim == 3 else img * m, (0, 0), sigma)
    den = cv2.GaussianBlur(m, (0, 0), sigma)
    den = np.maximum(den, 1e-4)
    return num / (den[..., None] if img.ndim == 3 else den)


def build(R, evening):
    key, W, H, room = R['key'], R['W'], R['H'], R['room']
    photo = np.asarray(Image.open(R['path']).convert('RGB'), float)
    assert photo.shape[:2] == (H, W), (photo.shape, W, H)

    # ---- coverage and surface ids
    surf_masks = [poly_mask(W, H, [s['poly']]) for s in R['surfaces']]
    hole = poly_mask(W, H, R['holes']) if R['holes'] else np.zeros((H, W))
    if R.get('extra_hole') is not None:
        hole = np.maximum(hole, R['extra_hole'](photo))
    cover = np.clip(sum(surf_masks), 0, 1) * (1 - hole)
    stack = np.stack([cv2.dilate(m, np.ones((5, 5))) for m in surf_masks])
    sid = np.argmax(stack, axis=0).astype(np.uint8)
    mask_img = np.zeros((H, W, 3), np.uint8)
    mask_img[..., 0] = np.round(cover * 255)
    mask_img[..., 1] = sid * 85
    Image.fromarray(mask_img).save(f'{OUT}/{key}-mask.png', optimize=True)

    # ---- light and reflections on the coated surfaces
    lin = srgb_to_lin(photo)
    inner = (cover > 0.98).astype(float)
    inner = cv2.erode(inner, np.ones((3, 3)))
    med = cv2.medianBlur(np.clip(photo, 0, 255).astype(np.uint8), R.get('median', 9))
    med_lin = srgb_to_lin(med.astype(float))
    lum = med_lin @ np.array([0.2126, 0.7152, 0.0722])
    # diffuse light: the lower envelope of the floor brightness, smoothed
    k = R.get('env_k', 15)
    low = cv2.erode(np.where(inner > 0, lum, 10.0).astype(np.float32), np.ones((k, k)))
    low = np.where(low > 5, lum, low)
    diff_l = masked_blur(low, inner, R.get('diff_sigma', 10))
    col = masked_blur(med_lin, inner, R.get('diff_sigma', 10))
    col_l = col @ np.array([0.2126, 0.7152, 0.0722])
    diff_rgb = col * (diff_l / np.maximum(col_l, 1e-5))[..., None]
    blur_rgb = masked_blur(med_lin, inner, 1.2)
    diff_l3 = diff_rgb
    gloss = np.clip(blur_rgb - diff_l3 - R.get('gloss_floor', 0.01), 0, None)
    gloss = cv2.GaussianBlur(gloss, (0, 0), 0.8)
    albedo = srgb_to_lin(np.array(R['albedo_srgb'], float))
    shade = diff_rgb / albedo
    if R.get('neutral_light'):
        sl = shade @ np.array([0.2126, 0.7152, 0.0722])
        tint = (shade * inner[..., None]).sum((0, 1)) / max(inner.sum(), 1)
        tint = tint / (tint @ np.array([0.2126, 0.7152, 0.0722]))
        shade = sl[..., None] * tint
        gl_l = gloss @ np.array([0.2126, 0.7152, 0.0722])
        gloss = gl_l[..., None] * np.ones(3)
    # fill outside the coverage so texture filtering at the edges reads sensible values
    fill = cv2.dilate(inner, np.ones((5, 5)))
    shade = masked_blur(shade, inner, 3) * (1 - inner[..., None]) + shade * inner[..., None]

    # ---- evening
    eve = evening(R, lin, shade, gloss)

    def enc_light(s):
        return np.clip((np.clip(s, 0, None) / LIGHT_SCALE) ** (1 / 2.2) * 255, 0, 255).astype(np.uint8)

    def enc_gloss(g):
        return np.clip((np.clip(g, 0, None) / GLOSS_SCALE) ** (1 / 2.2) * 255, 0, 255).astype(np.uint8)

    Image.fromarray(np.vstack([enc_light(shade), enc_light(eve['shade'])])).save(f'{OUT}/{key}-light.jpg', quality=90)
    Image.fromarray(np.vstack([enc_gloss(gloss), enc_gloss(eve['gloss'])])).save(f'{OUT}/{key}-gloss.jpg', quality=90)
    Image.fromarray(photo.astype(np.uint8)).save(f'{OUT}/{key}-day.jpg', quality=88, optimize=True, progressive=True)
    Image.fromarray(np.round(lin_to_srgb(eve['bg'])).astype(np.uint8)).save(f'{OUT}/{key}-eve.jpg', quality=88, optimize=True, progressive=True)

    th = Image.fromarray(photo.astype(np.uint8)); th.thumbnail((240, 180)); th.save(f'{OUT}/{key}-thumb.jpg', quality=82)
    mats = []
    for s in R['surfaces']:
        if s['kind'] == 'floor':
            M = room.Hfloor
        else:
            M = room.wall_H(s['along'], s['base'])
        mats.append([float(x) for x in (M / np.abs(M).max()).ravel()])
    return dict(key=key, name=R['name'], W=W, H=H, mats=mats, tile=R.get('tile_ft', 1.0),
                orig=R.get('orig_label', ''), lightScale=LIGHT_SCALE, glossScale=GLOSS_SCALE)
