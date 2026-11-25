"""Photos from The Coating Crew's own Facebook page (facebook.com/TheCoatingCrew), captured from the public
photo viewer. This script trims the captures, turns sideways phone shots upright, softens bystanders and a
license plate, and writes the web sizes. No color changes are made: these are shown as the crew posted them.

Before and after pairs are lined up to each other (a geometric registration only, so the wall, doors and
fixtures sit in the same place in both frames) and cropped to the area both photos share.

Usage: python3 tools/photos/fb.py <folder with the captures>
"""
import json
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = sys.argv[1] if len(sys.argv) > 1 else ''

# capture number -> photo. "rot" marks a portrait photo that was captured lying on its side.
SHOTS = {
    'hotrods':            dict(n=18, fbid='1921174734697548', city='', kind='Chip floor', alt='Two classic cars parked on a glossy gray chip floor'),
    'jeep':               dict(n=20, fbid='1921174531364235', city='', kind='Our Jeep', alt='The Coating Crew Jeep parked between two stands of chip floor samples'),
    'stairs-edina':       dict(n=21, fbid='1915255298622825', city='Edina', kind='Stairs', alt='A stairway and landing coated in a tan chip finish'),
    'garage-edina':       dict(n=27, fbid='1915255291956159', city='Edina', kind='Garage', alt='A garage with a light tan chip floor'),
    'prep-hastings':      dict(n=15, fbid='1911272329021122', city='Hastings', kind='Prep', alt='A floor grinder and dust vacuum on bare garage concrete'),
    'prep-hastings-2':    dict(n=14, fbid='1911272345687787', city='Hastings', kind='Prep', alt='A floor grinder, vacuums and hoses spread across a large bare garage floor'),
    'garage-hastings':    dict(n=28, fbid='1911272342354454', city='Hastings', kind='Large garage', alt='A large garage with a finished gray chip floor'),
    'garage-cabinets':    dict(n=19, fbid='1902344353247253', city='', kind='Garage', alt='A garage with white cabinets and a gray chip floor'),
    'shop-igh':           dict(n=23, fbid='1888732324608456', city='Inver Grove Heights', kind='Chip floor', alt='A tall room with a wood stair and a gray chip floor'),
    'basement-wsp':       dict(n=13, fbid='1867716416710047', city='West Saint Paul', kind='Basement', alt='A basement with white block walls and a gray chip floor'),
    'basement-wsp-before': dict(n=12, fbid='1867716433376712', city='West Saint Paul', kind='Basement, before', alt='The same basement before coating, with bare patched concrete'),
    'crew-arena':         dict(n=16, fbid='1863276780487344', city='', kind='Crew at work', alt='Crew members running floor grinders across a large red floor'),
    'grinder':            dict(n=17, fbid='1863276760487346', city='', kind='Prep', alt='A floor grinder taking an old red coating off concrete'),
    'barn-henderson':     dict(n=25, fbid='1860538344094521', city='Henderson', kind='Steel building', alt='A large steel-sided building with a gray chip floor'),
    'commercial-eagan':   dict(n=26, fbid='1845119475636408', city='Eagan', kind='Commercial floor', alt='A large commercial room with a glossy concrete floor'),
    'steps-lakeelmo':     dict(n=22, fbid='1823105341171155', city='Lake Elmo', kind='Steps', alt='Garage steps and floor coated in a gray chip finish'),
}
# before and after pairs: (before capture, after capture). A tuple is one photo captured in two halves.
# "slide" pairs were shot from nearly the same spot, so they are lined up for a drag-to-compare view.
PAIRS = {
    'cottagegrove': dict(before=10, after=11, fbid='1851292685019087', city='Cottage Grove', kind='Garage', slide=True),
    'forestlake':   dict(before=(2, 3), after=(4, 5), fbid='1906564492825239', city='Forest Lake', kind='Garage'),
    'wsp':          dict(before=12, after=13, fbid='1867716416710047', city='West Saint Paul', kind='Basement'),
    'shelf':        dict(before=6, after=7, fbid='1894176897397332', city='', kind='Garage'),
}
SOFTEN = {  # regions to blur, as fractions of the frame: bystanders and a license plate
    'jeep': [(0.045, 0.225, 0.26, 0.365)],
    'hotrods': [(0.458, 0.346, 0.494, 0.382)],
}


def cap(n):
    """Load one capture, trimmed of the viewer edge."""
    import glob
    f = glob.glob(os.path.join(SRC, f'screenshot-*-{n}.png'))
    im = Image.open(f[0]).convert('RGB')
    return im.crop((0, 0, im.width - 10, im.height))


def load(spec):
    if isinstance(spec, tuple):                      # two captures: the top 350 px of the page, then the rest
        top, bot = cap(spec[0]), cap(spec[1])
        bot = bot.crop((0, 0, bot.width, bot.height // 2))
        im = Image.new('RGB', (top.width, top.height + bot.height))
        im.paste(top, (0, 0)); im.paste(bot, (0, top.height))
    else:
        im = cap(spec)
    a = np.asarray(im).astype(int).sum(axis=2)       # trim any black bars left by the viewer
    rows = np.where(a.mean(axis=1) > 12)[0]; cols = np.where(a.mean(axis=0) > 12)[0]
    return im.crop((cols[0], rows[0], cols[-1] + 1, rows[-1] + 1))


def soften(im, boxes):
    for x0, y0, x1, y1 in boxes:
        box = (int(x0 * im.width), int(y0 * im.height), int(x1 * im.width), int(y1 * im.height))
        im.paste(im.crop(box).filter(ImageFilter.GaussianBlur(7)), box)
    return im


def save(im, name, folder='img/w', widths=(640, 960, 1200)):
    os.makedirs(os.path.join(ROOT, folder), exist_ok=True)
    for w in widths:
        r = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        r.save(os.path.join(ROOT, folder, f'{name}-{w}.webp'), 'WEBP', quality=72 if w <= 640 else 76, method=6)


def register(before, after):
    """Warp the before photo into the after photo's frame using matched points on the walls and fixtures.
    The floor is left out of the matching, because the floor is the part that changed."""
    b, a = cv2.cvtColor(np.asarray(before), cv2.COLOR_RGB2GRAY), cv2.cvtColor(np.asarray(after), cv2.COLOR_RGB2GRAY)
    h, w = a.shape
    clahe = cv2.createCLAHE(3.0, (8, 8))
    sift = cv2.SIFT_create(12000, contrastThreshold=0.012, edgeThreshold=14)
    best = (None, 0)
    for keep in (0.50, 0.62, 0.42):                  # share of the frame, from the top, that holds walls
        mask = np.zeros((h, w), np.uint8); mask[:int(h * keep)] = 255
        kb, db = sift.detectAndCompute(clahe.apply(b), mask); ka, da = sift.detectAndCompute(clahe.apply(a), mask)
        if db is None or da is None or len(kb) < 20 or len(ka) < 20:
            continue
        good = [m for m, n in cv2.BFMatcher().knnMatch(db, da, k=2) if m.distance < 0.8 * n.distance]
        if len(good) < 12:
            continue
        pb = np.float32([kb[m.queryIdx].pt for m in good]); pa = np.float32([ka[m.trainIdx].pt for m in good])
        H, inl = cv2.findHomography(pb, pa, cv2.RANSAC, 5.0)
        if H is None:
            continue
        c = cv2.perspectiveTransform(np.float32([[[0, 0]], [[w, 0]], [[w, h]], [[0, h]]]), H).reshape(4, 2)
        area = cv2.contourArea(c) / (w * h)
        sane = 0.55 < area < 1.7 and cv2.isContourConvex(c.astype(np.float32)) and np.abs(c - np.float32([[0, 0], [w, 0], [w, h], [0, h]])).max() < 0.33 * w
        if sane and int(inl.sum()) > best[1]:
            warped = cv2.warpPerspective(np.asarray(before), H, (w, h), flags=cv2.INTER_LANCZOS4)
            valid = cv2.warpPerspective(np.full(b.shape, 255, np.uint8), H, (w, h))
            best = ((warped, valid), int(inl.sum()))
    return best


def common_crop(valid, ratio=4 / 3):
    """Largest centered 4:3 box that lies inside the warped photo."""
    h, w = valid.shape
    best = None
    for s in np.linspace(1.0, 0.6, 41):
        cw, ch = int(w * s), int(w * s / ratio)
        if ch > h:
            continue
        for cy in np.linspace(0, h - ch, 9).astype(int):
            for cx in np.linspace(0, w - cw, 9).astype(int):
                if valid[cy:cy + ch, cx:cx + cw].min() > 250:
                    return cx, cy, cx + cw, cy + ch
    return best


def main():
    man = {'shots': {}, 'pairs': {}}
    for name, s in SHOTS.items():
        im = load(s['n'])
        if s.get('rot'):
            im = im.transpose(Image.ROTATE_270)
        if name in SOFTEN:
            im = soften(im, SOFTEN[name])
        im.save(os.path.join(ROOT, 'img/photos', f'fb-{name}.jpg'), 'JPEG', quality=88, optimize=True, progressive=True)
        save(im, f'fb-{name}')
        man['shots'][name] = dict(fbid=s['fbid'], city=s['city'], kind=s['kind'], alt=s['alt'], w=im.width, h=im.height)
        print('shot', name, im.size)
    for name, p in PAIRS.items():
        before, after = load(p['before']), load(p['after'])
        aligned, inl = False, 0
        if p.get('slide'):
            if before.size != after.size:
                before = before.resize(after.size, Image.LANCZOS)
            reg, inl = register(before, after)
            if reg and inl >= 40:
                warped, valid = reg
                box = common_crop(valid)
                if box:
                    before = Image.fromarray(warped).crop(box); after = after.crop(box); aligned = True
        widths = (640, 960, 1200) if aligned else (480, 960)
        save(before, f'{name}-before', 'img/ba', widths); save(after, f'{name}-after', 'img/ba', widths)
        man['pairs'][name] = dict(fbid=p['fbid'], city=p['city'], kind=p['kind'], aligned=aligned, w=after.width, h=after.height)
        print('pair', name, before.size, after.size, 'aligned' if aligned else 'side by side', inl)
    json.dump(man, open(os.path.join(ROOT, 'tools/photos/fb.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
