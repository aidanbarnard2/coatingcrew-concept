/* Free-estimate form (home page) and the owner's lead inbox (owner.html).
   Leads go to a shared database when the page has one; otherwise they stay in this browser, so a request
   sent from the home page shows up on the owner page of the same browser. */
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var toast = function (t, b) { if (window.ccToast) window.ccToast(t, b); };
  var slug = function (n) { return n.toLowerCase().replace(/ /g, '-'); };
  var KEY = 'ccLeads';

  function readLocal() { try { return JSON.parse(localStorage.getItem(KEY) || '[]'); } catch (e) { return []; } }
  function writeLocal(list) { try { localStorage.setItem(KEY, JSON.stringify(list.slice(0, 200))); return true; } catch (e) { return false; } }
  function useDb() {
    var p = window.claude && window.claude.use ? Promise.resolve().then(function () { return window.claude.use('db'); }) : Promise.resolve(null);
    return p.catch(function () { return null; });
  }

  /* ---------- estimate form ----------
     One question per step. Picking an answer with a mouse or finger moves on by itself; keyboard and
     screen-reader users choose with the arrow keys and press Next, so nothing jumps ahead on them. */
  var est = $('#est');
  if (est) (function () {
    var step = 1, data = {}, picks = null, db = null;
    useDb().then(function (d) { if (d) db = d.collection('leads'); });
    try { picks = JSON.parse(sessionStorage.getItem('ccPicks') || 'null'); } catch (e) {}
    try { if (!picks && sessionStorage.getItem('ccBlendPicked')) picks = { touched: true, blend: sessionStorage.getItem('ccBlend') }; } catch (e) {}
    document.addEventListener('viz:change', function (e) { picks = e.detail; renderPicks(); });

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
    // the sample picked in the showroom, plus the answers so far (the room and lighting are only viewing aids, so they stay out of the request)
    function renderPicks() {
      var has = picks && picks.touched && picks.blend;
      if ($('#picksEmpty')) { $('#picksEmpty').hidden = true; $('#picksRow').hidden = !has; }
      if ($('#picks')) $('#picks').hidden = !(has || data.space || data.size || data.finish);   /* an empty box only sends people away from the form */
      if (has && $('#picksLoupe')) {
        $('#picksLoupe').style.backgroundImage = picks.bare ? 'none' : 'url(img/colors/l/' + slug(picks.blend) + '.webp)';
        var dl = $('#picksList'); dl.innerHTML = '';
        [['Sample', picks.bare ? 'Bare concrete for now (last picked: ' + picks.blend + ')' : picks.blend]].forEach(function (r) {
          if (!r[1]) return;
          var dt = document.createElement('dt'); dt.textContent = r[0];
          var dd = document.createElement('dd'); dd.textContent = r[1];
          dl.appendChild(dt); dl.appendChild(dd);
        });
        // a picked chip blend means a chip floor, unless they've chosen another finish
        if (!data.finish && !picks.bare) { data.finish = 'Chip'; var c = $('input[name="finish"][value="Chip"]', est); if (c) c.checked = true; }
      }
      var box = $('#estSummary'); if (!box) return; box.innerHTML = '';
      [data.space, data.size, data.finish].filter(Boolean).forEach(function (t) { var c = document.createElement('li'); c.className = 'chip'; c.textContent = t; box.appendChild(c); });
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
      if (n > 1 && window.ccTrack) window.ccTrack(n === 5 ? 'estimate_done' : 'estimate_step', { step: n });
      $('.est-progress', est).hidden = n === 5; $('.bar', est).hidden = n === 5;
      if (n === 2) renderSizes();
      renderPicks();
      if (focus) { var t = $('[data-step="' + n + '"]', est); if (t) t.focus({ preventScroll: false }); }
    }
    var pointerPick = false;
    est.addEventListener('pointerdown', function (e) { if (e.target.closest('.opt')) pointerPick = true; });
    est.addEventListener('keydown', function () { pointerPick = false; });
    est.addEventListener('change', function (e) {
      var t = e.target; if (t.type !== 'radio') return;
      data[t.name] = t.value;
      if (t.name === 'space') data.size = null;
      clearErr(); renderPicks();
      if (pointerPick) { pointerPick = false; var at = step; setTimeout(function () { if (step === at) go(step + 1, true); }, reduce ? 0 : 250); }
    });
    back.addEventListener('click', function () { go(Math.max(1, step - 1), true); });
    $('#estReset').addEventListener('click', function () { data = {}; est.reset(); go(1, true); });

    function fail(el, msg) {
      err.textContent = msg; err.hidden = false;
      if (el) { el.setAttribute('aria-invalid', 'true'); el.setAttribute('aria-describedby', 'estErr'); el.focus(); }
    }
    function save(lead) {
      var cfg = window.CC_CONFIG || {};
      // live site: every request is sent to the business's endpoint (CRM, email or text service)
      if (cfg.formEndpoint) return fetch(cfg.formEndpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(lead) }).then(function (r) { if (!r.ok) throw new Error('send'); });
      if (db) return db.add(lead);
      var list = readLocal(); list.unshift(Object.assign({ id: 'local-' + Date.now() }, lead));
      return writeLocal(list) ? Promise.resolve() : Promise.reject({ code: 'storage' });
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
      var p = picks && picks.touched ? picks : {};
      var lead = {
        name: name.value.trim().slice(0, 80), phone: phone.value.trim().slice(0, 30),
        email: $('#f-email').value.trim().slice(0, 120), zip: $('#f-zip').value.trim().slice(0, 5),
        source: $('#f-source').value || 'Not given', space: data.space || '', size: data.size || '',
        finish: data.finish || '', blend: p.blend && !p.bare ? p.blend : '',
        status: 'new', createdAt: Date.now()
      };
      var visit = window.ccVisit ? window.ccVisit() : null;
      if (visit) { lead.channel = visit.channel; lead.campaign = visit.campaign; lead.term = visit.term; lead.landing = visit.landing; lead.gclid = visit.ids.gclid; lead.fbclid = visit.ids.fbclid; }
      if (window.ccTrack) window.ccTrack('estimate_submit', { space: lead.space, size: lead.size, finish: lead.finish, blend: lead.blend, channel: lead.channel || '' });
      next.disabled = true; next.textContent = 'Sending…';
      save(lead).then(function () {
        next.disabled = false;
        $('#doneText').textContent = 'Thanks, ' + lead.name.split(' ')[0] + '. The Coating Crew will call ' + lead.phone + ' to schedule your free estimate.';
        $('#doneOffer').hidden = !(data.space === 'Garage' && data.size === '2 stall');
        go(5, true);
        toast('Request sent', 'It’s waiting in the owner’s lead inbox.');
      }, function () {
        next.disabled = false; next.textContent = 'Get My Free Estimate';
        fail(null, 'That didn’t send. Check your connection and press the button again, or call (651) 263-8557.');
      });
    });
    go(1);
  })();

  /* ---------- lead inbox (owner page) ---------- */
  var leadsBox = $('#leads');
  if (leadsBox) (function () {
    var col = null, list = [], seen = {}, first = true, live = $('#liveTag');
    function ago(ts) { var s = (Date.now() - ts) / 1000; if (s < 50) return 'just now'; if (s < 3600) return Math.round(s / 60) + ' min ago'; if (s < 86400) return Math.round(s / 3600) + ' hr ago'; return new Date(ts).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }); }
    function el(tag, cls, txt) { var x = document.createElement(tag); if (cls) x.className = cls; if (txt != null) x.textContent = txt; return x; }
    function render(fresh) {
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
      leadsBox.innerHTML = '';
      if (!list.length) {
        var em = el('div', 'empty'); em.appendChild(document.createTextNode('No leads yet. '));
        var a = el('a', null, 'Send a test request from the home page'); a.href = './#estimate'; em.appendChild(a);
        em.appendChild(document.createTextNode(' and it shows up here, with the floor they picked and where they heard about you.'));
        leadsBox.appendChild(em); return;
      }
      list.forEach(function (l) {
        var card = el('article', 'lead' + (fresh.indexOf(l.id) >= 0 ? ' fresh' : ''));
        var top = el('div', 'top'); top.appendChild(el('h3', 'who', l.name || 'No name')); top.appendChild(el('span', 'when', ago(l.createdAt || Date.now())));
        var ct = el('p', 'contact', [l.phone, l.zip ? 'ZIP ' + l.zip : '', l.email].filter(Boolean).join(', '));
        var meta = el('div', 'meta');
        [['src', l.channel ? 'Came from: ' + l.channel : ''], ['', l.campaign ? 'Campaign: ' + l.campaign : ''], ['', l.term ? 'Search: ' + l.term : ''], ['', l.landing ? 'Landed on: ' + l.landing : ''], ['src', l.source ? 'Says: ' + l.source : ''], ['', l.space], ['', l.size], ['', l.finish], ['', l.blend ? l.blend + ' blend' : ''], ['', l.status === 'called' ? 'Called' : '']]
          .forEach(function (m) { if (m[1]) meta.appendChild(el('span', m[0], m[1])); });
        var act = el('div', 'act');
        var call = el('button', null, l.status === 'called' ? 'Mark as new' : 'Mark called'); call.type = 'button';
        call.addEventListener('click', function () { setStatus(l, l.status === 'called' ? 'new' : 'called'); });
        var del = el('button', 'warn', 'Remove'); del.type = 'button';
        del.addEventListener('click', function () {
          act.innerHTML = ''; act.appendChild(el('span', null, 'Remove this lead?'));
          var yes = el('button', 'warn', 'Yes, remove'); yes.type = 'button';
          var no = el('button', null, 'Keep'); no.type = 'button';
          yes.addEventListener('click', function () { remove(l); });
          no.addEventListener('click', function () { render(); });
          act.appendChild(yes); act.appendChild(no); no.focus();
        });
        act.appendChild(call); act.appendChild(del);
        card.appendChild(top); card.appendChild(ct); card.appendChild(meta); card.appendChild(act); leadsBox.appendChild(card);
      });
    }
    function setStatus(l, s) {
      if (col) { col.doc(l.id).update({ status: s }).catch(function () { toast('Couldn’t update that lead', 'Try again in a moment.'); }); return; }
      l.status = s; writeLocal(list); render();
    }
    function remove(l) {
      if (col) { col.doc(l.id).delete().catch(function () { toast('Couldn’t remove that lead', 'Try again in a moment.'); }); return; }
      list = list.filter(function (x) { return x !== l; }); writeLocal(list); render();
    }
    setInterval(function () { $$('.when', leadsBox).forEach(function (w, i) { if (list[i]) w.textContent = ago(list[i].createdAt); }); }, 30000);
    useDb().then(function (db) {
      if (!db) {
        live.textContent = 'Demo mode'; $('#inboxNote').textContent = 'Leads stay in this browser';
        list = readLocal(); render();
        // a request sent from another tab shows up here right away
        addEventListener('storage', function (e) {
          if (e.key !== KEY) return;
          var before = {}; list.forEach(function (l) { before[l.id] = 1; });
          list = readLocal();
          var fresh = list.filter(function (l) { return !before[l.id]; }).map(function (l) { return l.id; });
          render(fresh);
          if (fresh.length) { var l = list[0]; toast('New lead from ' + l.source, (l.space || 'Floor') + (l.size ? ', ' + l.size : '') + ', ' + l.name); }
        });
        return;
      }
      col = db.collection('leads');
      live.textContent = 'Live'; live.classList.remove('off'); $('#inboxNote').textContent = 'Updates in real time';
      col.orderBy('createdAt', 'desc').limit(200).onSnapshot(function (snap) {
        var fresh = [];
        list = snap.docs.map(function (d) { var o = Object.assign({}, d.data()); o.id = d.id; return o; });
        snap.docChanges().forEach(function (c) {
          if (c.type !== 'added') return;
          if (!first && !seen[c.doc.id]) { var l = c.doc.data(); fresh.push(c.doc.id); toast('New lead from ' + (l.source || 'the website'), (l.space || 'Floor') + (l.size ? ', ' + l.size : '') + ', ' + (l.name || '')); }
          seen[c.doc.id] = true;
        });
        first = false; render(fresh);
      }, function () { live.textContent = 'Offline'; live.classList.add('off'); });
    });
  })();
})();
