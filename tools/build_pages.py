"""Wrap every page of the concept site in the same head, header, footer and scripts.

Run from the repo root:  python3 tools/build_pages.py
Pages with a source in tools/pages/ (home, colors, finishes, owner) are built from it; every other page keeps its
own <main> content, which is cleaned up to the current design (real <img> tags with WebP sizes instead of CSS
backgrounds, no label lines above headings, no arrows on links). Safe to run again.
"""
import glob
import hashlib
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
# ad landing pages: one job (the estimate), so no site menu to wander off into
LANDING = {'garage-floor-coating.html', 'basement-floor-coating.html'}
EXTRA_JS.update({p: ['home.js'] for p in LANDING})

I_PHONE = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round"><path d="M5 3h4l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 5a2 2 0 0 1 2-2z"/></svg>'
I_MENU = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg>'
I_SEARCH = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5L21 21"/></svg>'
I_PLAY = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor"><path d="M7 4.5v15l13-7.5z"/></svg>'
I_SPLIT = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M12 2v20"/></svg>'
I_ARROWS = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M9 7l-5 5 5 5M15 7l5 5-5 5"/></svg>'
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


def ver(f):
    """Content hash for cache busting: a file's URL changes whenever the file does."""
    return hashlib.md5(open(os.path.join(ROOT, f), 'rb').read()).hexdigest()[:8]


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


def pic(src, alt='', sizes='(min-width:900px) 600px, calc(100vw - 32px)', eager=False):
    """An <img> with WebP sizes (640, 960, 1200) for any photo from img/photos/."""
    m = re.match(r'img/photos/(?:t/)?([\w-]+)\.jpg$', src)
    if m and os.path.exists(os.path.join(ROOT, f'img/w/{m.group(1)}-1200.webp')):
        n = m.group(1)
        b = f'img/w/{n}-1200.webp'
        sset = ', '.join(f'img/w/{n}-{w}.webp {w}w' for w in (640, 960, 1200) if os.path.exists(os.path.join(ROOT, f'img/w/{n}-{w}.webp')))
        w, h = dims(b)
        load = ' fetchpriority="high"' if eager else ' loading="lazy"'
        return f'<img src="{b}" srcset="{sset}" sizes="{sizes}" alt="{esc(alt)}" width="{w}" height="{h}" decoding="async"{load}>'
    w, h = dims(src)
    load = ' fetchpriority="high"' if eager else ' loading="lazy"'
    return f'<img src="{src}" alt="{esc(alt)}" width="{w}" height="{h}" decoding="async"{load}>'


# ---------------------------------------------------------------- real jobs and outside ratings
# Photos, city tags and post links come from The Coating Crew's own Facebook page (tools/photos/fb.py).
FB = json.load(open(os.path.join(ROOT, 'tools', 'photos', 'fb.json')))
EXT = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M14 4h6v6M20 4l-9 9M18 13v6a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h6"/></svg>'


def fb_url(fbid):
    return 'https://www.facebook.com/photo/?fbid=' + fbid


def post_link(fbid, what):
    return (f'<a class="post-link" href="{fb_url(fbid)}" target="_blank" rel="noopener" data-fb-post>See the Facebook post'
            f'<span class="sr-only"> of {esc(what)} (opens in a new tab)</span>{EXT}</a>')


def job(slug, sizes='(min-width:700px) 600px, 84vw'):
    """A real job from the crew's Facebook page: the photo opens up close, the caption links to the post."""
    j = FB['shots'][slug]
    what = (j['kind'][0].lower() + j['kind'][1:] if j['kind'] != 'Our Jeep' else 'our Jeep') + (f' in {j["city"]}' if j['city'] else '')
    head_ = f'<b>{esc(j["city"])}</b> {esc(j["kind"])}' if j['city'] else f'<b>{esc(j["kind"])}</b>'
    return (f'<figure class="job"><button type="button" class="gitem shot" aria-label="Open photo: {esc(j["kind"])}{", " + esc(j["city"]) if j["city"] else ""}" data-post="{fb_url(j["fbid"])}">'
            f'{pic(f"img/photos/fb-{slug}.jpg", j["alt"], sizes)}</button>'
            f'<figcaption><span class="j-what">{head_}</span>{post_link(j["fbid"], "the " + what)}</figcaption></figure>')


def pair(slug):
    """A before and after pair, shown side by side as the crew posted it."""
    p = FB['pairs'][slug]
    where = f'{p["kind"].lower()} in {p["city"]}' if p['city'] else p['kind'].lower()
    def one(state):
        b = f'img/ba/{slug}-{state}'
        return (f'<button type="button" class="gitem" aria-label="Open photo: {esc(p["kind"])}{", " + esc(p["city"]) if p["city"] else ""}, {state}" data-post="{fb_url(p["fbid"])}">'
                f'<img src="{b}-960.webp" srcset="{b}-480.webp 480w, {b}-960.webp 960w" sizes="(min-width:1000px) 230px, 45vw" alt="The {esc(where)}, {state} coating" '
                f'width="{p["w"]}" height="{p["h"]}" loading="lazy" decoding="async"><span>{state.capitalize()}</span></button>')
    head_ = f'<b>{esc(p["city"])}</b> {esc(p["kind"])}' if p['city'] else f'<b>{esc(p["kind"])}</b>'
    return (f'<figure class="pair"><div class="pair-pics">{one("before")}{one("after")}</div>'
            f'<figcaption><span class="j-what">{head_}</span>{post_link(p["fbid"], "the " + where)}</figcaption></figure>')


def compare(slug):
    """Two photos taken from nearly the same spot, lined up so a visitor can drag between them."""
    p = FB['pairs'][slug]
    where = f'{p["kind"].lower()} in {p["city"]}'
    def im(state, cls, alt):
        b = f'img/ba/{slug}-{state}'
        return (f'<img class="{cls}" src="{b}-1200.webp" srcset="{b}-640.webp 640w, {b}-960.webp 960w, {b}-1200.webp 1200w" sizes="(min-width:1000px) 660px, calc(100vw - 32px)" '
                f'alt="{esc(alt)}" width="{p["w"]}" height="{p["h"]}" loading="lazy" decoding="async">')
    return (f'<figure class="cmp" style="--pos:50%"><div class="cmp-view">'
            + im('after', 'cmp-a', f'The {where} after coating, with a gray chip floor')
            + im('before', 'cmp-b', f'The same garage before coating, with stained bare concrete')
            + '<span class="cmp-tag b" aria-hidden="true">Before</span><span class="cmp-tag a" aria-hidden="true">After</span>'
            '<span class="cmp-bar" aria-hidden="true"><i><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6l-5 6 5 6M15 6l5 6-5 6"/></svg></i></span>'
            f'<input class="cmp-range" type="range" min="0" max="100" value="50" step="1" aria-label="Slide between the before and after photo of the {esc(where)}">'
            f'</div><figcaption><span class="j-what"><b>{esc(p["city"])}</b> {esc(p["kind"])}. Drag to compare.</span>{post_link(p["fbid"], "the " + where)}</figcaption></figure>')


# Outside ratings, worded and numbered as each site showed them on RATED. Each one links to its source.
RATED = 'November 24, 2026'
RATINGS = [
    ('4.9', 'Google', '251 reviews', 'https://www.google.com/maps?cid=15792623999213110421', True),
    ('A+', 'BBB rating', 'Accredited since 2014', 'https://www.bbb.org/us/mn/inver-grove-heights/profile/epoxy-floor-coating/the-coating-crew-0704-96506371', False),
    ('4.9', 'Angi', '35 reviews', 'https://www.angi.com/companylist/us/mn/hastings/the-coating-crew-reviews-1.htm', True),
    ('4.9', 'HomeAdvisor', '37 reviews', 'https://www.homeadvisor.com/rated.TheCoatingCrew.52880804.html', True),
]
STAR = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor"><path d="M12 2l2.9 6.2 6.6.7-5 4.5 1.4 6.6L12 16.8 6.1 20l1.4-6.6-5-4.5 6.6-.7z"/></svg>'


def proof():
    li = ''.join(
        f'<li><a href="{u}" target="_blank" rel="noopener" data-rating="{esc(site)}"><b>{val}{STAR if star else ""}</b>'
        f'<span><strong>{esc(site)}</strong>{esc(note)}<span class="sr-only">{", " + val + " out of 5" if star else ""} (opens in a new tab)</span></span></a></li>'
        for val, site, note, u, star in RATINGS)
    return ('<section class="proofbar" aria-label="Ratings and reviews">\n  <div class="wrap">\n    <ul class="ratings">' + li +
            '</ul>\n'
            f'    <p class="ratings-note">Ratings as each site showed them on {RATED}. Choose one to read the reviews there.</p>\n  </div>\n</section>')


# ---------------------------------------------------------------- visualizer pieces
def _js_list(name, js):
    return re.findall(r"'([^']+)'", re.search(name + r": \[(.*?)\]", js).group(1))


VIZ_JS = open(os.path.join(ROOT, 'visualizer.js')).read()
GROUPS = [('gray', 'Grays and blues'), ('warm', 'Warm grays and stone'), ('tan', 'Tans and browns')]
ROOMS = json.load(open(os.path.join(ROOT, 'img', 'studio', 'rooms.json')))


def slug(n):
    return n.lower().replace(' ', '-')


def viz_stage(open_desk=False, p='v-'):
    """The live room, the control bar under it (room, time of day, lights) and the full lighting drawer."""
    r = ROOMS[0]
    rooms = '\n'.join(
        f'        <button type="button" class="room" data-i="{i}" aria-pressed="{str(i == 0).lower()}"><img src="img/studio/{x["key"]}-thumb.webp" alt="" width="105" height="70" decoding="async"><span>{esc(x["name"])}</span></button>'
        for i, x in enumerate(ROOMS))
    label = f'{r["name"]} with bare concrete, showroom lights'
    sun = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="12" cy="12" r="4.5"/><path d="M12 1.5v2.5M12 20v2.5M4.6 4.6l1.8 1.8M17.6 17.6l1.8 1.8M1.5 12H4M20 12h2.5M4.6 19.4l1.8-1.8M17.6 6.4l1.8-1.8"/></svg>'
    cloud = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round"><path d="M7 18h10a4 4 0 0 0 .6-7.95A6 6 0 0 0 6.1 9.2 4.5 4.5 0 0 0 7 18z"/></svg>'
    chev = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg>'
    presets = [('showroom', 'Showroom lights'), ('morning', 'Sunny morning'), ('afternoon', 'Bright afternoon'), ('cloudy', 'Cloudy day'), ('golden', 'Golden hour'),
               ('evening', 'Evening, warm bulbs'), ('nightcool', 'Night, cool LEDs'), ('dark', 'Lights off')]
    pb = ''.join(f'<button type="button" data-preset="{k}" aria-pressed="{str(k == "showroom").lower()}">{v}</button>' for k, v in presets)
    bulbs = ''.join(f'<button type="button" data-bulbs="{k}" aria-pressed="{str(k == "cool").lower()}">{v}</button>' for k, v in (('off', 'Off'), ('warm', 'Warm'), ('cool', 'Cool')))
    hid = '' if open_desk else ' hidden'
    return f'''<div class="s-viz">
    <div class="viz-stage">
      <img class="viz-photo" src="img/studio/garage-bare-1320.webp" srcset="img/studio/garage-bare-660.webp 660w, img/studio/garage-bare-990.webp 990w, img/studio/garage-bare-1320.webp 1320w" sizes="(min-width:1340px) 700px, (min-width:1001px) 56vw, calc(100vw - 32px)" alt="{label}" width="1320" height="880" fetchpriority="high">
      <canvas role="img" aria-hidden="true" aria-label="{label}"></canvas>
      <span class="viz-tag" aria-hidden="true"><b class="viz-tag-blend">Bare concrete</b><span class="viz-tag-light">Showroom lights</span></span>
      <span class="loader" aria-hidden="true">Loading the room…</span>
      <button type="button" class="viz-compare" aria-pressed="false">{I_SPLIT}Before and after</button>
      <div class="ba" hidden>
        <input type="range" class="ba-range" min="0" max="100" step="1" value="50" aria-label="Before and after: compare bare concrete with the coating">
        <span class="ba-line" aria-hidden="true"><span class="ba-grip">{I_ARROWS}</span></span>
        <span class="ba-lab ba-l" aria-hidden="true">Before</span><span class="ba-lab ba-r" aria-hidden="true">After</span>
      </div>
    </div>
    <div class="cbar">
      <div class="viz-rooms" role="group" aria-label="Choose a room">
{rooms}
      </div>
      <div class="cbar-row">
        <label class="tod"><span>Time of day <output class="viz-time-out">Midday</output></span><input type="range" class="viz-time" min="0" max="4" step="1" value="1" aria-label="Time of day" aria-valuetext="Midday"><span class="tod-ticks" aria-hidden="true"><i>Morning</i><i>Midday</i><i>Golden</i><i>Dusk</i><i>Night</i></span></label>
        <div class="group"><span class="sub" id="{p}bulbLbl">Indoor lights</span><div class="seg seg3" role="group" aria-labelledby="{p}bulbLbl">{bulbs}</div></div>
        <button type="button" class="viz-day" aria-pressed="false">{I_PLAY}<span>Play a full day</span></button>
        <button type="button" class="more-btn" aria-expanded="{str(open_desk).lower()}" aria-controls="{p}desk">More lighting{chev}</button>
      </div>
    </div>
    <div class="desk" id="{p}desk"{hid}>
      <div class="group wide"><span class="sub" id="{p}presetLbl">Quick looks</span><div class="presets" role="group" aria-labelledby="{p}presetLbl">{pb}</div></div>
      <div class="group"><span class="sub" id="{p}skyLbl">Weather</span><div class="seg" role="group" aria-labelledby="{p}skyLbl"><button type="button" data-sky="sun" aria-pressed="true">{sun}Sunny</button><button type="button" data-sky="cloud" aria-pressed="false">{cloud}Cloudy</button></div></div>
      <label class="range kelvin"><span>Bulb color <output class="viz-k-out">5000K, cool daylight</output></span><input type="range" class="viz-k" min="2200" max="6500" step="100" value="5000" aria-label="Bulb color"><span class="kbar" aria-hidden="true"></span><span class="ends" aria-hidden="true"><i>Warm</i><i>Cool</i></span></label>
      <div class="group">
        <button type="button" class="toggle viz-ceil-on" aria-pressed="true"><span class="viz-ceil-name">{esc(r["ceiling"])}</span><span class="sw" aria-hidden="true"></span></button>
        <label class="range"><span>Brightness <output class="viz-ceil-out">100%</output></span><input type="range" class="viz-ceil-dim" min="5" max="100" step="5" value="100" aria-label="{esc(r["ceiling"])} brightness"></label>
      </div>
      <div class="group">
        <button type="button" class="toggle viz-lamps-on" aria-pressed="true"><span class="viz-lamps-name">{esc(r["lamps"])}</span><span class="sw" aria-hidden="true"></span></button>
        <label class="range"><span>Brightness <output class="viz-lamps-out">100%</output></span><input type="range" class="viz-lamps-dim" min="5" max="100" step="5" value="100" aria-label="{esc(r["lamps"])} brightness"></label>
      </div>
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
      <a class="btn btn-primary" href="{est}" data-price-floor>Price this floor</a>
      <div class="rail-btns"><button type="button" data-rail="prev" aria-label="Scroll the samples back">{I_LEFT}</button><button type="button" data-rail="next" aria-label="Scroll to more samples">{I_RIGHT}</button></div>
    </div>
    <p class="viz-nogl note" hidden>Your browser is showing still pictures, so the floor stays Domino here. The swatch above shows the blend you picked.</p>
    <div class="rail">
      {"".join(groups)}
    </div>
  </div>'''


# ---------------------------------------------------------------- shell
def cta(est):
    return f'''<section class="night" aria-labelledby="ctaTitle">
  <img src="img/studio/garage-night-1320.webp" srcset="img/studio/garage-night-660.webp 660w, img/studio/garage-night-990.webp 990w, img/studio/garage-night-1320.webp 1320w" sizes="100vw" alt="" width="1320" height="880" loading="lazy" decoding="async">
  <div class="wrap">
    <h2 class="display" id="ctaTitle">Ready for a floor you’ll love?</h2>
    <p>Free, no-obligation estimates across the Minneapolis / Saint Paul area.</p>
    <div class="btn-row"><a class="btn btn-primary" href="{est}">Get My Free Estimate</a><a class="btn btn-light" href="{TEL}">Call {PHONE}</a></div>
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
    if page in LANDING:
        return f'''<a class="skip" href="#main">Skip to main content</a>
<aside class="preview-note" aria-label="About this page">Concept preview by Aidan Barnard. Not the live website.</aside>
<header class="site">
  <div class="wrap hdr">
    <a class="logo" href="./"><img src="img/logo-300.webp" srcset="img/logo-150.webp 150w, img/logo-300.webp 300w, img/logo-450.webp 450w" sizes="147px" alt="The Coating Crew home" width="147" height="52"></a>
    <div class="hdr-cta">
      <a class="phone" href="{TEL}" aria-label="Call {PHONE}">{I_PHONE}<span>{PHONE}</span></a>
      <a class="btn btn-primary" href="#estimate">Get a Price</a>
    </div>
  </div>
</header>'''
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
      <a class="srch-btn" href="search.html" data-search-open aria-label="Search the site">{I_SEARCH}<span>Search</span><kbd aria-hidden="true">/</kbd></a>
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
    <p>Concept design © 2026, shared with The Coating Crew for review only. All wording and photos come from your current website. The garage, basement and sunroom pictures and the sample blocks are 3D renders, not photos of your jobs. See the <a href="owner.html">owner’s lead inbox</a>.</p>
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


# Blocks pop into place the first time they are seen. The class goes on before the first paint so nothing
# flashes; if site.js never arrives, the class comes off again and everything simply shows.
POP_JS = ("(function(d){try{if('IntersectionObserver' in window&&!matchMedia('(prefers-reduced-motion: reduce)').matches)"
          "{d.classList.add('pop-on');setTimeout(function(){if(!window.ccPop)d.classList.remove('pop-on')},4000)}}catch(e){}})(document.documentElement)")

# the next page starts loading when a visitor hovers a link; pages with the 3D room are only fetched,
# so their opening animation plays when the visitor actually arrives
SPEC = json.dumps({
    'prerender': [{'where': {'and': [{'selector_matches': "a[href$='.html']"},
                                     {'not': {'selector_matches': "a[href^='colors.html'], a[href='index.html'], a[target], a[href='owner.html']"}}]},
                   'eagerness': 'moderate'}],
    'prefetch': [{'where': {'selector_matches': "a[href='./'], a[href^='./#'], a[href^='colors.html']"}, 'eagerness': 'moderate'}],
}, separators=(',', ':'))


def strip_tags(s):
    return html.unescape(re.sub(r'<[^>]+>', '', s)).strip()


def ld(page, title, main):
    url = SITE + ('' if page == 'index.html' else page)
    graph = []
    if page in ('index.html', 'contact-us.html'):
        graph.append(BUSINESS)
    if page != 'index.html':
        name = strip_tags(re.search(r'<h1[^>]*>(.*?)</h1>', main, flags=re.S).group(1)) if '<h1' in main else title
        crumb = re.search(r'<p class="crumbs">.*?</a>\s*/\s*([^<]+)</p>', main)
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
    card = f'img/og/{page[:-5]}.jpg'
    og = card if os.path.exists(os.path.join(ROOT, card)) else img
    t, d = esc(title), esc(desc)
    # the not-found page can be served at any depth, so its links resolve from the site root
    base = '\n<base href="/coatingcrew-concept/">' if page == '404.html' else ''
    url = SITE + ('' if page == 'index.html' else page)
    html_cls = ' class="logo-in-hero"' if page == 'index.html' else ''
    return f'''<!doctype html>
<html lang="en"{html_cls}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">{base}
<title>{t}</title>
<meta name="description" content="{d}">
<meta name="robots" content="{ROBOTS}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="The Coating Crew">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:image" content="{SITE}{og}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{t}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{SITE}{og}">
<meta name="theme-color" content="#1D232A">
<link rel="icon" href="img/favicon-48.png" sizes="48x48" type="image/png">
<link rel="apple-touch-icon" href="img/apple-touch-icon.png">
<link rel="preload" href="fonts/archivo-wdth.woff2" as="font" type="font/woff2" crossorigin>
<script>{POP_JS}</script>
<link rel="stylesheet" href="site.css?v={ver('site.css')}">
<script type="speculationrules">{SPEC}</script>
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
               lambda mo: f'<section class="phero"{mo.group(1)}>\n  <div class="wrap">\n    <div class="ptext">{mo.group(3).rstrip()}\n    </div>\n    <div class="pimg">{pic(mo.group(2), "", "(min-width:900px) 560px, calc(100vw - 32px)", eager=True)}</div>\n  </div>\n</section>',
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

    def thumb(mo):
        tag = mo.group(0)
        alt = re.search(r'alt="([^"]*)"', tag)
        full = re.search(r'data-full="([^"]*)"', tag)
        big = 'class="gitem big"' in m[max(0, mo.start() - 200):mo.start()]
        new = pic(mo.group(1), html.unescape(alt.group(1)) if alt else '', '(min-width:900px) 50vw, 100vw' if big else '(min-width:900px) 25vw, 50vw')
        return new.replace('<img ', f'<img data-full="{full.group(1)}" ', 1) if full else new
    m = re.sub(r'<img (?:width="\d+" height="\d+" )?src="(img/photos/t/[^"]+)"[^>]*>', thumb, m)
    # photos placed by an earlier build: add the 960 size and phone-accurate sizes
    m = re.sub(r'srcset="img/w/([\w-]+)-640\.webp 640w, img/w/\1-1200\.webp 1200w"',
               lambda mo: f'srcset="img/w/{mo.group(1)}-640.webp 640w, img/w/{mo.group(1)}-960.webp 960w, img/w/{mo.group(1)}-1200.webp 1200w"', m)
    m = m.replace('sizes="(min-width:900px) 560px, 100vw"', 'sizes="(min-width:900px) 560px, calc(100vw - 32px)"')
    m = m.replace('sizes="(min-width:900px) 600px, 100vw"', 'sizes="(min-width:900px) 600px, calc(100vw - 32px)"')
    # the photo viewer opens the color-corrected WebP
    m = re.sub(r'data-full="img/photos/([\w-]+)\.jpg"', lambda mo: f'data-full="img/w/{mo.group(1)}-1200.webp"' if os.path.exists(os.path.join(ROOT, f'img/w/{mo.group(1)}-1200.webp')) else mo.group(0), m)
    m = re.sub(r'<section class="(?:cta|night)".*?</section>', '{{CTA}}', m, flags=re.S)
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
    est = '#estimate' if page == 'index.html' or page in LANDING else './#estimate'
    if os.path.exists(src):
        s = open(src).read()
        title = re.search(r'<!--title: (.*?)-->', s).group(1)
        desc = re.search(r'<!--desc: (.*?)-->', s).group(1)
        main = re.sub(r'<!--(title|desc): .*?-->\n?', '', s)
        show = '#showroom' if page == 'index.html' else 'colors.html'
        main = main.replace('{{COMPARE}}', open(os.path.join(SRC, '_compare.html')).read().replace('{show}', show))
        main = main.replace('{{VIZ_STAGE}}', viz_stage(open_desk=page == 'colors.html')).replace('{{VIZ_RAIL}}', viz_rail(est))
        main = main.replace('{{EST_FORM}}', open(os.path.join(SRC, '_estimate_form.html')).read().rstrip())
        main = main.replace('{{LOGO}}', open(os.path.join(SRC, '_logo.svg')).read().strip())
        main = re.sub(r'\{\{PIC (\S+) "([^"]*)" "([^"]*)"( eager)?\}\}', lambda mo: pic(mo.group(1), mo.group(2), mo.group(3), bool(mo.group(4))), main)
        main = re.sub(r'\{\{JOB ([\w-]+)\}\}', lambda mo: job(mo.group(1)), main)
        main = re.sub(r'\{\{PAIR ([\w-]+)\}\}', lambda mo: pair(mo.group(1)), main)
        main = re.sub(r'\{\{SLIDE ([\w-]+)\}\}', lambda mo: compare(mo.group(1)), main)
        main = re.sub(r'\{\{POST ([\w-]+) "([^"]*)"\}\}', lambda mo: post_link(FB['shots'][mo.group(1)]['fbid'], mo.group(2)), main)
        main = main.replace('{{PROOF}}', proof())
    else:
        s = open(path).read()
        title = html.unescape(re.search(r'<title>(.*?)</title>', s, flags=re.S).group(1).strip())
        dm = re.search(r'<meta name="description" content="([^"]*)"', s)
        desc = html.unescape(dm.group(1)) if dm else ''
        a = s.index('<main'); a = s.index('>', a) + 1
        main = clean(s[a:s.index('</main>')], page).strip('\n')
    main = main.replace('{{CTA}}', cta(est))
    js = ['track.js', 'site.js'] + EXTRA_JS.get(page, []) + ([] if page in NO_SEARCH or page in LANDING else ['search-index.js', 'search.js'])
    out = [head(page, title, desc, main), header(page, est), f'<main id="main" tabindex="-1">\n{main.strip()}\n</main>', footer(page, est)]
    if 'class="gitem' in main:
        out.append(LIGHTBOX)
    out.append('<div class="toast" id="toast" role="status" aria-live="polite"><b id="toastTitle"></b><span id="toastBody"></span></div>')
    out.append('\n'.join(f'<script src="{j}?v={ver(j)}" defer></script>' for j in js))
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
    # sitemap for launch; robots.txt keeps crawlers out until CC_INDEX=1
    public = [os.path.basename(p) for p in pages if os.path.basename(p) not in ('404.html', 'owner.html', 'search.html') and os.path.basename(p) not in LANDING]
    urls = ''.join(f'  <url><loc>{SITE}{"" if n == "index.html" else n}</loc></url>\n' for n in sorted(public, key=lambda n: n != 'index.html'))
    open(os.path.join(ROOT, 'sitemap.xml'), 'w').write(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n')
    open(os.path.join(ROOT, 'robots.txt'), 'w').write(f'User-agent: *\nAllow: /\nSitemap: {SITE}sitemap.xml\n' if os.environ.get('CC_INDEX') else 'User-agent: *\nDisallow: /\n')
