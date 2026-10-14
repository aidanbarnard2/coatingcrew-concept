(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  document.documentElement.classList.add('js');
  function frame() { return new Promise(function (r) { requestAnimationFrame(function () { r(); }); }); }
  function rng(seed) { var a = seed >>> 0; return function () { a = (a + 0x6D2B79F5) | 0; var t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  function hashStr(s) { var h = 2166136261; for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
  function parsePal(str) {
    var out = str.split(' ').map(function (t) { var p = t.split(':'), h = p[0]; return { c: [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)], w: +p[1] }; });
    var tot = out.reduce(function (s, o) { return s + o.w; }, 0), acc = 0;
    out.forEach(function (o) { o.c = o.c.map(function (v) { return Math.max(0, Math.min(255, 120 + (v - 120) * 1.35)); }); acc += o.w / tot; o.cum = acc; });
    return out;
  }  /* Seamless chip texture: thousands of irregular flakes in the blend's own colors */
  function flakeCanvas(size, palStr, opt) {
    opt = opt || {};
    var rMin = opt.rMin || 2, rMax = opt.rMax || 5.5, coverage = opt.coverage || 2.7, seed = opt.seed || 7, chunk = opt.chunk || 0;
    var pal = parsePal(palStr), cv = document.createElement('canvas'); cv.width = cv.height = size;
    var ctx = cv.getContext('2d'), base = [0, 0, 0];
    pal.forEach(function (o) { var w = o.w / pal.reduce(function (s, q) { return s + q.w; }, 0); base[0] += o.c[0] * w; base[1] += o.c[1] * w; base[2] += o.c[2] * w; });
    ctx.fillStyle = 'rgb(' + (base[0] | 0) + ',' + (base[1] | 0) + ',' + (base[2] | 0) + ')'; ctx.fillRect(0, 0, size, size);
    var avg = (rMin + rMax) / 2, n = Math.round(coverage * size * size / (Math.PI * avg * avg * 0.55)), R = rng(seed);
    var pts = new Float32Array(16);
    function draw(x, y, k) { ctx.beginPath(); ctx.moveTo(x + pts[0], y + pts[1]); for (var v = 1; v < k; v++) ctx.lineTo(x + pts[v * 2], y + pts[v * 2 + 1]); ctx.closePath(); ctx.fill(); }
    var i = 0;
    function batch(limit) {
      for (; i < limit; i++) {
        var x = R() * size, y = R() * size, r = rMin + R() * (rMax - rMin), u = R(), k = 0;
        while (k < pal.length - 1 && u > pal[k].cum) k++;
        var c = pal[k].c, j = (R() - 0.5) * 20;
        ctx.fillStyle = 'rgb(' + ((c[0] + j) | 0) + ',' + ((c[1] + j) | 0) + ',' + ((c[2] + j) | 0) + ')';
        var verts = 4 + ((R() * 4) | 0), a0 = R() * 6.2832, sq = 0.6 + 0.4 * R();
        for (var v = 0; v < verts; v++) { var a = a0 + v * 6.2832 / verts + (R() - 0.5) * 0.7, rr = r * (0.45 + 0.55 * R()); pts[v * 2] = rr * Math.cos(a); pts[v * 2 + 1] = rr * Math.sin(a) * sq; }
        draw(x, y, verts);
        var ex = x < rMax ? size : (x > size - rMax ? -size : 0), ey = y < rMax ? size : (y > size - rMax ? -size : 0);
        if (ex) draw(x + ex, y, verts); if (ey) draw(x, y + ey, verts); if (ex && ey) draw(x + ex, y + ey, verts);
      }
    }
    if (!chunk) { batch(n); return Promise.resolve(cv); }
    return (async function () { while (i < n) { batch(Math.min(n, i + chunk)); await frame(); } return cv; })();
  }
  var BLENDS = [
    ['Armadillo','6a6358:10 807a6e:20 938c7f:27 a39c8f:24 b5aea1:14 ccc6ba:6'],
    ['Basalt','656a6e:13 777b80:29 84898d:27 92969b:21 a3a7ab:9 bfc3c7:2'],
    ['Buckskin','594f41:9 847a6a:13 a39a89:18 bcb2a0:27 d1c7b6:25 e7e1d6:8'],
    ['Chestnut','31261c:7 61422e:26 775c46:25 90765d:21 aa9275:16 d0bca1:6'],
    ['Claystone','585349:5 716a5e:14 837d71:21 979185:26 afa99d:22 d1ccc1:12'],
    ['Denim','383d41:9 596881:16 78869b:20 9ba3ae:22 b9c0c5:22 dfe3e4:11'],
    ['Dolphin','35332d:7 6e6b62:11 918e83:26 a6a396:36 bab5a5:17 d5d3cc:3'],
    ['Domino','23231f:8 43433f:10 646560:14 878681:23 a6a6a1:29 c9c9c5:16'],
    ['Driftwood','4e4639:4 8f8168:16 a69a82:28 b8ad96:24 c8bda7:19 dad1bb:9'],
    ['Garnet','625649:6 716456:16 7c6e5f:25 867868:26 928373:20 a39483:7'],
    ['Gunflint','292620:11 433e35:15 5e574a:18 7b7262:22 9b907b:21 c4baa6:13'],
    ['Husky','575550:7 77756d:18 8a877f:28 9a978e:27 aeaba2:14 d1cec5:5'],
    ['Lanai Grey','50504f:6 666664:17 757574:25 838482:26 939391:19 a9a9a7:8'],
    ['Leopard','27241f:5 4b4339:8 6b5f4f:21 827766:28 9e9481:31 bebab1:7'],
    ['North Oaks','6b6a62:13 87867f:19 9d9c96:27 afaea9:22 c2c2bd:13 dddeda:5'],
    ['Oasis','6d675b:8 857f72:18 968f83:30 a59e91:32 bbb4a5:9 d9d4c7:3'],
    ['Obsidian','696256:4 7e7567:13 8c8374:23 988f7f:28 a59b8a:23 b5ac9c:10'],
    ['Pebble Beach','5f5242:5 817663:16 968c7a:29 a59c8b:29 b8b0a2:13 d3cdc2:8'],
    ['Pecan','50463a:3 92795f:18 a69277:24 b7a78b:24 c6b89d:20 d4c7ae:11'],
    ['Pumice','6f685e:5 898278:14 9b9489:24 a9a197:26 b6afa5:21 c6c0b5:9'],
    ['Sandstone','493c2d:13 846e53:29 a48c6d:28 bda98a:18 cfbfa4:9 ded9d1:3'],
    ['Schist','828280:10 999997:19 aaaaa9:22 b8b8b7:21 c6c6c5:18 d7d7d6:10'],
    ['Shale','5b564b:6 787267:21 8a8478:28 9b9488:24 aea89b:15 ccc6b9:6'],
    ['Silver Creek','4c4943:14 656259:23 7b786f:22 928f86:20 aca89f:15 cdcbc4:5'],
    ['Slate','3f382d:8 635b4d:22 7d7566:26 968d7d:26 b1a998:14 dbd3c4:3'],
    ['Slate Stone','626665:11 838581:16 9d9e99:24 b2b3af:23 c7c8c5:17 dedfdc:9'],
    ['Smoke','373835:8 6c6c69:21 82837f:31 999a95:21 b4b5b1:12 d4d4d1:7'],
    ['Tamarack','292521:11 57544f:22 7d786e:20 9e9a91:18 b9b6ad:17 d9d8d1:12'],
    ['Thistle','494238:6 7e7262:7 a2927c:22 b4a793:25 c4baaa:24 d5cec1:15'],
    ['Tidal Wave','444644:11 64625b:18 817c73:18 9d988c:21 bab3a5:20 d9d2c4:13'],
    ['Turquoise','5c594e:8 716d63:20 827e73:25 959186:24 aca89d:16 cdc9bd:8'],
    ['Wombat Blue','282927:7 585957:13 44618b:3 777976:43 989996:21 c6c7c4:13']
  ];
  /* header + progress */
  var header = $('header.site'), progress = $('#progress'), ticking = false;
  function onScroll() { if (ticking) return; ticking = true; requestAnimationFrame(function () { ticking = false; var y = scrollY || 0, max = document.documentElement.scrollHeight - innerHeight; if (header) header.classList.toggle('scrolled', y > 30); if (progress) progress.style.transform = 'scaleX(' + (max > 0 ? Math.min(1, y / max) : 0) + ')'; }); }
  addEventListener('scroll', onScroll, { passive: true }); onScroll();
  /* mobile menu */
  var menuBtn = $('#menuBtn'), menu = $('#mobileMenu');
  if (menuBtn && menu) menuBtn.addEventListener('click', function () { var open = menu.hidden; menu.hidden = !open; menuBtn.setAttribute('aria-expanded', String(open)); });
  /* reveals: content stays readable, it only slides into place */
  if ('IntersectionObserver' in window && !reduce) {
    var io = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { var el = e.target; el.classList.remove('pre'); io.unobserve(el); setTimeout(function () { el.classList.remove('rv'); }, 1000); } }); }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    $$('.rv').forEach(function (el) { if (el.getBoundingClientRect().top > innerHeight * 0.92) { el.classList.add('pre'); io.observe(el); } });
  }
  /* gallery filter + lightbox */
  var items = $$('.gitem'), lb = $('#lb');
  if (items.length && lb) {
    var img = $('#lbImg'), cap = $('#lbCap'), cur = 0, list = items, last = null;
    $$('.fbtn').forEach(function (b) { b.addEventListener('click', function () { $$('.fbtn').forEach(function (x) { x.setAttribute('aria-pressed', String(x === b)); }); var f = b.dataset.f; items.forEach(function (it) { it.hidden = !(f === 'all' || it.dataset.cat === f); }); }); });
    function show(i) { cur = (i + list.length) % list.length; var it = list[cur], im = it.querySelector('img'); img.src = im.src; img.alt = im.alt; cap.textContent = it.getAttribute('aria-label').replace('Open photo: ', '') + '  ·  ' + (cur + 1) + ' of ' + list.length; }
    function open(it) { last = it; list = items.filter(function (x) { return !x.hidden; }); show(list.indexOf(it)); lb.hidden = false; document.body.style.overflow = 'hidden'; $('#lbX').focus(); }
    function close() { lb.hidden = true; document.body.style.overflow = ''; if (last) last.focus(); }
    items.forEach(function (it) { it.addEventListener('click', function () { open(it); }); });
    $('#lbX').addEventListener('click', close); $('#lbPv').addEventListener('click', function () { show(cur - 1); }); $('#lbNx').addEventListener('click', function () { show(cur + 1); });
    lb.addEventListener('click', function (e) { if (e.target === lb) close(); });
    function openFromHash() { if (location.hash.indexOf('#p-') !== 0) return; var it = document.getElementById(location.hash.slice(1)); if (it && it.classList.contains('gitem')) { it.scrollIntoView({ block: 'center' }); open(it); } }
    openFromHash(); addEventListener('hashchange', openFromHash);
    addEventListener('keydown', function (e) { if (lb.hidden) return; if (e.key === 'Escape') close(); if (e.key === 'ArrowLeft') show(cur - 1); if (e.key === 'ArrowRight') show(cur + 1); });
  }
  /* colors page: the real swatch photos; tapping one opens it in the 3D studio */
  var grid = $('#swgrid');
  if (grid) {
    BLENDS.forEach(function (b) {
      var slug = b[0].toLowerCase().replace(/ /g, '-');
      var a = document.createElement('a'); a.className = 'swc'; a.href = './#studio'; a.id = 'color-' + slug;
      a.setAttribute('aria-label', b[0] + ': try it in the 3D studio');
      var ico = document.createElement('i'); ico.style.backgroundImage = 'url(img/colors/' + slug + '.jpg)';
      a.appendChild(ico); a.appendChild(document.createTextNode(b[0])); grid.appendChild(a);
      a.addEventListener('click', function () { try { sessionStorage.setItem('ccBlend', b[0]); } catch (e) {} });
    });
    if (location.hash.indexOf('#color-') === 0) { var t = document.getElementById(location.hash.slice(1)); if (t) setTimeout(function () { t.scrollIntoView({ block: 'center' }); t.focus({ preventScroll: true }); }, 60); }
  }
  /* contact form (concept: validates, sends nothing) */
  var cf = $('#contactForm');
  if (cf) cf.addEventListener('submit', function (e) {
    e.preventDefault(); var err = $('#cErr'), n = $('#c-name').value.trim(), ph = $('#c-phone').value.replace(/\D/g, '');
    if (!n) { err.textContent = 'Add your name so we know who to ask for.'; err.hidden = false; return; }
    if (ph.length < 10) { err.textContent = 'Enter a 10-digit phone number, like 651 555 0123.'; err.hidden = false; return; }
    err.hidden = true; $('#cDone').hidden = false; cf.reset();
  });
})();
