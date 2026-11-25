"""Share images (1200x630) for every page: the page's own headline and picture with the logo.

    python3 tools/og/build_og.py     (run after tools/build_pages.py, then run the build again to link them)
"""
import asyncio
import glob
import html
import os
import re

from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOGO = open(os.path.join(ROOT, 'tools', 'pages', '_logo.svg')).read()
# real floors from the crew's own Facebook page lead wherever the page is about finished work
PICS = {'index.html': 'img/w/fb-hotrods-1200.webp', 'colors.html': 'img/studio/garage-poster-1320.webp',
        'garage-floor-coating.html': 'img/w/fb-hotrods-1200.webp', 'basement-floor-coating.html': 'img/w/fb-basement-wsp-1200.webp',
        'gallery.html': 'img/w/fb-garage-hastings-1200.webp', 'residential.html': 'img/w/fb-garage-cabinets-1200.webp',
        'about-us.html': 'img/w/fb-jeep-1200.webp', 'reviews.html': 'img/w/fb-garage-edina-1200.webp',
        'finishes.html': 'img/systems/lineup-1600.webp', 'owner.html': 'img/studio/garage-poster-1320.webp',
        '404.html': 'img/studio/garage-bare-1320.webp', 'search.html': 'img/w/banner-chip-1200.webp'}

TPL = '''<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:"Archivo";font-weight:100 900;font-stretch:62% 125%;src:url(file://{root}/fonts/archivo-wdth.woff2) format("woff2")}}
*{{margin:0;box-sizing:border-box}}
body{{width:1200px;height:630px;background:#1D232A;font-family:Archivo,sans-serif;color:#fff;overflow:hidden;position:relative}}
.pic{{position:absolute;right:0;top:0;width:740px;height:630px;object-fit:cover;{pos}}}
.fade{{position:absolute;inset:0;background:linear-gradient(90deg,#1D232A 0,#1D232A 470px,rgba(29,35,42,.82) 570px,rgba(29,35,42,.35) 680px,rgba(29,35,42,0) 800px)}}
.txt{{position:absolute;left:64px;top:60px;width:600px;display:flex;flex-direction:column;gap:26px}}
.logo{{width:300px}} .logo svg{{width:100%;height:auto;display:block;overflow:visible}}
h1{{font-stretch:75%;font-weight:800;font-size:{size}px;line-height:1;letter-spacing:-.012em;{caps}}}
.foot{{position:absolute;left:64px;bottom:50px;display:flex;flex-direction:column;align-items:flex-start;gap:14px;font-size:24px;font-weight:700;max-width:640px;white-space:nowrap}}
.pill{{background:#F06722;color:#1A1E23;padding:10px 18px;border-radius:99px;font-weight:800}}
.chk{{position:absolute;left:0;right:0;bottom:0;height:14px;background:conic-gradient(#1A1E23 25%,#fff 0 50%,#1A1E23 0 75%,#fff 0) 0 0/14px 14px}}
</style></head><body>
<img class="pic" src="file://{root}/{pic}">
<div class="fade"></div>
<div class="txt"><div class="logo">{logo}</div><h1>{title}</h1></div>
<div class="foot">{foot}</div>
<div class="chk"></div>
</body></html>'''


async def main():
    pages = sorted(glob.glob(os.path.join(ROOT, '*.html')))
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width': 1200, 'height': 630})
        for path in pages:
            name = os.path.basename(path)
            s = open(path).read()
            h1 = re.search(r'<h1[^>]*>(.*?)</h1>', s, flags=re.S)
            title = html.unescape(re.sub(r'<[^>]+>', '', h1.group(1))).strip() if h1 else 'The Coating Crew'
            pic = PICS.get(name)
            if not pic:
                m = re.search(r'class="pimg[^"]*"><img src="([^"]+)"', s)
                pic = m.group(1) if m else 'img/studio/garage-poster-1320.webp'
            home = name == 'index.html'
            foot = ('<span class="pill">Ask about our two-stall garage floor: $2,495*</span><span>Free estimates: (651) 263-8557</span><span style="font-size:15px;font-weight:600">*Based on 400 sq ft of new concrete, no repairs needed. Other costs may apply.</span>' if home
                    else '<span>Free estimates across Minneapolis / Saint Paul</span><span>(651) 263-8557</span>')
            size = 66 if len(title) < 40 else 56 if len(title) < 64 else 48
            out = TPL.format(root=ROOT, pic=pic, logo=LOGO, title=html.escape(title), foot=foot, size=size + (8 if home else 0),
                             caps='text-transform:uppercase;font-stretch:62%;font-weight:850;line-height:.92' if home else '',
                             pos='object-position:60% 50%' if 'lineup' in pic else '')
            tmp = os.path.join(ROOT, 'tools', 'og', '_card.html')
            open(tmp, 'w').write(out)
            await pg.goto('file://' + tmp)
            await pg.wait_for_timeout(250)
            await pg.screenshot(path=os.path.join(ROOT, 'img', 'og', name[:-5] + '.jpg'), type='jpeg', quality=84)
            print('card', name, '|', title)
        os.remove(tmp)
        await b.close()

asyncio.run(main())
