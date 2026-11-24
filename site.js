/* The Coating Crew concept site: shared behavior for every page. */
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  document.documentElement.classList.add('js');

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
