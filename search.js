/* The Coating Crew site search: instant, typo-tolerant results grouped by type, with quick answers. */
(function () {
  'use strict';
  var IDX = window.CC_INDEX;
  if (!IDX) return;
  var PHONE = '(651) 263-8557', TEL = 'tel:+16512638557';
  var MAPS = 'https://www.google.com/maps/search/?api=1&query=10967+Clark+Rd+Ste+E+Inver+Grove+Heights+MN+55077';

  /* ---------- text helpers ---------- */
  function norm(s) { return String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[’'`]/g, '').replace(/&/g, ' and ').replace(/[^a-z0-9$]+/g, ' ').trim(); }
  function stem(w) {
    if (w.length > 4 && /ies$/.test(w)) return w.slice(0, -3) + 'y';
    if (w.length > 4 && /(sh|ch|x|ss|z)es$/.test(w)) return w.slice(0, -2);
    if (w.length > 3 && /s$/.test(w) && !/(ss|us|is)$/.test(w)) return w.slice(0, -1);
    return w;
  }
  function toks(s) { var n = norm(s); return n ? n.split(' ').map(stem) : []; }
  function escHtml(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function escRe(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }
  var STOP = new Set('a an the of for to my do does did you your i is in on and or at it be are can could with we our me what whats how get got need want would like should will any some this that there their them from by as if so just much its im much'.split(' '));
  var SYN = {
    price: ['cost', 'estimate', 'quote', 'offer'], cost: ['price', 'estimate', 'quote', 'offer'], quote: ['estimate', 'price'], estimate: ['quote', 'price'], pricing: ['price', 'cost'],
    cheap: ['price', 'affordable'], affordable: ['price'], warranty: ['guarantee', 'lifetime'], guarantee: ['warranty'], gray: ['grey'], grey: ['gray'], colour: ['color'],
    flake: ['chip'], chip: ['flake'], swatch: ['color', 'blend'], storage: ['container', 'trailer'], pod: ['storage', 'container'], trailer: ['storage', 'container'],
    container: ['storage'], stuff: ['belonging', 'storage'], dealership: ['showroom'], car: ['garage', 'showroom'], restaurant: ['kitchen'], kennel: ['vet'], veterinary: ['vet'],
    dog: ['vet', 'kennel'], pet: ['vet', 'kennel'], gym: ['locker'], school: ['locker'], hospital: ['medical'], clinic: ['medical', 'vet'], bathroom: ['restroom'], spa: ['salon'],
    plant: ['factory', 'manufacturing'], manufacturing: ['factory'], brewery: ['food', 'production'], outdoor: ['patio', 'exterior', 'pool'], outside: ['patio', 'exterior'],
    exterior: ['patio', 'outdoor'], deck: ['patio', 'pool'], porch: ['patio'], fast: ['day', 'quick'], quick: ['day', 'fast'], time: ['day', 'hour'], dry: ['hour', 'ready'],
    cure: ['hour', 'ready'], phone: ['call', 'contact'], call: ['phone', 'contact'], email: ['contact', 'message'], address: ['contact', 'visit'], direction: ['map', 'visit'],
    install: ['installation', 'installer'], installer: ['installation', 'certified'], photo: ['gallery', 'picture'], picture: ['gallery', 'photo'], pic: ['gallery', 'photo'],
    slippery: ['slip'], nonslip: ['slip'], polyaspartic: ['polyurea'], winter: ['year', 'round'], review: ['testimonial'], testimonial: ['review'], rating: ['review'],
    basement: ['lower'], residential: ['home'], home: ['residential', 'house'], house: ['home', 'residential'], business: ['commercial'], commercial: ['business'], industrial: ['factory', 'warehouse']
  };
  var COLOR_WORDS = new Set(['color', 'colour', 'blend', 'chip', 'flake', 'swatch', 'sample', 'option']);

  /* ---------- index ---------- */
  var DOCS, COLORS, VOC, VOCAB, built = false;
  function build() {
    if (built) return; built = true;
    VOC = new Map();
    function post(tok, key, w) { var m = VOC.get(tok); if (!m) VOC.set(tok, m = new Map()); if ((m.get(key) || 0) < w) m.set(key, w); }
    DOCS = IDX.docs.map(function (d, i) { return { d: d, i: i, h: toks(d.h), c: toks(d.c), k: toks(d.k), x: toks(d.x), hn: norm(d.h), xn: norm(d.x) }; });
    COLORS = IDX.colors.map(function (c, j) { return { d: c, key: 'c' + j, h: toks(c.n), k: toks(c.k), hn: norm(c.n) }; });
    DOCS.forEach(function (o) { o.h.forEach(function (t) { post(t, o.i, 6); }); o.k.forEach(function (t) { post(t, o.i, 3.5); }); o.c.forEach(function (t) { post(t, o.i, 2); }); o.x.forEach(function (t) { post(t, o.i, 1); }); });
    COLORS.forEach(function (o) { o.h.forEach(function (t) { post(t, o.key, 6); }); o.k.forEach(function (t) { post(t, o.key, 3); }); });
    VOCAB = Array.from(VOC.keys());
  }
  function dist(a, b, max) {
    if (Math.abs(a.length - b.length) > max) return max + 1;
    var prev2 = [], prev = [], cur, i, j;
    for (j = 0; j <= b.length; j++) prev[j] = j;
    for (i = 1; i <= a.length; i++) {
      cur = [i]; var best = i;
      for (j = 1; j <= b.length; j++) {
        var v = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
        if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) v = Math.min(v, prev2[j - 2] + 1);
        cur[j] = v; if (v < best) best = v;
      }
      if (best > max) return max + 1;
      prev2 = prev; prev = cur;
    }
    return prev[b.length];
  }
  var mcache = new Map();
  function matchTerm(t) {
    if (mcache.has(t)) return mcache.get(t);
    var out = [], max = t.length >= 5 ? 2 : (t.length >= 4 ? 1 : 0);
    for (var n = 0; n < VOCAB.length; n++) {
      var v = VOCAB[n], s = 0, kind = 'f';
      if (v === t) { s = 1; kind = 'e'; }
      else if (t.length >= 2 && v.indexOf(t) === 0) { s = 0.55 + 0.4 * t.length / v.length; kind = 'p'; }
      else if (max && v.length >= 3) {
        var d = dist(t, v, max);
        if (d <= max) s = d === 1 ? 0.62 : 0.45;
        else if (t.length >= 5 && v.length > t.length && dist(t, v.slice(0, t.length), 1) <= 1) s = 0.42;
      }
      if (s) out.push([v, s, kind]);
    }
    mcache.set(t, out); return out;
  }

  /* ---------- quick answers ---------- */
  var ANSWERS = [
    { re: /\b(price|prices|pricing|cost|costs|how much|quote|quotes|estimate|estimates|affordable|cheap|expensive|budget|offer|deal|special)\b|\$/, big: 'Two-stall garage floor for only $2,495*', p: '*Offer based on 400 square feet of new concrete and no repair treatments needed. Additional costs may include steps, stemwalls, joint fill, travel and more. Every estimate is free.', acts: [['Get my free estimate', './#estimate', 1], ['Call ' + PHONE, TEL]] },
    { re: /\b(how long|long does|long will|takes?|one day|1 day|same day|fast|quick|turnaround|dry|drying|cure|curing|ready|24 hours?|walk on|drive on)\b/, big: 'Ready in as little as one day', p: 'In as little as one day, we can get your epoxy or polyurea floor coating installed and ready for full use. Most surfaces are ready for use within 24 hours.', acts: [['How it works', './#how', 1], ['Get my free estimate', './#estimate']] },
    { re: /\b(warrant\w*|guarant\w*|lifetime|peel\w*|coverage)\b/, big: 'Lifetime guarantee and a 15-year product warranty', p: 'Available on many of our products. Installation workmanship is covered for two years, and some products carry longer installation warranties.', acts: [['Worry-free guarantee', 'worry-free-guarantee.html', 1], ['Installation warranty', 'certified-professionals.html']] },
    { re: /\b(storage|store my|my stuff|stuff|belongings|containers?|pods?|trailers?|dart|move my)\b/, big: 'On-site storage while we work', p: 'Store your belongings in an on-site storage container from our partner Dart Portable Storage, Inc., protected from the weather. Storage is available for a drop-off and pick-up fee.', acts: [['On-site storage', 'trailers.html', 1], ['Get my free estimate', './#estimate']] },
    { re: /\b(winter|cold|snow|year round|seasons?|freez\w*)\b/, big: 'Yes, we install year-round', p: 'In as little as one day, your floor is installed and ready for full use. Most surfaces are ready within 24 hours.', acts: [['Get my free estimate', './#estimate', 1]] },
    { re: /\b(hours|open|opening|closed|closing|saturday|sunday|weekends?|weekdays?|monday|friday)\b/, big: 'Open Monday – Friday, 7am – 6pm', p: 'Closed Saturday and Sunday. Call ' + PHONE + ' or send a message any time.', acts: [['Call ' + PHONE, TEL, 1], ['Contact us', 'contact-us.html']] },
    { re: /\b(phone|call|number|contact|talk|reach|email|text me|message)\b/, big: PHONE, p: 'Call Monday – Friday, 7am – 6pm, or send a message and we will be in touch.', acts: [['Call now', TEL, 1], ['Send a message', 'contact-us.html']] },
    { re: /\b(where|address|location|located|directions?|map|office|near me|service area|serve|serving|cities)\b/, big: '10967 Clark Rd, Ste E, Inver Grove Heights, MN 55077', p: 'Based in Inver Grove Heights, serving the Minneapolis / Saint Paul area.', acts: [['Open in Google Maps', MAPS, 1], ['Contact us', 'contact-us.html']] },
    { re: /^(about|about us|who|who are you|company)\b|\b(family owned|owner|history|since 1999|years of experience)\b/, big: 'Family owned and operated since 1999', p: 'Over 20 years of concrete experience, specializing in residential and light commercial floors, inside and out.', acts: [['About us', 'about-us.html', 1], ['Read reviews', 'reviews.html']] }
  ];
  function answerFor(q) { var n = ' ' + norm(q) + ' ', raw = q.toLowerCase(); for (var i = 0; i < ANSWERS.length; i++) if (ANSWERS[i].re.test(n.trim()) || (i === 0 && raw.indexOf('$') >= 0)) return ANSWERS[i]; return null; }

  /* ---------- search ---------- */
  function search(q) {
    build();
    var raw = toks(q), terms = raw.filter(function (t) { return !STOP.has(t); });
    if (!terms.length) terms = raw;
    terms = terms.slice(0, 8);
    var groups = terms.map(function (t) { return { t: t, alts: (SYN[t] || []).map(stem) }; });
    var scores = new Map(), marks = new Set(), fixes = [];
    groups.forEach(function (g) {
      var per = new Map(), prim = matchTerm(g.t), solid = prim.filter(function (m) { return m[2] !== 'f'; }), use;
      if (solid.length) use = solid;
      else { var top = prim.reduce(function (a, m) { return Math.max(a, m[1]); }, 0); use = prim.filter(function (m) { return m[1] >= top - 0.001; }); if (use.length) { fixes.push([g.t, use[0][0]]); g.fix = use[0][0]; } }
      var pairs = use.map(function (m) { return [m[0], m[1]]; });
      g.alts.forEach(function (a) { matchTerm(a).forEach(function (m) { if (m[2] !== 'f') pairs.push([m[0], m[1] * 0.7]); }); });
      pairs.forEach(function (pr) {
        marks.add(pr[0]);
        VOC.get(pr[0]).forEach(function (w, key) { var v = pr[1] * w; if ((per.get(key) || 0) < v) per.set(key, v); });
      });
      g.generic = COLOR_WORDS.has(g.t) || (g.fix && COLOR_WORDS.has(g.fix));
      per.forEach(function (v, key) { var e = scores.get(key) || { s: 0, n: 0, cn: 0 }; e.s += v; e.n += 1; if (!g.generic) e.cn += 1; scores.set(key, e); });
    });
    var nq = norm(q), total = groups.length, specific = groups.filter(function (g) { return !g.generic; }).length;
    var docs = [], colors = [];
    scores.forEach(function (e, key) {
      if (typeof key === 'string') {
        if (e.cn > 0 && e.cn === specific) colors.push({ o: COLORS[+key.slice(1)], s: e.s });
        return;
      }
      var o = DOCS[key], s = e.s * (e.n === total ? 1 : 0.3 * e.n / total);
      if (nq.length >= 4) { if (o.hn.indexOf(nq) >= 0) s += 8; else if (o.xn.indexOf(nq) >= 0) s += 3; }
      s *= { page: 1.15, section: 1, faq: 1.1, photo: 0.85, review: 0.8 }[o.d.t] || 1;
      docs.push({ o: o, s: s, full: e.n === total });
    });
    docs.sort(function (a, b) { return b.s - a.s; });
    var full = docs.filter(function (r) { return r.full; });
    if (full.length >= 3) docs = full.concat(docs.filter(function (r) { return !r.full && r.s > (full[0] ? full[0].s * 0.5 : 0); }));
    if (docs.length) { var top = docs[0].s; docs = docs.filter(function (r) { return r.s >= top * 0.12; }); }
    colors.sort(function (a, b) { return b.s - a.s; });
    var colorGeneric = groups.some(function (g) { return g.generic; });
    if (!colors.length && colorGeneric && specific === 0) colors = COLORS.map(function (o) { return { o: o, s: 1, all: true }; });
    var fixed = null;
    if (fixes.length) { fixed = norm(q); fixes.forEach(function (f) { fixed = fixed.replace(new RegExp('\\b' + escRe(f[0]) + '\\w*'), f[1]); }); }
    return { docs: docs, colors: colors, marks: Array.from(marks), fixed: fixed, answer: answerFor(q) };
  }

  /* ---------- rendering ---------- */
  function snippet(text, marks) {
    var low = text.toLowerCase(), pos = -1;
    for (var i = 0; i < marks.length && pos < 0; i++) { var m = new RegExp('\\b' + escRe(marks[i])).exec(low); if (m) pos = m.index; }
    var start = pos > 70 ? text.lastIndexOf(' ', pos - 60) + 1 : 0, out = text.slice(start, start + 200);
    if (start + 200 < text.length) out = out.replace(/\s+\S*$/, '') + '…';
    return (start > 0 ? '…' : '') + out;
  }
  function hl(text, marks) {
    if (!marks.length) return escHtml(text);
    var re = new RegExp('\\b(' + marks.slice().sort(function (a, b) { return b.length - a.length; }).map(escRe).join('|') + ')[a-z]*', 'gi');
    return escHtml(text.replace(re, '\u0001$&\u0002')).replace(/\u0001/g, '<mark>').replace(/\u0002/g, '</mark>');
  }
  var TYPE = { page: 'Page', section: '', faq: 'Question', photo: 'Photo', review: 'Review' };
  function resultRow(r, marks) {
    var d = r.o.d, crumb = d.t === 'section' ? d.c : TYPE[d.t];
    if (d.t === 'page') crumb = d.c === 'Home' ? 'Home page' : d.c + ' page';
    var th = d.img ? '<span class="th" style="background-image:url(' + escHtml(d.img) + ')"></span>' : '<span class="th ic" aria-hidden="true">' + (d.t === 'faq' ? '?' : '“') + '</span>';
    var body = d.t === 'review' ? '“' + snippet(d.x, marks) + '”' : snippet(d.x, marks);
    return '<a class="sr" data-r href="' + escHtml(d.u) + '">' + th + '<span class="tx"><span class="crumb">' + escHtml(crumb) + '</span><b>' + hl(d.t === 'review' ? 'Review from ' + d.h : d.h, marks) + '</b><p>' + hl(body, marks) + '</p></span></a>';
  }
  function colorTile(c, marks) {
    return '<a class="sc" data-r data-blend="' + escHtml(c.d.n) + '" href="' + escHtml(c.d.u) + '"><i style="background-image:url(' + escHtml(c.d.img) + ')"></i>' + hl(c.d.n, marks) + '</a>';
  }
  function section(title, count, inner) { return '<div class="srch-sec"><p class="srch-h">' + title + (count ? '<em>' + count + '</em>' : '') + '</p>' + inner + '</div>'; }
  function answerCard(a) {
    var acts = a.acts.map(function (x) { var ext = /^https?:/.test(x[1]); return '<a class="btn ' + (x[2] ? 'btn-orange' : 'btn-ink') + '" data-r href="' + escHtml(x[1]) + '"' + (ext ? ' target="_blank" rel="noopener"' : '') + '>' + (x[2] ? escHtml(x[0]) : '<span class="gt">' + escHtml(x[0]) + '</span>') + '</a>'; }).join('');
    return '<div class="ans"><p class="srch-h">Quick answer</p><p class="big">' + escHtml(a.big) + '</p><p>' + escHtml(a.p) + '</p><div class="acts">' + acts + '</div></div>';
  }
  var POPULAR = ['Garage floor cost', 'How long does it take?', 'Warranty', 'Blue chip colors', 'Basement floors', 'Storage while you work', 'Commercial kitchens', 'Hours and phone'];
  function recent() { try { return JSON.parse(localStorage.getItem('ccRecent') || '[]').slice(0, 5); } catch (e) { return []; } }
  function remember(q) { q = q.trim(); if (q.length < 2) return; try { var r = recent().filter(function (x) { return x.toLowerCase() !== q.toLowerCase(); }); r.unshift(q); localStorage.setItem('ccRecent', JSON.stringify(r.slice(0, 5))); } catch (e) {} }
  function chips(list) { return '<div class="srch-chips">' + list.map(function (c) { return '<button type="button" class="srch-chip" data-q="' + escHtml(c) + '">' + escHtml(c) + '</button>'; }).join('') + '</div>'; }
  function emptyView() {
    build();
    var r = recent(), pages = DOCS.filter(function (o) { return o.d.t === 'page' && o.d.c !== 'Privacy policy'; }).slice(0, 9);
    return (r.length ? section('Recent searches', '', chips(r)) : '') + section('Popular searches', '', chips(POPULAR)) +
      section('Jump to a page', '', '<div class="srch-list">' + pages.map(function (o) { return resultRow({ o: o }, []); }).join('') + '</div>');
  }
  function resultsView(q, res, inline) {
    var html = '', n = 0;
    if (res.fixed && res.fixed !== norm(q)) html += '<p class="srch-fix">No exact match for “' + escHtml(q) + '”. Showing results for <b>' + escHtml(res.fixed) + '</b>.</p>';
    if (res.answer) html += answerCard(res.answer);
    if (res.colors.length) {
      var all = res.colors[0].all, show = res.colors.slice(0, all ? 12 : 16);
      html += section(all ? 'Chip colors' : 'Matching colors', res.colors.length + (res.colors.length === 1 ? ' blend' : ' blends'), '<div class="sr-colors">' + show.map(function (c) { return colorTile(c.o, all ? [] : res.marks); }).join('') + '</div>' + (res.colors.length > show.length ? '<a class="sr" data-r href="colors.html"><span class="th ic" aria-hidden="true">+</span><span class="tx"><b>See all ' + res.colors.length + ' chip colors</b><p>Every blend with its real swatch photo.</p></span></a>' : ''));
      n += res.colors.length;
    }
    var main = res.docs.filter(function (r) { return r.o.d.t !== 'photo' && r.o.d.t !== 'review'; });
    var photos = res.docs.filter(function (r) { return r.o.d.t === 'photo'; });
    var reviews = res.docs.filter(function (r) { return r.o.d.t === 'review'; });
    var lim = inline ? 20 : 8;
    if (main.length) { html += section('Best matches', main.length + (main.length === 1 ? ' result' : ' results'), '<div class="srch-list">' + main.slice(0, lim).map(function (r) { return resultRow(r, res.marks); }).join('') + '</div>'); n += main.length; }
    if (photos.length) { html += section('Photos', photos.length, '<div class="sr-photos">' + photos.slice(0, inline ? 20 : 8).map(function (r) { var d = r.o.d; return '<a class="sp" data-r href="' + escHtml(d.u) + '"><img src="' + escHtml(d.img) + '" alt="" loading="lazy"><span>' + escHtml(d.h) + '</span></a>'; }).join('') + '</div>'); n += photos.length; }
    if (reviews.length) { html += section('Reviews', reviews.length, '<div class="srch-list">' + reviews.slice(0, inline ? 6 : 3).map(function (r) { return resultRow(r, res.marks); }).join('') + '</div>'); n += reviews.length; }
    if (!n && !res.answer) {
      html += '<p class="srch-msg">No matches for <b>“' + escHtml(q) + '”</b>. Try a shorter word, or one of these:</p>' + chips(POPULAR.slice(0, 6)) +
        '<div class="ans"><p class="big">Ask us directly</p><p>Call ' + PHONE + ' Monday – Friday, 7am – 6pm, or get a free estimate online.</p><div class="acts"><a class="btn btn-orange" data-r href="./#estimate">Get my free estimate</a><a class="btn btn-ink" data-r href="' + TEL + '"><span class="gt">Call ' + PHONE + '</span></a></div></div>';
    } else if (!inline) {
      html += '<a class="sr" data-r data-all href="search.html?q=' + encodeURIComponent(q) + '"><span class="th ic" aria-hidden="true">→</span><span class="tx"><b>See every result for “' + escHtml(q) + '”</b><p>Open the full search page.</p></span></a>';
    }
    return { html: html, n: n + (res.answer ? 1 : 0) };
  }

  /* ---------- UI ---------- */
  var ICON = '<svg viewBox="0 0 24 24" stroke-linecap="round" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5 21 21"/></svg>';
  function panelHtml(id, inline) {
    return '<div class="srch-panel"><div class="srch-top">' + ICON + '<input id="' + id + '" type="search" placeholder="Search floors, colors, prices, answers…" autocomplete="off" spellcheck="false" enterkeyhint="search" aria-label="Search The Coating Crew" aria-controls="' + id + '-res">' +
      (inline ? '' : '<button type="button" class="srch-x" data-close>Close</button>') + '</div>' +
      '<div class="srch-body" id="' + id + '-res"></div><p id="' + id + '-st" style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)" aria-live="polite"></p>' +
      (inline ? '' : '<div class="srch-foot"><span><kbd>↑</kbd> <kbd>↓</kbd> move</span><span><kbd>Enter</kbd> open</span><span><kbd>Esc</kbd> close</span><span>Press <kbd>/</kbd> on any page to search</span></div>') + '</div>';
  }
  function wire(root, input, body, status, inline, onGo) {
    var timer = 0, active = -1, lastQ = '';
    function items() { return Array.prototype.slice.call(body.querySelectorAll('[data-r]')); }
    function setActive(i) { var it = items(); it.forEach(function (x) { x.classList.remove('on'); }); active = it.length ? (i + it.length) % it.length : -1; if (active >= 0) { it[active].classList.add('on'); it[active].scrollIntoView({ block: 'nearest' }); } }
    function render() {
      var q = input.value.trim(); lastQ = q; active = -1;
      if (!q) { body.innerHTML = emptyView(); status.textContent = ''; return; }
      var out = resultsView(q, search(q), inline); body.innerHTML = out.html; body.scrollTop = 0;
      status.textContent = out.n ? out.n + ' results' : 'No results';
      if (inline) { try { history.replaceState(null, '', location.pathname + '?q=' + encodeURIComponent(q)); } catch (e) {} }
    }
    input.addEventListener('input', function () { clearTimeout(timer); timer = setTimeout(render, 70); });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); setActive(active + 1); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); setActive(active - 1); }
      else if (e.key === 'Enter') { e.preventDefault(); clearTimeout(timer); if (!input.value.trim()) return; if (lastQ !== input.value.trim()) render(); var it = items().filter(function (x) { return !x.hasAttribute('data-all') || items().length === 1; }); var pick = active >= 0 ? items()[active] : it[0]; if (pick) { remember(input.value); pick.click(); } }
    });
    body.addEventListener('click', function (e) {
      var chip = e.target.closest('.srch-chip');
      if (chip) { input.value = chip.dataset.q; render(); input.focus(); return; }
      var a = e.target.closest('a[data-r]'); if (!a) return;
      remember(input.value);
      if (a.dataset.blend) { try { sessionStorage.setItem('ccBlend', a.dataset.blend); } catch (er) {} }
      if (a.hasAttribute('data-all')) { try { sessionStorage.setItem('ccQ', input.value.trim()); } catch (er) {} }
      if (onGo) onGo();
    });
    return { render: render };
  }

  var overlay = null, ui = null, opener = null;
  function ensureOverlay() {
    if (overlay) return;
    overlay = document.createElement('div'); overlay.className = 'srch'; overlay.hidden = true;
    overlay.setAttribute('role', 'dialog'); overlay.setAttribute('aria-modal', 'true'); overlay.setAttribute('aria-label', 'Search The Coating Crew');
    overlay.innerHTML = panelHtml('ccq', false); document.body.appendChild(overlay);
    var input = overlay.querySelector('#ccq');
    ui = wire(overlay, input, overlay.querySelector('#ccq-res'), overlay.querySelector('#ccq-st'), false, closeSearch);
    overlay.addEventListener('click', function (e) { if (e.target === overlay || e.target.closest('[data-close]')) closeSearch(); });
    overlay.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { e.preventDefault(); if (input.value) { input.value = ''; ui.render(); } else closeSearch(); }
      if (e.key === 'Tab') { var f = Array.prototype.slice.call(overlay.querySelectorAll('input,button,a[href]')).filter(function (x) { return x.offsetParent !== null; }); if (!f.length) return; var first = f[0], last = f[f.length - 1]; if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); } else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); } }
    });
  }
  function openSearch(src, q) {
    ensureOverlay(); opener = src || document.activeElement;
    var input = overlay.querySelector('#ccq'); if (typeof q === 'string') input.value = q;
    overlay.hidden = false; document.documentElement.style.overflow = 'hidden'; ui.render();
    setTimeout(function () { input.focus(); input.select(); }, 20);
  }
  function closeSearch() { if (!overlay || overlay.hidden) return; overlay.hidden = true; document.documentElement.style.overflow = ''; if (opener && opener.focus) opener.focus(); }

  document.addEventListener('click', function (e) { var b = e.target.closest('[data-search-open]'); if (b) { e.preventDefault(); openSearch(b); } });
  document.addEventListener('keydown', function (e) {
    var t = e.target, typing = t && (t.isContentEditable || /^(input|textarea|select)$/i.test(t.tagName));
    if ((e.key === '/' && !typing && !e.ctrlKey && !e.metaKey && !e.altKey) || ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K'))) {
      if (overlay && !overlay.hidden) return; var pageBox = document.getElementById('searchPage');
      e.preventDefault(); if (pageBox) { var pi = pageBox.querySelector('input'); if (pi) { pi.focus(); pi.select(); } } else openSearch(null);
    }
  });

  /* full search page */
  var pageBox = document.getElementById('searchPage');
  if (pageBox) {
    pageBox.innerHTML = panelHtml('ccp', true);
    var pin = pageBox.querySelector('#ccp'), q0 = '';
    try { var sp = new URLSearchParams(location.search); q0 = sp.get('q') || sp.get('query') || ''; } catch (e) {}
    if (!q0) { try { q0 = sessionStorage.getItem('ccQ') || ''; sessionStorage.removeItem('ccQ'); } catch (e) {} }
    pin.value = q0;
    var pui = wire(pageBox, pin, pageBox.querySelector('#ccp-res'), pageBox.querySelector('#ccp-st'), true, null);
    pui.render(); if (!q0) pin.focus();
  }

  /* open the answer a search result points to */
  function openTarget() {
    if (!location.hash || location.hash.length < 2) return;
    var el = null; try { el = document.getElementById(decodeURIComponent(location.hash.slice(1))); } catch (e) {}
    if (el && el.tagName === 'DETAILS') { el.open = true; setTimeout(function () { el.scrollIntoView({ block: 'center' }); }, 60); }
  }
  openTarget(); addEventListener('hashchange', openTarget);
  window.CCSearch = { open: openSearch, search: function (q) { return search(q); } };
})();
