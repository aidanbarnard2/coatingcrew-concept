"""Stills for the page: the bare-concrete first frame, the Domino fallback and the room thumbnails, all in the
default 'Showroom lights' look (midday sun with every indoor light on at 5000K)."""
import sys
sys.path.insert(0, '/home/claude/coatingcrew-concept/tools/studio')
import mix
from PIL import Image
orig = mix.read
GLOSS = {'k': 1.0}
def read(p):
    d = orig(p)
    if p.endswith('_B.exr'):
        d = {k: v * GLOSS['k'] for k, v in d.items()}
    return d
mix.read = read
OUT = '/home/claude/coatingcrew-concept/img/studio/'
for room in (sys.argv[1:] or ['garage', 'basement', 'sunroom']):
    GLOSS['k'] = 0.035
    bare = Image.fromarray(mix.mix(room, 'final', 'showroom', 'bare-concrete'))
    GLOSS['k'] = 1.0
    dom = Image.fromarray(mix.mix(room, 'final', 'showroom', 'domino'))
    dom.save(f'{OUT}{room}-poster.jpg', 'JPEG', quality=84, progressive=True, optimize=True)
    for w in (660, 990, 1320):
        bare.resize((w, w * 2 // 3), Image.LANCZOS).save(f'{OUT}{room}-bare-{w}.webp', 'WEBP', quality=80, method=6)
        dom.resize((w, w * 2 // 3), Image.LANCZOS).save(f'{OUT}{room}-poster-{w}.webp', 'WEBP', quality=70, method=6)
    th = dom.resize((210, 140), Image.LANCZOS)
    th.save(f'{OUT}{room}-thumb.webp', 'WEBP', quality=74, method=6)
    th.resize((270, 180), Image.LANCZOS).save(f'{OUT}{room}-thumb.jpg', 'JPEG', quality=82)
    print(room, 'ok')
