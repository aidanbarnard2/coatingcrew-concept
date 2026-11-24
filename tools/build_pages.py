"""Wrap every page of the concept site in the same head, header, footer and scripts.

Run from the repo root:  python3 tools/build_pages.py
Pages with a source in tools/pages/ (home, colors, finishes, owner) are built from it; every other page keeps its
own <main> content, which is cleaned up to the current design (real <img> tags with WebP sizes instead of CSS
backgrounds, no label lines above headings, no arrows on links). Safe to run again.
"""
import glob
import html
import json
import os
import re

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'tools', 'pages')
SITE = 'https://aidanbarnard2.github.io/coatingcrew-concept/'
PHONE, TEL = '(651) 263-8557', 'tel:+16512638557'
CSS_V = '4'
# the concept stays out of search results; set CC_INDEX=1 when this becomes the live site
ROBOTS = 'index, follow' if os.environ.get('CC_INDEX') else 'noindex, nofollow'

NAV = [('residential.html', 'Residential'), ('commercial.html', 'Commercial'),
       ('colors.html', 'Colors &amp; Visualizer'), ('gallery.html', 'Our Work'), ('about-us.html', 'About')]
SECTION = {'industrial.html': 'commercial.html', 'reviews.html': 'gallery.html', 'finishes.html': 'colors.html',
           'certified-professionals.html': 'about-us.html', 'worry-free-guarantee.html': 'about-us.html',
           'trailers.html': 'about-us.html'}
EXTRA_JS = {'index.html': ['visualizer.js', 'home.js'], 'colors.html': ['visualizer.js'], 'owner.html': ['home.js']}
OG_IMG = {'index.html': 'img/studio/garage-poster.jpg', 'colors.html': 'img/studio/garage-poster.jpg',
          'finishes.html': 'img/systems/lineup.jpg'}
NO_SEARCH = {'owner.html'}

I_PHONE = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round"><path d="M5 3h4l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 5a2 2 0 0 1 2-2z"/></svg>'
I_MENU = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg>'
I_LEFT = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5l-7 7 7 7"/></svg>'
I_RIGHT = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M9 5l7 7-7 7"/></svg>'

BUSINESS = {
    '@type': 'HomeAndConstructionBusiness', '@id': SITE + '#business', 'name': 'The Coating Crew', 'url': SITE,
    'telephone': '+1-651-263-8557', 'image': SITE + 'img/photos/job-garage-5.jpg', 'logo': SITE + 'img/logo.webp',
    'description': 'Family-owned epoxy and polyurea floor coating company serving the Minneapolis / Saint Paul area since 1999.',
    'foundingDate': '1999',
    'address': {'@type': 'PostalAddress', 'streetAddress': '10967 Clark Rd, Ste E', 'addressLocality': 'Inver Grove Heights',
                'addressRegion': 'MN', 'postalCode': '55077', 'addressCountry': 'US'},
    'openingHoursSpecification': [{'@type': 'OpeningHoursSpecification', 'dayOfWeek': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                                   'opens': '07:00', 'closes': '18:00'}],
    'areaServed': {'@type': 'Place', 'name': 'Minneapolis / Saint Paul metro area'},
    'makesOffer': {'@type': 'Offer', 'name': 'Two-stall garage floor coating', 'price': '2495', 'priceCurrency': 'USD',
                   'description': 'Based on 400 square feet of new concrete with no repairs needed. Steps, stemwalls, joint fill, travel and more may add to the cost.'},
}


def esc(s):
    return html.escape(s, quote=True)


# ---------------------------------------------------------------- images
_dims = {}


def dims(path):
    if path not in _dims:
        try:
            _dims[path] = Image.open(os.path.join(ROOT, path)).size
        except Exception:
            _dims[path] = (1200, 900)
    return _dims[path]


def pic(src, alt='', sizes='(min-width:900px) 600px, 100vw', eager=False):
    """An <img> with WebP sizes for any photo from img/photos/."""
    m = re.match(r'img/photos/([\w-]+)\.jpg$', src)
    if m and os.path.exists(os.path.join(ROOT, f'img/w/{m.group(1)}-1200.webp')):
        a, b = f'img/w/{m.group(1)}-640.webp', f'img/w/{m.group(1)}-1200.webp'
        w, h = dims(b)
        load = ' fetchpriority="high"' if eager else ' loading="lazy"'
        return f'<img src="{b}" srcset="{a} 640w, {b} 1200w" sizes="{sizes}" alt="{esc(alt)}" width="{w}" height="{h}" decoding="async"{load}>'
    w, h = dims(src)
    load = ' fetchpriority="high"' if eager else ' loading="lazy"'
    return f'<img src="{src}" alt="{esc(alt)}" width="{w}" height="{h}" decoding="async"{load}>'


# ---------------------------------------------------------------- visualizer pieces
def _js_list(name, js):
    return re.findall(r"'([^']+)'", re.search(name + r": \[(.*?)\]", js).group(1))


VIZ_JS = open(os.path.join(ROOT, 'visualizer.js')).read()
GROUPS = [('gray', 'Grays and blues'), ('warm', 'Warm grays and stone'), ('tan', 'Tans and browns')]
ROOMS = json.load(open(os.path.join(ROOT, 'img', 'studio', 'rooms.json')))


def slug(n):
    return n.lower().replace(' ', '-')


def viz_stage():
    rooms = '\n'.join(
        f'      <button type="button" class="room" data-i="{i}" aria-pressed="{str(i == 0).lower()}"><img src="img/studio/{r["key"]}-thumb.webp" alt="" width="105" height="70" decoding="async"><span>{esc(r["name"])}</span></button>'
        for i, r in enumerate(ROOMS))
    label = f'{ROOMS[0]["name"]} with bare concrete, bright afternoon'
    return f'''<div class="s-viz">
    <div class="viz-stage">
      <img class="viz-photo" src="img/studio/garage-bare-1320.webp" srcset="img/studio/garage-bare-660.webp 660w, img/studio/garage-bare-990.webp 990w, img/studio/garage-bare-1320.webp 1320w" sizes="(min-width:1340px) 700px, (min-width:1001px) 56vw, calc(100vw - 32px)" alt="{label}" width="1320" height="880" fetchpriority="high">
      <canvas role="img" aria-hidden="true" aria-label="{label}"></canvas>
      <span class="viz-tag" aria-hidden="true"><b class="viz-tag-blend">Bare concrete</b><span class="viz-tag-light">Bright afternoon</span></span>
      <span class="loader" aria-hidden="true">Loading the room…</span>
    </div>
    <div class="viz-rooms" role="group" aria-label="Choose a room">
{rooms}
    </div>
  </div>'''


def viz_rail(est, p='v-'):
    groups = []
    for key, label in GROUPS:
        tiles = ''.join(
            f'<button type="button" class="sample" data-blend="{n}" aria-pressed="{str(n == "Domino").lower()}"><span class="face"><img src="img/colors/s/{slug(n)}.webp" alt="" width="160" height="160" loading="lazy" decoding="async"></span><span class="lab">{n}</span></button>'
            for n in _js_list(key, VIZ_JS))
        groups.append(f'<div class="rail-group"><p class="sub" id="{p}{key}">{label}</p><div class="viz-tiles" data-group="{key}" role="group" aria-labelledby="{p}{key}">{tiles}</div></div>')
    return f'''<div class="s-rail">
    <div class="rail-head">
      <div class="picked"><span class="loupe viz-loupe" aria-hidden="true" style="background-image:url(img/colors/l/domino.webp)"></span><div><span>Your sample</span><b class="viz-blend-name">Domino</b></div></div>
      <button type="button" class="toggle viz-orig" aria-pressed="false">Show bare concrete<span class="sw" aria-hidden="true"></span></button>
      <a class="btn btn-primary" href="{est}" data-price-floor>Price this floor</a>
      <div class="rail-btns"><button type="button" data-rail="prev" aria-label="Scroll the samples back">{I_LEFT}</button><button type="button" data-rail="next" aria-label="Scroll to more samples">{I_RIGHT}</button></div>
    </div>
    <p class="viz-nogl note" hidden>Your browser is showing still pictures, so the floor stays Domino here. The swatch above shows the blend you picked.</p>
    <div class="rail">
      {"".join(groups)}
    </div>
  </div>'''


def viz_desk(p='v-'):
    r = ROOMS[0]
    sun = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="12" cy="12" r="4.5"/><path d="M12 1.5v2.5M12 20v2.5M4.6 4.6l1.8 1.8M17.6 17.6l1.8 1.8M1.5 12H4M20 12h2.5M4.6 19.4l1.8-1.8M17.6 6.4l1.8-1.8"/></svg>'
    cloud = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round"><path d="M7 18h10a4 4 0 0 0 .6-7.95A6 6 0 0 0 6.1 9.2 4.5 4.5 0 0 0 7 18z"/></svg>'
    presets = [('morning', 'Sunny morning'), ('afternoon', 'Bright afternoon'), ('cloudy', 'Cloudy day'), ('golden', 'Golden hour'),
               ('evening', 'Evening, warm bulbs'), ('nightcool', 'Night, cool LEDs'), ('dark', 'Lights off')]
    pb = ''.join(f'<button type="button" data-preset="{k}" aria-pressed="{str(k == "afternoon").lower()}">{v}</button>' for k, v in presets)
    times = [('morning', 'Morning'), ('midday', 'Midday'), ('golden', 'Golden hour'), ('dusk', 'Dusk'), ('night', 'Night')]
    tb = ''.join(f'<button type="button" data-time="{k}" aria-pressed="{str(k == "midday").lower()}">{v}</button>' for k, v in times)
    return f'''<div class="s-desk">
    <div class="desk">
      <div class="desk-top">
        <h2 class="desk-h" id="{p}lightTitle">Change the light</h2>
        <div class="presets" role="group" aria-labelledby="{p}lightTitle">{pb}</div>
      </div>
      <div class="desk-col">
        <div class="group"><span class="sub" id="{p}timeLbl">Time of day</span><div class="seg5" role="group" aria-labelledby="{p}timeLbl">{tb}</div></div>
        <div class="group"><span class="sub" id="{p}skyLbl">Weather</span><div class="seg" role="group" aria-labelledby="{p}skyLbl"><button type="button" data-sky="sun" aria-pressed="true">{sun}Sunny</button><button type="button" data-sky="cloud" aria-pressed="false">{cloud}Cloudy</button></div></div>
      </div>
      <div class="desk-col">
        <div class="group">
          <button type="button" class="toggle viz-ceil-on" aria-pressed="false"><span class="viz-ceil-name">{esc(r["ceiling"])}</span><span class="sw" aria-hidden="true"></span></button>
          <label class="range"><span>Brightness <output class="viz-ceil-out">100%</output></span><input type="range" class="viz-ceil-dim" min="5" max="100" step="5" value="100" aria-label="{esc(r["ceiling"])} brightness"></label>
        </div>
        <div class="group">
          <button type="button" class="toggle viz-lamps-on" aria-pressed="false"><span class="viz-lamps-name">{esc(r["lamps"])}</span><span class="sw" aria-hidden="true"></span></button>
          <label class="range"><span>Brightness <output class="viz-lamps-out">100%</output></span><input type="range" class="viz-lamps-dim" min="5" max="100" step="5" value="100" aria-label="{esc(r["lamps"])} brightness"></label>
        </div>
      </div>
      <div class="desk-col">
        <label class="range kelvin"><span>Bulb color <output class="viz-k-out">3000K, soft white</output></span><input type="range" class="viz-k" min="2200" max="6500" step="100" value="3000" aria-label="Bulb color"><span class="kbar" aria-hidden="true"></span><span class="ends" aria-hidden="true"><i>Warm</i><i>Cool</i></span></label>
        <p class="desk-note">Bulb color changes every light that’s on. Warm bulbs bring out tans and browns; cool LEDs make grays and blues look crisper.</p>
      </div>
    </div>
  </div>'''


# ---------------------------------------------------------------- shell
def cta(est):
    return f'''<section class="cta" aria-labelledby="ctaTitle">
  <div class="wrap">
    <div>
      <h2 id="ctaTitle">Ready for a floor you’ll love?</h2>
      <p>Free, no-obligation estimates across the Minneapolis / Saint Paul area.</p>
    </div>
    <div class="btn-row"><a class="btn btn-dark" href="{est}">Get My Free Estimate</a><a class="btn btn-outline" href="{TEL}">Call {PHONE}</a></div>
  </div>
</section>'''


def header(page, est):
    cur = SECTION.get(page, page)

    def item(href, label):
        a = ''
        if href == page:
            a = ' aria-current="page"'
        elif href == cur:
            a = ' aria-current="true"'
        return f'<li><a href="{href}"{a}>{label}</a></li>'
    links = '\n        '.join(item(h, l) for h, l in NAV)
    return f'''<a class="skip" href="#main">Skip to main content</a>
<aside class="preview-note" aria-label="About this page">Concept preview by Aidan Barnard. Not the live website.</aside>
<header class="site">
  <div class="wrap hdr">
    <a class="logo" href="./"><img src="img/logo-300.webp" srcset="img/logo-150.webp 150w, img/logo-300.webp 300w, img/logo-450.webp 450w" sizes="147px" alt="The Coating Crew home" width="147" height="52"></a>
    <nav class="nav" aria-label="Main">
      <ul>
        {links}
      </ul>
    </nav>
    <div class="hdr-cta">
      <a class="phone" href="{TEL}" aria-label="Call {PHONE}">{I_PHONE}<span>{PHONE}</span></a>
      <a class="btn btn-primary" href="{est}">Get a Price</a>
      <button class="menu-btn" id="menuBtn" type="button" aria-expanded="false" aria-controls="mobileMenu">{I_MENU}<span class="menu-label">Menu</span></button>
    </div>
  </div>
  <nav class="mobile-menu" id="mobileMenu" aria-label="Menu" hidden>
    <div class="wrap">
      <ul>
        {links}
        <li><a href="contact-us.html"{' aria-current="page"' if page == 'contact-us.html' else ''}>Contact us</a></li>
        <li><a href="search.html" data-search-open>Search the site</a></li>
      </ul>
      <div class="btn-row"><a class="btn btn-primary" href="{est}">Get a Price</a><a class="btn btn-outline" href="{TEL}">Call {PHONE}</a></div>
    </div>
  </nav>
</header>'''


def footer(page, est):
    return f'''<footer>
  <div class="wrap fgrid">
    <div class="stack" style="gap:16px">
      <a class="logo-box" href="./"><img src="img/logo-300.webp" srcset="img/logo-150.webp 150w, img/logo-300.webp 300w, img/logo-450.webp 450w" sizes="136px" alt="The Coating Crew home" width="136" height="48" loading="lazy"></a>
      <p>Family owned and operated since 1999. BBB accredited and a member of the Builders Association of the Twin Cities.</p>
    </div>
    <div>
      <h2>Visit or call</h2>
      <p>10967 Clark Rd, Ste E<br>Inver Grove Heights, MN 55077</p>
      <p>Monday to Friday, 7am to 6pm</p>
      <p><a class="fphone" href="{TEL}">{PHONE}</a></p>
    </div>
    <nav aria-label="Floors">
      <h2>Floors</h2>
      <ul>
        <li><a href="residential.html">Residential</a></li>
        <li><a href="commercial.html">Commercial</a></li>
        <li><a href="industrial.html">Industrial</a></li>
        <li><a href="finishes.html">Finishes</a></li>
        <li><a href="colors.html">Colors and visualizer</a></li>
        <li><a href="gallery.html">Our work</a></li>
        <li><a href="reviews.html">Reviews</a></li>
      </ul>
    </nav>
    <nav aria-label="Company">
      <h2>Company</h2>
      <ul>
        <li><a href="about-us.html">About us</a></li>
        <li><a href="worry-free-guarantee.html">Worry-free guarantee</a></li>
        <li><a href="certified-professionals.html">Certified professionals</a></li>
        <li><a href="trailers.html">On-site storage</a></li>
        <li><a href="contact-us.html">Contact us</a></li>
        <li><a href="search.html" data-search-open>Search the site</a></li>
        <li><a href="privacy-policy.html">Privacy policy</a></li>
      </ul>
    </nav>
  </div>
  <div class="wrap"><div class="legal">
    <p>Concept design © 2026, shared with The Coating Crew for review only. Photos are from your current website. The floor visualizer rooms and sample blocks are 3D renders. See the <a href="owner.html">owner’s lead inbox</a>.</p>
    <p class="builtby">Built by <a href="https://saintpaulagency.com" target="_blank" rel="noopener">saintpaulagency.com</a> and <a href="https://www.aidanbarnard.com" target="_blank" rel="noopener">aidanbarnard.com</a></p>
  </div></div>
</footer>
<nav class="mbar" aria-label="Call or get a price">
  <div class="in"><a class="btn btn-dark" href="{TEL}">Call Now</a><a class="btn btn-primary" href="{est}">Get a Price</a></div>
</nav>'''


LIGHTBOX = '''<div class="lb" id="lb" role="dialog" aria-modal="true" aria-label="Photo viewer" hidden>
  <figure><img id="lbImg" src="data:," alt=""><figcaption id="lbCap"></figcaption></figure>
  <button type="button" class="x" id="lbX" aria-label="Close photo viewer">✕</button>
  <button type="button" class="pv" id="lbPv" aria-label="Previous photo">‹</button>
  <button type="button" class="nx" id="lbNx" aria-label="Next photo">›</button>
</div>'''


def strip_tags(s):
    return html.unescape(re.sub(r'<[^>]+>', '', s)).strip()


def ld(page, title, main):
    url = SITE + ('' if page == 'index.html' else page)
    graph = []
    if page in ('index.html', 'contact-us.html'):
        graph.append(BUSINESS)
    if page != 'index.html':
        name = strip_tags(re.search(r'<h1[^>]*>(.*?)</h1>', main, flags=re.S).group(1)) if '<h1' in main else title
        crumb = re.search(r'<p class="crumbs">.*?/\s*([^<]+)</p>', main)
        graph.append({'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': SITE},
            {'@type': 'ListItem', 'position': 2, 'name': crumb.group(1).strip() if crumb else name, 'item': url}]})
    qs = re.findall(r'<details[^>]*><summary>(.*?)</summary><p>(.*?)</p></details>', main, flags=re.S)
    if qs:
        graph.append({'@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': strip_tags(q), 'acceptedAnswer': {'@type': 'Answer', 'text': strip_tags(a)}} for q, a in qs]})
    if not graph:
        return ''
    data = {'@context': 'https://schema.org', '@graph': graph}
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/') + '</script>\n'


def head(page, title, desc, main):
    img = OG_IMG.get(page, 'img/photos/job-garage-5.jpg')
    t, d = esc(title), esc(desc)
    url = SITE + ('' if page == 'index.html' else page)
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{t}</title>
<meta name="description" content="{d}">
<meta name="robots" content="{ROBOTS}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="The Coating Crew">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:image" content="{SITE}{img}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#1D232A">
<link rel="icon" href="img/logo.webp">
<link rel="preload" href="fonts/archivo-wdth.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="site.css?v={CSS_V}">
{ld(page, title, main)}</head>
<body>'''


# ---------------------------------------------------------------- cleanup for pages kept from the old build
def clean(m, page):
    m = re.sub(r'\s*<div class="checker"[^>]*></div>', '', m)
    m = re.sub(r'<span class="gt">(.*?)</span>', r'\1', m, flags=re.S)

    def cls(mo):
        toks = [t for t in mo.group(1).split() if t not in ('rv', 'rv-l', 'rv-r', 'rv-z', 'pre')]
        return f' class="{" ".join(toks)}"' if toks else ''
    m = re.sub(r' class="([^"]*)"', cls, m)
    m = m.replace('btn btn-orange', 'btn btn-primary').replace('btn btn-ghost', 'btn btn-light').replace('btn btn-line', 'btn btn-outline')
    m = m.replace('<div style="display:flex;flex-wrap:wrap;gap:12px">', '<div class="btn-row">')
    m = m.replace(' style="background:var(--paper)"', '')
    m = m.replace('<section class="band" style="background:var(--concrete)">', '<section class="band alt">')
    m = re.sub(r'<a href="([^"]+)" style="font-weight:700;font-size:20px">', r'<a class="tlink" href="\1">', m)
    # v3: no label lines above headings, no arrows on links
    m = re.sub(r'\s*<p class="eyebrow">.*?</p>', '', m)
    m = re.sub(r' ?<span aria-hidden="true">→</span>', '', m)
    m = re.sub(r' ?→</a>', '</a>', m)
    m = m.replace('class="link-arrow"', 'class="tlink"')
    m = m.replace('./#studio', 'colors.html#visualizer').replace('./#inbox', 'owner.html')
    # page heroes: a real photo beside the headline instead of a dimmed background
    m = re.sub(r'<section class="phero"([^>]*)>\s*<div class="bg" style="background-image:url\(([^)]+)\)" aria-hidden="true"></div>\s*<div class="wrap">(.*?)</div>\s*</section>',
               lambda mo: f'<section class="phero"{mo.group(1)}>\n  <div class="wrap">\n    <div class="ptext">{mo.group(3).rstrip()}\n    </div>\n    <div class="pimg">{pic(mo.group(2), "", "(min-width:900px) 560px, 100vw", eager=True)}</div>\n  </div>\n</section>',
               m, flags=re.S)
    m = re.sub(r'(<div class="ptext">)\s*\n\s*\n', r'\1\n', m)
    m = re.sub(r'\n\s*\n(\s*<div class="btn-row">)', r'\n\1', m)
    # side photos and card photos as <img>
    m = re.sub(r'<div class="media( fit)?" role="img" aria-label="([^"]*)" style="background-image:url\(img/photos/system-quartz\.jpg\)"></div>',
               lambda mo: '<div class="media"><img src="img/systems/quartz-close-1200.webp" srcset="img/systems/quartz-close-640.webp 640w, img/systems/quartz-close-1200.webp 1200w" sizes="(min-width:900px) 600px, 100vw" alt="Sample block with a blue quartz finish, the system we recommend for pool decks" width="1200" height="900" loading="lazy" decoding="async"></div>', m)
    m = re.sub(r'<div class="media( fit)?" role="img" aria-label="([^"]*)" style="background-image:url\(([^)]+)\)"></div>',
               lambda mo: f'<div class="media{mo.group(1) or ""}">{pic(mo.group(3), mo.group(2))}</div>', m)
    m = re.sub(r'<div class="cimg" style="background-image:url\(([^)]+)\)"></div>',
               lambda mo: f'<div class="cimg">{pic(mo.group(1), "", "(min-width:960px) 600px, 100vw")}</div>', m)
    if page == 'contact-us.html' and '<legend style' in m:
        m = re.sub(r'<form class="est" id="contactForm" novalidate>.*?</form>', CONTACT_FORM, m, flags=re.S)
    if page == 'commercial.html' and 'industrial.html' not in m:
        m = m.replace('</div></div></section><section class="band alt">',
                      '</div><p class="lede">Running a warehouse, machine shop or food plant? <a class="tlink" href="industrial.html">See industrial floors</a></p></div></section><section class="band alt">', 1)
    if page == 'commercial.html' and 'id="spaces-title"' not in m:
        m = m.replace('<div class="cards2">', '<h2 class="h2" id="spaces-title">Commercial spaces we coat</h2>\n<div class="cards2">', 1)
    if page == 'gallery.html':
        m = re.sub(r'(aria-label|alt)="([^"]*?) · ([^"]*)"', r'\1="\2, \3"', m)

        def named(mo):
            label, vis = mo.group(2), mo.group(4)
            if vis.lower() not in label.lower():
                label = f'{vis}, {label[0].lower() + label[1:]}'
            return f'{mo.group(1)}aria-label="Open photo: {label}"{mo.group(3)}<span>{vis}</span></button>'
        m = re.sub(r'(<button type="button" class="gitem[^>]*?)aria-label="Open photo: ([^"]*)"(.*?)<span>([^<]*)</span></button>', named, m, flags=re.S)
        if 'id="reviews"' not in m:
            m = m.replace('{{CTA}}', REVIEWS + '\n{{CTA}}', 1)

    def sized(mo):
        tag = mo.group(0)
        if ' width=' in tag:
            return tag
        w, h = dims(mo.group(1))
        return tag.replace('<img ', f'<img width="{w}" height="{h}" ', 1)
    m = re.sub(r'<img src="(img/photos/t/[^"]+)"[^>]*>', sized, m)
    m = re.sub(r'<section class="cta".*?</section>', '{{CTA}}', m, flags=re.S)
    return m


CONTACT_FORM = '''<form class="est" id="contactForm" novalidate aria-labelledby="cfTitle">
  <h2 class="h3" id="cfTitle">Send us a message</h2>
  <div class="fields">
    <label><span>Name <span class="req">(required)</span></span><input type="text" id="c-name" autocomplete="name" required></label>
    <label><span>Phone <span class="req">(required)</span></span><input type="tel" id="c-phone" autocomplete="tel" inputmode="tel" required></label>
    <label class="full"><span>Email <span class="req">(optional)</span></span><input type="email" id="c-email" autocomplete="email"></label>
    <label class="full"><span>How can we help? <span class="req">(optional)</span></span><textarea id="c-msg" rows="4"></textarea></label>
  </div>
  <p class="err" id="cErr" role="alert" hidden></p>
  <button type="submit" class="btn btn-primary" style="align-self:flex-start">Send Message</button>
  <p id="cDone" class="ok" tabindex="-1" hidden>Thanks! The Coating Crew will be in touch soon. (Concept demo: nothing was sent.)</p>
</form>'''


def reviews_block():
    src = open(os.path.join(ROOT, 'reviews.html')).read()
    grid = re.search(r'<div class="rgrid">.*?</div>(?=<p class="note">)', src, flags=re.S)
    g = grid.group(0) if grid else ''
    g = re.sub(r' id="review-(\d)"', r' id="r-\1"', g)
    g = re.sub(r' class="review rv"', ' class="review"', g)
    return f'''<section class="band alt" id="reviews" aria-labelledby="revTitle">
  <div class="wrap stack" style="gap:40px">
    <h2 class="h2" id="revTitle">What our customers say</h2>
    {g}
  </div>
</section>'''


REVIEWS = ''


def build(path):
    page = os.path.basename(path)
    src = os.path.join(SRC, page)
    est = '#estimate' if page == 'index.html' else './#estimate'
    if os.path.exists(src):
        s = open(src).read()
        title = re.search(r'<!--title: (.*?)-->', s).group(1)
        desc = re.search(r'<!--desc: (.*?)-->', s).group(1)
        main = re.sub(r'<!--(title|desc): .*?-->\n?', '', s)
        show = '#showroom' if page == 'index.html' else 'colors.html'
        main = main.replace('{{COMPARE}}', open(os.path.join(SRC, '_compare.html')).read().replace('{show}', show))
        main = main.replace('{{VIZ_STAGE}}', viz_stage()).replace('{{VIZ_RAIL}}', viz_rail(est)).replace('{{VIZ_DESK}}', viz_desk())
        main = re.sub(r'\{\{PIC (\S+) "([^"]*)" "([^"]*)"( eager)?\}\}', lambda mo: pic(mo.group(1), mo.group(2), mo.group(3), bool(mo.group(4))), main)
    else:
        s = open(path).read()
        title = html.unescape(re.search(r'<title>(.*?)</title>', s, flags=re.S).group(1).strip())
        dm = re.search(r'<meta name="description" content="([^"]*)"', s)
        desc = html.unescape(dm.group(1)) if dm else ''
        a = s.index('<main'); a = s.index('>', a) + 1
        main = clean(s[a:s.index('</main>')], page).strip('\n')
    main = main.replace('{{CTA}}', cta(est))
    js = ['site.js'] + EXTRA_JS.get(page, []) + ([] if page in NO_SEARCH else ['search-index.js', 'search.js'])
    out = [head(page, title, desc, main), header(page, est), f'<main id="main" tabindex="-1">\n{main.strip()}\n</main>', footer(page, est)]
    if 'class="gitem' in main:
        out.append(LIGHTBOX)
    out.append('<div class="toast" id="toast" role="status" aria-live="polite"><b id="toastTitle"></b><span id="toastBody"></span></div>')
    out.append('\n'.join(f'<script src="{j}" defer></script>' for j in js))
    out.append('</body>\n</html>\n')
    open(path, 'w').write('\n'.join(out))
    return page


if __name__ == '__main__':
    REVIEWS = reviews_block()
    for p in sorted(glob.glob(os.path.join(SRC, '*.html'))):
        name = os.path.basename(p)
        if not name.startswith('_') and not os.path.exists(os.path.join(ROOT, name)):
            open(os.path.join(ROOT, name), 'w').write('<main></main>')
    pages = sorted(p for p in glob.glob(os.path.join(ROOT, '*.html')) if not os.path.basename(p).startswith('test-'))
    for p in pages:
        print('built', build(p))
