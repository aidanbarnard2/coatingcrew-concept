/* Home page: the free-estimate form and the owner's lead inbox. */
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var toast = function (t, b) { if (window.ccToast) window.ccToast(t, b); };

  /* ---------- estimate form ----------
     One question per step. Picking an answer with a mouse or finger moves on by itself; keyboard and
     screen-reader users choose with the arrow keys and press Next, so nothing jumps ahead on them. */
  var est = $('#est'); if (!est) return;
  var step = 1, data = {}, blend = null;
  try { if (sessionStorage.getItem('ccBlendPicked')) blend = sessionStorage.getItem('ccBlend'); } catch (e) {}
  document.addEventListener('viz:blend', function (e) { blend = e.detail; renderSummary(); });

  var SIZES = { Garage: ['1 stall', '2 stall', '3+ stall'], other: ['Under 300 sq ft', '300 to 600 sq ft', '600 to 1,000 sq ft', 'Over 1,000 sq ft'] };
  var NEED = { 1: 'space', 2: 'size', 3: 'finish' };
  var err = $('#estErr'), next = $('#estNext'), back = $('#estBack'), stepTxt = $('#estStep');

  function renderSizes() {
    var list = data.space === 'Garage' ? SIZES.Garage : SIZES.other, box = $('#sizeOpts');
    $('#sizeLegend').textContent = data.space === 'Garage' ? 'How many stalls?' : 'About how big is it?';
    box.innerHTML = '';
    list.forEach(function (s, i) {
      var l = document.createElement('label'); l.className = 'opt';
      var inp = document.createElement('input'); inp.type = 'radio'; inp.name = 'size'; inp.value = s; inp.id = 'sz-' + i; inp.checked = data.size === s;
      var sp = document.createElement('span'); sp.textContent = s;
      l.appendChild(inp); l.appendChild(sp); box.appendChild(l);
    });
  }
  function renderSummary() {
    var box = $('#estSummary'); box.innerHTML = '';
    var parts = [data.space, data.size, data.finish, blend ? blend + ' blend' : null].filter(Boolean);
    $('#estSummaryWrap').hidden = !parts.length;
    parts.forEach(function (t) { var c = document.createElement('li'); c.className = 'chip'; c.textContent = t; box.appendChild(c); });
  }
  function clearErr() { err.hidden = true; err.textContent = ''; $$('[aria-invalid]', est).forEach(function (el) { el.removeAttribute('aria-invalid'); el.removeAttribute('aria-describedby'); }); }
  function go(n, focus) {
    step = n; clearErr();
    $$('[data-step]', est).forEach(function (fs) { fs.hidden = +fs.dataset.step !== n; });
    $('#estBar').style.width = Math.min(100, n * 25) + '%';
    back.hidden = n === 1 || n === 5;
    $('#estNav').hidden = n === 5;
    next.textContent = n === 4 ? 'Get My Free Estimate' : 'Next';
    stepTxt.textContent = 'Step ' + n + ' of 4';
    $('.est-progress', est).hidden = n === 5; $('.bar', est).hidden = n === 5;
    if (n === 2) renderSizes();
    renderSummary();
    if (focus) { var t = $('[data-step="' + n + '"]', est); if (t) t.focus({ preventScroll: false }); }
  }
  // pointer picks move on automatically; keyboard picks wait for Next
  var pointerPick = false;
  est.addEventListener('pointerdown', function (e) { if (e.target.closest('.opt')) pointerPick = true; });
  est.addEventListener('keydown', function () { pointerPick = false; });
  est.addEventListener('change', function (e) {
    var t = e.target; if (t.type !== 'radio') return;
    data[t.name] = t.value;
    if (t.name === 'space') data.size = null;
    clearErr(); renderSummary();
    if (pointerPick) { pointerPick = false; var at = step; setTimeout(function () { if (step === at) go(step + 1, true); }, reduce ? 0 : 250); }
  });
  back.addEventListener('click', function () { go(Math.max(1, step - 1), true); });
  $('#estReset').addEventListener('click', function () { data = {}; est.reset(); go(1, true); });

  function fail(el, msg) {
    err.textContent = msg; err.hidden = false;
    if (el) { el.setAttribute('aria-invalid', 'true'); el.setAttribute('aria-describedby', 'estErr'); el.focus(); }
  }
  est.addEventListener('submit', function (e) {
    e.preventDefault();
    if (step < 4) {
      if (!data[NEED[step]]) { var first = $('[data-step="' + step + '"] input', est); fail(first, 'Pick one of the options to continue.'); return; }
      go(step + 1, true); return;
    }
    var name = $('#f-name'), phone = $('#f-phone'), digits = phone.value.replace(/\D/g, '');
    clearErr();
    if (!name.value.trim()) return fail(name, 'Add your name so we know who to ask for.');
    if (digits.length < 10) return fail(phone, 'Enter a 10-digit phone number, like 651 555 0123.');
    var lead = {
      name: name.value.trim().slice(0, 80), phone: phone.value.trim().slice(0, 30),
      email: $('#f-email').value.trim().slice(0, 120), zip: $('#f-zip').value.trim().slice(0, 5),
      source: $('#f-source').value || 'Not given', space: data.space || '', size: data.size || '',
      finish: data.finish || '', blend: blend || '', status: 'new', createdAt: Date.now()
    };
    next.disabled = true; next.textContent = 'Sending…';
    saveLead(lead).then(function () {
      next.disabled = false;
      $('#doneText').textContent = 'Thanks, ' + lead.name.split(' ')[0] + '. The Coating Crew will call ' + lead.phone + ' to schedule your free estimate.';
      $('#doneOffer').hidden = !(data.space === 'Garage' && data.size === '2 stall');
      go(5, true);
    }, function (x) {
      next.disabled = false; next.textContent = 'Get My Free Estimate';
      fail(null, x && x.code === 'quota_exceeded' ? 'The demo inbox is full. Remove a few test leads below, then try again.' : 'That didn’t send. Check your connection and press the button again.');
    });
  });
  go(1);

  /* ---------- lead inbox (live when the page has a shared database, otherwise kept in this browser) ---------- */
  var leadsCol = null, localLeads = [], currentList = [], seenIds = {}, firstSnap = true, live = $('#liveTag');
  function saveLead(lead) {
    if (leadsCol) return leadsCol.add(lead);
    var l = Object.assign({ id: 'local-' + Date.now() }, lead);
    localLeads.unshift(l); renderLeads(localLeads, [l.id]);
    toast('New lead from ' + l.source, (l.space || 'Floor') + (l.size ? ' · ' + l.size : '') + ' · ' + l.name);
    return Promise.resolve();
  }
  function ago(ts) { var s = (Date.now() - ts) / 1000; if (s < 50) return 'just now'; if (s < 3600) return Math.round(s / 60) + ' min ago'; if (s < 86400) return Math.round(s / 3600) + ' hr ago'; return new Date(ts).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }); }
  function el(tag, cls, txt) { var x = document.createElement(tag); if (cls) x.className = cls; if (txt != null) x.textContent = txt; return x; }
  function renderLeads(list, fresh) {
    fresh = fresh || [];
    $('#kTotal').textContent = list.length;
    $('#kGarage').textContent = list.filter(function (l) { return l.space === 'Garage' && l.size === '2 stall'; }).length;
    var counts = {}; list.forEach(function (l) { counts[l.source] = (counts[l.source] || 0) + 1; });
    var srcs = Object.keys(counts).sort(function (a, b) { return counts[b] - counts[a]; }), max = srcs.length ? counts[srcs[0]] : 1, sb = $('#sources');
    sb.innerHTML = '';
    if (!srcs.length) sb.appendChild(el('p', null, 'Sources appear here as leads come in.'));
    srcs.forEach(function (s) {
      var row = el('div', 'srcrow'), tr = el('span', 'track'), i = el('i');
      tr.setAttribute('aria-hidden', 'true'); i.style.width = (counts[s] / max * 100) + '%'; tr.appendChild(i);
      row.appendChild(el('span', null, s)); row.appendChild(tr); row.appendChild(el('b', null, counts[s])); sb.appendChild(row);
    });
    var box = $('#leads'); box.innerHTML = '';
    if (!list.length) { box.appendChild(el('div', 'empty', 'No leads yet. Fill out the free estimate form above and it shows up here right away, with where they heard about you.')); return; }
    list.forEach(function (l) {
      var card = el('article', 'lead' + (fresh.indexOf(l.id) >= 0 ? ' fresh' : ''));
      var top = el('div', 'top'); top.appendChild(el('span', 'who', l.name || 'No name')); top.appendChild(el('span', 'when', ago(l.createdAt || Date.now())));
      var ph = el('span', 'phone', (l.phone || '') + (l.zip ? '  ·  ZIP ' + l.zip : '') + (l.email ? '  ·  ' + l.email : ''));
      var meta = el('div', 'meta');
      [['src', l.source], ['', l.space], ['', l.size], ['', l.finish], ['', l.blend ? l.blend + ' blend' : ''], ['', l.status === 'called' ? 'Called' : '']].forEach(function (m) { if (m[1]) meta.appendChild(el('span', m[0], m[1])); });
      var act = el('div', 'act');
      var call = el('button', null, l.status === 'called' ? 'Mark as new' : 'Mark called'); call.type = 'button';
      call.addEventListener('click', function () { setStatus(l, l.status === 'called' ? 'new' : 'called'); });
      var del = el('button', 'warn', 'Remove'); del.type = 'button';
      del.addEventListener('click', function () {
        act.innerHTML = ''; act.appendChild(el('span', null, 'Remove this lead?'));
        var yes = el('button', 'warn', 'Yes, remove'); yes.type = 'button';
        var no = el('button', null, 'Keep'); no.type = 'button';
        yes.addEventListener('click', function () { removeLead(l); });
        no.addEventListener('click', function () { renderLeads(leadsCol ? currentList : localLeads); });
        act.appendChild(yes); act.appendChild(no); no.focus();
      });
      act.appendChild(call); act.appendChild(del);
      card.appendChild(top); card.appendChild(ph); card.appendChild(meta); card.appendChild(act); box.appendChild(card);
    });
  }
  function setStatus(l, s) { if (leadsCol && String(l.id).indexOf('local-') !== 0) leadsCol.doc(l.id).update({ status: s }).catch(function () { toast('Couldn’t update that lead', 'Try again in a moment.'); }); else { l.status = s; renderLeads(localLeads); } }
  function removeLead(l) { if (leadsCol && String(l.id).indexOf('local-') !== 0) leadsCol.doc(l.id).delete().catch(function () { toast('Couldn’t remove that lead', 'Try again in a moment.'); }); else { localLeads = localLeads.filter(function (x) { return x !== l; }); renderLeads(localLeads); } }
  renderLeads([]);
  setInterval(function () { $$('#leads .when').forEach(function (w, i) { var l = (leadsCol ? currentList : localLeads)[i]; if (l) w.textContent = ago(l.createdAt); }); }, 30000);
  (function connect() {
    var p = window.claude && window.claude.use ? Promise.resolve().then(function () { return window.claude.use('db'); }) : Promise.resolve(null);
    p.catch(function () { return null; }).then(function (db) {
      if (!db) { live.textContent = 'Demo mode'; $('#inboxNote').textContent = 'Leads stay in this browser'; return; }
      leadsCol = db.collection('leads');
      live.textContent = 'Live'; live.classList.remove('off'); $('#inboxNote').textContent = 'Updates in real time';
      leadsCol.orderBy('createdAt', 'desc').limit(200).onSnapshot(function (snap) {
        var fresh = [];
        currentList = snap.docs.map(function (d) { var o = Object.assign({}, d.data()); o.id = d.id; return o; });
        snap.docChanges().forEach(function (c) {
          if (c.type !== 'added') return;
          if (!firstSnap && !seenIds[c.doc.id]) { var l = c.doc.data(); fresh.push(c.doc.id); toast('New lead from ' + (l.source || 'the website'), (l.space || 'Floor') + (l.size ? ' · ' + l.size : '') + ' · ' + (l.name || '')); }
          seenIds[c.doc.id] = true;
        });
        firstSnap = false; renderLeads(currentList, fresh);
      }, function () { live.textContent = 'Offline'; live.classList.add('off'); });
    });
  })();
})();
