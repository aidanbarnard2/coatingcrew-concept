/* The Coating Crew concept site: shared behavior for every page. */
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  document.documentElement.classList.add('js');
  var motionOK = !(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);

  /* header shadow once the page scrolls */
  var header = $('header.site'), ticking = false;
  function onScroll() { if (ticking) return; ticking = true; requestAnimationFrame(function () { ticking = false; if (header) header.classList.toggle('scrolled', (scrollY || 0) > 20); }); }
  addEventListener('scroll', onScroll, { passive: true }); onScroll();

  /* mobile menu: a disclosure button; Escape closes it and returns focus to the button */
  var menuBtn = $('#menuBtn'), menu = $('#mobileMenu');
  function setMenu(open, focusBack) {
    if (!menu) return;
    menu.hidden = !open; menuBtn.setAttribute('aria-expanded', String(open));
    var lab = $('.menu-label', menuBtn); if (lab) lab.textContent = open ? 'Close' : 'Menu';
    if (!open && focusBack) menuBtn.focus();
  }
  if (menuBtn && menu) {
    menuBtn.addEventListener('click', function () { setMenu(menu.hidden); if (!menu.hidden) { var f = $('a', menu); if (f) f.focus(); } });
    menu.addEventListener('click', function (e) { if (e.target.closest('a,button[data-search-open]')) setMenu(false); });
    addEventListener('keydown', function (e) { if (e.key === 'Escape' && !menu.hidden) setMenu(false, true); });
    addEventListener('resize', function () { if (innerWidth > 1080 && !menu.hidden) setMenu(false); });
  }

  /* on the home page the big logo leads; the header logo appears once it scrolls away */
  var heroLogo = $('#ccLogo'), rootEl = document.documentElement;
  if (heroLogo && 'IntersectionObserver' in window) {
    new IntersectionObserver(function (es) { rootEl.classList.toggle('logo-in-hero', es[0].isIntersecting); }, { rootMargin: '-80px 0px 0px 0px' }).observe(heroLogo);
  } else rootEl.classList.remove('logo-in-hero');

  /* hero logo: the checkered flags wave as the page opens, settle within a few seconds, and wave again on hover or tap */
  var logo = $('#ccLogo');
  if (logo && motionOK) (function () {
    var flags = $$('.cc-cloth', logo).map(function (g) {
      var top = g.dataset.top.split(',').map(Number), bot = g.dataset.bottom.split(',').map(Number), side = +g.dataset.side;
      var dx = bot[0] - top[0], dy = bot[1] - top[1], len = Math.hypot(dx, dy), d = [dx / len, dy / len];
      var o = side < 0 ? [-d[1], d[0]] : [d[1], -d[0]];
      o = [o[0] * 0.985 + d[0] * 0.174, o[1] * 0.985 + d[1] * 0.174];
      return { cells: $$('polygon', g), edge: $('.cc-edge', g), A: [top[0] + d[0] * 10, top[1] + d[1] * 10], d: d, o: o, t0: +(g.dataset.t || 0) };
    });
    var NU = 6, NV = 7, L = 300, W = 260;
    function draw(f, t) {
      var P = [], i, j;
      for (i = 0; i <= NU; i++) { P[i] = []; for (j = 0; j <= NV; j++) {
        var u = i / NU, v = j / NV, a = 6.2832 * (1.15 * v - t * 0.55) + 0.9 * u;
        var al = u * L + 24 * v * Math.sin(a), aw = v * W - 12 * v * (1 - Math.cos(a));
        P[i][j] = [f.A[0] + f.d[0] * al + f.o[0] * aw, f.A[1] + f.d[1] * al + f.o[1] * aw];
      } }
      var k = 0, fmt = function (q) { return q[0].toFixed(1) + ',' + q[1].toFixed(1); };
      for (i = 0; i < NU; i++) for (j = 0; j < NV; j++) {
        f.cells[k++].setAttribute('points', [P[i][j], P[i + 1][j], P[i + 1][j + 1], P[i][j + 1]].map(fmt).join(' '));
      }
      var e = [P[0][0]];
      for (j = 1; j <= NV; j++) e.push(P[0][j]);
      for (i = 1; i <= NU; i++) e.push(P[i][NV]);
      for (j = NV - 1; j >= 0; j--) e.push(P[NU][j]);
      f.edge.setAttribute('d', 'M' + e.map(function (q) { return q[0].toFixed(1) + ' ' + q[1].toFixed(1); }).join(' L'));
    }
    var t = 0, speed = 0, until = 0, last = 0, running = false;
    function frame(now) {
      var dt = Math.min(0.05, (now - last) / 1000); last = now;
      var target = now < until ? 1 : 0;
      speed += (target - speed) * (target ? 0.08 : 0.045);
      t += dt * speed;
      flags.forEach(function (f) { draw(f, t + f.t0); });
      if (target || speed > 0.01) requestAnimationFrame(frame); else running = false;
    }
    function wave(ms) {
      until = performance.now() + ms;
      if (!running) { running = true; last = performance.now(); requestAnimationFrame(frame); }
    }
    wave(2600);  // with the ease-out, the flags are still within about four seconds
    logo.addEventListener('pointerenter', function () { wave(1800); });
    logo.addEventListener('click', function () { wave(2200); });
  })();

  /* the picked floor follows you down the page, until the estimate form is in view */
  var follow = $('#follow'), studio = $('.studio');
  if (follow && studio && 'IntersectionObserver' in window) {
    var past = false, atEst = false, est = $('#estimate');
    var place = function () {
      var on = past && !atEst;
      if (on) { follow.hidden = false; requestAnimationFrame(function () { follow.classList.add('show'); }); }
      else { follow.classList.remove('show'); setTimeout(function () { if (!follow.classList.contains('show')) follow.hidden = true; }, 350); }
    };
    new IntersectionObserver(function (es) { past = !es[0].isIntersecting && es[0].boundingClientRect.top < 0; place(); }).observe(studio);
    if (est) new IntersectionObserver(function (es) { atEst = es[0].isIntersecting; place(); }, { rootMargin: '0px 0px -30% 0px' }).observe(est);
  }

  /* numbers count up once when they come into view */
  var counts = $$('[data-count]');
  if (counts.length && motionOK && 'IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        io.unobserve(e.target);
        var el = e.target, to = +el.dataset.count, t0 = performance.now();
        (function tick(now) {
          var p = Math.min(1, (now - t0) / 1100), v = Math.round(to * (1 - Math.pow(1 - p, 3)));
          el.textContent = v; if (p < 1) requestAnimationFrame(tick);
        })(t0);
      });
    }, { threshold: 0.6 });
    counts.forEach(function (el) { el.textContent = '0'; io.observe(el); });
  }

  /* photo strips: grab and fling with a mouse (touch screens already swipe) */
  $$('.reel').forEach(function (reel) {
    reel.classList.add('grab');
    var down = false, moved = false, x0 = 0, s0 = 0, vx = 0, lx = 0, lt = 0, raf = 0;
    reel.addEventListener('pointerdown', function (e) {
      if (e.pointerType !== 'mouse' || e.button !== 0) return;
      cancelAnimationFrame(raf); down = true; moved = false; x0 = lx = e.clientX; s0 = reel.scrollLeft; lt = performance.now(); vx = 0;
    });
    window.addEventListener('pointermove', function (e) {
      if (!down) return;
      var dx = e.clientX - x0;
      if (!moved && Math.abs(dx) > 6) { moved = true; reel.classList.add('dragging'); }
      if (!moved) return;
      reel.scrollLeft = s0 - dx;
      var now = performance.now(); vx = (e.clientX - lx) / Math.max(1, now - lt); lx = e.clientX; lt = now;
    });
    window.addEventListener('pointerup', function () {
      if (!down) return; down = false;
      if (!moved) return;
      var v = -vx * 12;
      (function glide() {
        if (motionOK && Math.abs(v) > 0.5) { reel.scrollLeft += v; v *= 0.92; raf = requestAnimationFrame(glide); }
        else reel.classList.remove('dragging');
      })();
    });
    reel.addEventListener('click', function (e) { if (moved) { e.preventDefault(); e.stopPropagation(); moved = false; } }, true);
  });

  /* toast, shared */
  var toast = $('#toast'), toastTimer;
  window.ccToast = function (title, body) {
    if (!toast) return;
    $('#toastTitle').textContent = title; $('#toastBody').textContent = body || '';
    toast.classList.add('show'); clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toast.classList.remove('show'); }, 6000);
  };

  /* gallery filter + photo viewer (a modal dialog that keeps focus inside while open) */
  var items = $$('.gitem'), lb = $('#lb');
  if (items.length && lb) {
    var img = $('#lbImg'), cap = $('#lbCap'), cur = 0, list = items, last = null;
    $$('.fbtn').forEach(function (b) {
      b.addEventListener('click', function () {
        $$('.fbtn').forEach(function (x) { x.setAttribute('aria-pressed', String(x === b)); });
        var f = b.dataset.f, n = 0;
        items.forEach(function (it) { it.hidden = !(f === 'all' || it.dataset.cat === f); if (!it.hidden) n++; });
        var st = $('#galleryStatus'); if (st) st.textContent = 'Showing ' + n + ' photo' + (n === 1 ? '' : 's') + '.';
      });
    });
    function show(i) {
      cur = (i + list.length) % list.length;
      var it = list[cur], im = $('img', it);
      img.src = im.dataset.full || im.src; img.alt = im.alt;
      cap.textContent = it.getAttribute('aria-label').replace('Open photo: ', '') + ', photo ' + (cur + 1) + ' of ' + list.length;
    }
    function open(it) { last = it; list = items.filter(function (x) { return !x.hidden; }); show(list.indexOf(it)); lb.hidden = false; document.body.style.overflow = 'hidden'; $('#lbX').focus(); }
    function close() { lb.hidden = true; document.body.style.overflow = ''; if (last) last.focus(); }
    items.forEach(function (it) { it.addEventListener('click', function () { open(it); }); });
    $('#lbX').addEventListener('click', close);
    $('#lbPv').addEventListener('click', function () { show(cur - 1); });
    $('#lbNx').addEventListener('click', function () { show(cur + 1); });
    lb.addEventListener('click', function (e) { if (e.target === lb) close(); });
    lb.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { e.preventDefault(); close(); }
      else if (e.key === 'ArrowLeft') show(cur - 1);
      else if (e.key === 'ArrowRight') show(cur + 1);
      else if (e.key === 'Tab') {
        var f = $$('button', lb), first = f[0], lastB = f[f.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); lastB.focus(); }
        else if (!e.shiftKey && document.activeElement === lastB) { e.preventDefault(); first.focus(); }
      }
    });
    var sx = null;
    lb.addEventListener('pointerdown', function (e) { sx = e.clientX; });
    lb.addEventListener('pointerup', function (e) { if (sx === null) return; var dx = e.clientX - sx; sx = null; if (Math.abs(dx) > 50) show(cur + (dx < 0 ? 1 : -1)); });
    function openFromHash() { if (location.hash.indexOf('#p-') !== 0) return; var it = document.getElementById(location.hash.slice(1)); if (it && it.classList.contains('gitem')) { it.scrollIntoView({ block: 'center' }); open(it); } }
    openFromHash(); addEventListener('hashchange', openFromHash);
  }

  /* contact form (concept: checks the fields, sends nothing) */
  var cf = $('#contactForm');
  if (cf) cf.addEventListener('submit', function (e) {
    e.preventDefault();
    var err = $('#cErr'), name = $('#c-name'), phone = $('#c-phone');
    [name, phone].forEach(function (el) { el.removeAttribute('aria-invalid'); el.removeAttribute('aria-describedby'); });
    function fail(el, msg) { err.textContent = msg; err.hidden = false; el.setAttribute('aria-invalid', 'true'); el.setAttribute('aria-describedby', 'cErr'); el.focus(); }
    if (!name.value.trim()) return fail(name, 'Add your name so we know who to ask for.');
    if (phone.value.replace(/\D/g, '').length < 10) return fail(phone, 'Enter a 10-digit phone number, like 651 555 0123.');
    err.hidden = true; $('#cDone').hidden = false; $('#cDone').focus(); cf.reset();
  });

  /* "Price this floor" carries the sample, room and light picked in the visualizer to the estimate form */
  document.addEventListener('click', function (e) {
    var a = e.target.closest('[data-price-floor]'); if (!a) return;
    var v = a.closest('[data-viz]'), viz = v && v._viz;
    if (viz) { viz.touched = true; viz.emit(); }
    try { var name = v && $('.viz-blend-name', v); if (name) { sessionStorage.setItem('ccBlend', name.textContent); sessionStorage.setItem('ccBlendPicked', '1'); } } catch (x) {}
  });

  /* photo reels: the arrow buttons scroll the reel in the same section */
  $$('[data-reel]').forEach(function (b) {
    b.addEventListener('click', function () {
      var sec = b.closest('section'), reel = sec && $('.reel', sec); if (!reel) return;
      var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
      reel.scrollBy({ left: (b.dataset.reel === 'next' ? 1 : -1) * reel.clientWidth * 0.8, behavior: reduce ? 'auto' : 'smooth' });
    });
  });
})();
