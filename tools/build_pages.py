"""Wrap every page of the concept site in the same header, footer and scripts.

Run from the repo root:  python3 tools/build_pages.py
Pages with a source in tools/pages/ (home, colors) are built from it; every other page keeps its own
<main> content, which is cleaned up (no gradient text spans, no reveal classes, solid buttons).
Safe to run again: it only rewrites the shell around <main>.
"""
import glob
import html
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'tools', 'pages')
SITE = 'https://aidanbarnard2.github.io/coatingcrew-concept/'
PHONE, TEL = '(651) 263-8557', 'tel:+16512638557'

NAV = [('residential.html', 'Residential'), ('commercial.html', 'Commercial'),
       ('colors.html', 'Colors &amp; Visualizer'), ('gallery.html', 'Our Work'), ('about-us.html', 'About')]
SECTION = {'industrial.html': 'commercial.html', 'reviews.html': 'gallery.html', 'finishes.html': 'colors.html',
           'certified-professionals.html': 'about-us.html', 'worry-free-guarantee.html': 'about-us.html',
           'trailers.html': 'about-us.html'}
EXTRA_JS = {'index.html': ['visualizer.js', 'home.js'], 'colors.html': ['visualizer.js']}
OG_IMG = {'index.html': 'img/photos/job-garage-5.jpg', 'colors.html': 'img/viz/garage-day.jpg'}

I_PHONE = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round"><path d="M5 3h4l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 5a2 2 0 0 1 2-2z"/></svg>'
I_MENU = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg>'


def cta(est):
    return f'''<section class="cta" aria-labelledby="ctaTitle">
  <div class="wrap">
    <div class="stack" style="gap:8px">
      <h2 id="ctaTitle">Ready for a floor you’ll love?</h2>
      <p>Free, no-obligation estimates across the Minneapolis / Saint Paul area.</p>
    </div>
    <div class="btn-row"><a class="btn btn-dark" href="{est}">Get My Price</a><a class="btn btn-outline" href="{TEL}">Call {PHONE}</a></div>
  </div>
</section>'''


def header(page, est):
    cur = SECTION.get(page, page)
    def item(href, label, cls=''):
        a = ''
        if href == page:
            a = ' aria-current="page"'
        elif href == cur:
            a = ' aria-current="true"'
        return f'<li><a href="{href}"{a}>{label}</a></li>'
    links = '\n        '.join(item(h, l) for h, l in NAV)
    return f'''<a class="skip" href="#main">Skip to main content</a>
<p class="preview-note">Concept preview by Aidan Barnard · Not the live website</p>
<header class="site">
  <div class="wrap hdr">
    <a class="logo" href="./"><img src="img/logo.webp" alt="The Coating Crew home" width="147" height="52"></a>
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
    <div class="stack" style="gap:14px">
      <a class="logo-box" href="./"><img src="img/logo.webp" alt="The Coating Crew home" width="130" height="46"></a>
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
        <li><a href="./#inbox">Lead inbox (owner view)</a></li>
      </ul>
    </nav>
  </div>
  <div class="wrap legal">
    <p>Concept design © 2026, shared with The Coating Crew for review only. Photos are from your current website; the floor visualizer re-coats those same job photos.</p>
    <p class="builtby">Built by <a href="https://saintpaulagency.com" target="_blank" rel="noopener">saintpaulagency.com</a> and <a href="https://www.aidanbarnard.com" target="_blank" rel="noopener">aidanbarnard.com</a></p>
  </div>
</footer>
<div class="mbar">
  <div class="in"><a class="btn btn-dark" href="{TEL}">Call Now</a><a class="btn btn-primary" href="{est}">Get a Price</a></div>
</div>'''


LIGHTBOX = '''<div class="lb" id="lb" role="dialog" aria-modal="true" aria-label="Photo viewer" hidden>
  <figure><img id="lbImg" src="data:," alt=""><figcaption id="lbCap"></figcaption></figure>
  <button type="button" class="x" id="lbX" aria-label="Close photo viewer">✕</button>
  <button type="button" class="pv" id="lbPv" aria-label="Previous photo">‹</button>
  <button type="button" class="nx" id="lbNx" aria-label="Next photo">›</button>
</div>'''


def head(page, title, desc):
    img = OG_IMG.get(page, 'img/photos/job-garage-5.jpg')
    t, d = html.escape(title, quote=True), html.escape(desc, quote=True)
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{t}</title>
<meta name="description" content="{d}">
<meta name="robots" content="noindex, nofollow">
<meta property="og:type" content="website">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:image" content="{SITE}{img}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#14171C">
<link rel="icon" href="img/logo.webp">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap">
<link rel="stylesheet" href="site.css?v=3">
</head>
<body>'''


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
    m = re.sub(r'<a href="([^"]+)" style="font-weight:700;font-size:20px">', r'<a class="link-arrow" href="\1">', m)
    m = re.sub(r' ?→</a>', ' <span aria-hidden="true">→</span></a>', m)
    m = m.replace('./#studio', 'colors.html#visualizer')
    m = re.sub(r'<section class="cta".*?</section>', '{{CTA}}', m, flags=re.S)
    if page == 'contact-us.html' and '<legend style' in m:
        m = re.sub(r'<form class="est" id="contactForm" novalidate>.*?</form>', CONTACT_FORM, m, flags=re.S)
    if page == 'commercial.html' and 'industrial.html' not in m:
        m = m.replace('</div></div></section><section class="band alt">',
                      '</div><p class="lede">Running a warehouse, machine shop or food plant? <a class="link-arrow" href="industrial.html">See industrial floors <span aria-hidden="true">→</span></a></p></div></section><section class="band alt">', 1)
    if page == 'gallery.html' and 'id="reviews"' not in m:
        m = m.replace('/ Gallery</p>', '/ Our work</p>').replace('<h1 id="pageTitle">Real floors by our crew</h1>', '<h1 id="pageTitle">Our work</h1>')
        m = m.replace('<p class="intro">Every photo from our current website', '<p class="intro">Real floors by our crew and what our customers say. Every photo from our current website')
        m = m.replace('<div class="gallery" id="gallery">', '<p class="sr-only" id="galleryStatus" role="status"></p>\n<div class="gallery" id="gallery">')
        m = m.replace('{{CTA}}', REVIEWS + '\n{{CTA}}', 1)
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
  <div class="wrap stack" style="gap:36px">
    <div class="stack" style="gap:12px"><p class="eyebrow">Reviews</p><h2 class="h2" id="revTitle">What our customers say</h2></div>
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
        if '{{VISUALIZER}}' in main:
            viz = open(os.path.join(SRC, '_visualizer.html')).read().replace('{p}', 'v-').replace('{est}', est)
            main = main.replace('{{VISUALIZER}}', viz)
    else:
        s = open(path).read()
        title = html.unescape(re.search(r'<title>(.*?)</title>', s, flags=re.S).group(1).strip())
        dm = re.search(r'<meta name="description" content="([^"]*)"', s)
        desc = html.unescape(dm.group(1)) if dm else ''
        a = s.index('<main'); a = s.index('>', a) + 1
        main = clean(s[a:s.index('</main>')], page).strip('\n')
    main = main.replace('{{CTA}}', cta(est))
    js = ['site.js'] + EXTRA_JS.get(page, []) + ['search-index.js', 'search.js']
    out = [head(page, title, desc), header(page, est), f'<main id="main" tabindex="-1">\n{main.strip()}\n</main>', footer(page, est)]
    if 'class="gitem' in main:
        out.append(LIGHTBOX)
    out.append('<div class="toast" id="toast" role="status" aria-live="polite"><b id="toastTitle"></b><span id="toastBody"></span></div>')
    out.append('\n'.join(f'<script src="{j}" defer></script>' for j in js))
    out.append('</body>\n</html>\n')
    open(path, 'w').write('\n'.join(out))
    return page


if __name__ == '__main__':
    REVIEWS = reviews_block()
    pages = sorted(p for p in glob.glob(os.path.join(ROOT, '*.html')) if not os.path.basename(p).startswith('test-'))
    for p in pages:
        print('built', build(p))
