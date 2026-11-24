"""Build the hero logo as an SVG: The Coating Crew's ribbon and checkered flags, traced from img/logo.webp.

    python3 tools/logo/build_logo.py      (writes tools/pages/_logo.svg)

The lettering is Poppins ExtraBold (the logo's typeface, SIL Open Font License) converted to outlines and set
along the ribbon's curve, so the page needs no extra font. The flags are drawn at rest; site.js waves them.
"""
import math
import os

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'pages', '_logo.svg')
ORANGE, FOLD = '#F06722', '#C9461C'


def bez(p0, p1, p2, t):
    u = 1 - t
    return (u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0], u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1])


def lettering(text='THE COATING CREW', size=79.0, target=928.0):
    f = TTFont(os.path.join(HERE, 'poppins-latin-800-normal.woff'))
    gs, cmap, hmtx = f.getGlyphSet(), f.getBestCmap(), f['hmtx']
    k = size / f['head'].unitsPerEm
    names = [cmap[ord(c)] for c in text]
    adv = [hmtx[n][0] * k for n in names]
    spacing = (target - sum(adv)) / (len(text) - 1)
    # baseline: a gentle arc, highest in the middle (measured from the logo)
    p0, p1, p2 = (150, 318), (631.5, 222), (1113, 318)
    N = 3000
    pts = [bez(p0, p1, p2, i / N) for i in range(N + 1)]
    cum = [0.0]
    for a, b in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    total = cum[-1]

    def at(d):
        lo, hi = 0, N
        while lo < hi:
            mid = (lo + hi) // 2
            if cum[mid] < d:
                lo = mid + 1
            else:
                hi = mid
        i = max(1, min(N, lo))
        a, b = pts[i - 1], pts[i]
        return b, math.atan2(b[1] - a[1], b[0] - a[0])
    out, d = [], (total - target) / 2
    for n, a in zip(names, adv):
        if n != 'space':
            pen = SVGPathPen(gs)
            gs[n].draw(pen)
            (x, y), th = at(d + a / 2)
            c, s = math.cos(th), math.sin(th)
            # font units (y up) -> scaled, centered on the glyph, rotated to the curve, moved onto it
            ox, oy = -a / 2, 0.0
            m = [k * c, k * s, k * s, -k * c, x + c * ox - s * oy, y + s * ox + c * oy]
            out.append(f'<path transform="matrix({",".join(f"{v:.4f}" for v in m)})" d="{pen.getCommands()}"/>')
        d += a + spacing
    return ''.join(out)


def cloth(top, bottom, side, t=0.0, NU=6, NV=7, L=300, W=260):
    """Checkered flag cloth at time t (same math as site.js): fixed along the pole, swept outward and down."""
    dx, dy = bottom[0] - top[0], bottom[1] - top[1]
    ln = math.hypot(dx, dy)
    d = (dx / ln, dy / ln)
    o = (-d[1], d[0]) if side < 0 else (d[1], -d[0])
    o = (o[0] * 0.985 + d[0] * 0.174, o[1] * 0.985 + d[1] * 0.174)
    A = (top[0] + d[0] * 10, top[1] + d[1] * 10)

    def ph(u, v):
        return 6.2832 * (1.15 * v - t * 0.55) + 0.9 * u
    P = [[None] * (NV + 1) for _ in range(NU + 1)]
    for i in range(NU + 1):
        for j in range(NV + 1):
            u, v = i / NU, j / NV
            a = ph(u, v)
            along = u * L + 24 * v * math.sin(a)
            away = v * W - 12 * v * (1 - math.cos(a))
            P[i][j] = (A[0] + d[0] * along + o[0] * away, A[1] + d[1] * along + o[1] * away)
    cells = []
    for i in range(NU):
        for j in range(NV):
            q = [P[i][j], P[i + 1][j], P[i + 1][j + 1], P[i][j + 1]]
            dark = (i + j) % 2 == 0
            col = '#1A1A1A' if dark else '#F4F4F4'
            pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in q)
            cells.append(f'<polygon points="{pts}" fill="{col}" stroke="{col}" stroke-width="1.2" stroke-linejoin="round"{" data-d" if dark else ""}/>')
    e = [P[0][0]] + [P[0][j] for j in range(1, NV + 1)] + [P[i][NV] for i in range(1, NU + 1)] + [P[NU][j] for j in range(NV - 1, -1, -1)]
    edge = 'M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in e)
    return ''.join(cells) + f'<path class="cc-edge" d="{edge}" fill="none" stroke="#FFFFFF" stroke-width="5" stroke-linejoin="round"/>'


def svg():
    ribbon = (f'<path d="M80 254 Q631.5 88 1183 254 L1257 316 L1183 356 L1218 437 L1046 386 L1048 350 '
              f'Q631.5 272 215 350 L217 386 L45 437 L80 356 L6 316 Z" fill="{ORANGE}"/>'
              f'<path d="M215 350 L110 381 L217 386 Z" fill="{FOLD}"/><path d="M1048 350 L1153 381 L1046 386 Z" fill="{FOLD}"/>')
    band = 'M80 254 Q631.5 88 1183 254 L1183 356 L1048 350 Q631.5 272 215 350 L80 356 Z'
    words = lettering()
    return f'''<svg class="cc-logo" id="ccLogo" viewBox="0 0 1263 446" role="img" aria-labelledby="ccLogoTitle">
<title id="ccLogoTitle">The Coating Crew</title>
<defs><clipPath id="ccBand"><path d="{band}"/></clipPath><linearGradient id="ccShineGrad" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".5"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>
<g class="cc-flag cc-flag-l"><g class="cc-cloth" data-top="420,10" data-bottom="692,420" data-side="-1">{cloth((420, 10), (692, 420), -1)}</g><line x1="420" y1="10" x2="692" y2="430" stroke="#E9E9E9" stroke-width="11" stroke-linecap="round"/></g>
<g class="cc-flag cc-flag-r"><g class="cc-cloth" data-top="845,10" data-bottom="573,420" data-side="1" data-t="0.35">{cloth((845, 10), (573, 420), 1, 0.35)}</g><line x1="845" y1="10" x2="573" y2="430" stroke="#E9E9E9" stroke-width="11" stroke-linecap="round"/></g>
<g class="cc-ribbon">{ribbon}<g clip-path="url(#ccBand)"><rect class="cc-shine" x="-300" y="60" width="240" height="340" fill="url(#ccShineGrad)" transform="skewX(-20)"/></g>
<g class="cc-words"><g fill="#141414" transform="translate(5 5)">{words}</g><g fill="#FFFFFF">{words}</g></g></g>
</svg>
'''


if __name__ == '__main__':
    s = svg()
    open(OUT, 'w').write(s)
    print('wrote', OUT, len(s), 'bytes')
