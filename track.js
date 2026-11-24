/* Measurement layer. Every meaningful action is pushed to window.dataLayer, so Google Tag Manager, Google Ads
   and Meta can be attached without touching the pages. Nothing loads from a third party until an ID is set
   below, which keeps the concept fast and private.
   Also remembers how the visitor arrived (ad click IDs and UTM tags) so each lead carries its campaign. */
(function () {
  'use strict';
  var CONFIG = window.CC_CONFIG = {
    gtmId: '',          // e.g. 'GTM-XXXXXXX'  (Google Tag Manager: Google Ads + Analytics)
    metaPixelId: '',    // e.g. '123456789012345'
    formEndpoint: ''    // URL that receives each estimate request as JSON (CRM, Zapier, Formspree...). Empty = demo mode
  };
  var dl = window.dataLayer = window.dataLayer || [];
  window.ccTrack = function (event, data) {
    var e = { event: 'cc_' + event }; for (var k in (data || {})) e[k] = data[k];
    dl.push(e);
    if (window.fbq && (event === 'estimate_submit' || event === 'call_click')) window.fbq('track', event === 'call_click' ? 'Contact' : 'Lead');
  };

  /* how they got here: kept for the visit, attached to the lead */
  var KEYS = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'gclid', 'gbraid', 'wbraid', 'fbclid', 'msclkid'];
  var saved = {};
  try { saved = JSON.parse(sessionStorage.getItem('ccVisit') || '{}'); } catch (e) {}
  var q = new URLSearchParams(location.search), found = false;
  KEYS.forEach(function (k) { var v = q.get(k); if (v) { saved[k] = v.slice(0, 200); found = true; } });
  if (!saved.landing) { saved.landing = location.pathname.split('/').pop() || 'home'; saved.referrer = document.referrer ? document.referrer.split('/')[2] || '' : ''; found = true; }
  if (found) try { sessionStorage.setItem('ccVisit', JSON.stringify(saved)); } catch (e) {}
  window.ccVisit = function () {
    var v = saved, src = v.gclid || v.gbraid || v.wbraid ? 'Google Ads' : v.fbclid ? 'Meta ad' : v.msclkid ? 'Microsoft Ads' : v.utm_source ? v.utm_source + (v.utm_medium ? ' / ' + v.utm_medium : '') : v.referrer ? v.referrer : 'Direct';
    return { channel: src, campaign: v.utm_campaign || '', term: v.utm_term || '', landing: v.landing || '', ids: { gclid: v.gclid || '', fbclid: v.fbclid || '' } };
  };

  /* calls, estimate buttons and showroom actions */
  document.addEventListener('click', function (e) {
    var a = e.target.closest('a,button'); if (!a) return;
    var where = (a.closest('section,header,footer,nav,aside') || {}).id || (a.closest('header') ? 'header' : a.closest('footer') ? 'footer' : a.closest('.mbar') ? 'bottom bar' : '');
    if (a.href && a.href.indexOf('tel:') === 0) window.ccTrack('call_click', { place: where });
    else if (a.getAttribute('href') && /#estimate$/.test(a.getAttribute('href'))) window.ccTrack('estimate_cta', { place: where, label: a.textContent.trim() });
    else if (a.classList.contains('sample')) window.ccTrack('sample_pick', { blend: a.dataset.blend });
    else if (a.classList.contains('room')) window.ccTrack('room_pick', { room: a.textContent.trim() });
    else if (a.classList.contains('viz-compare')) window.ccTrack('before_after');
    else if (a.classList.contains('viz-day')) window.ccTrack('play_day');
  }, true);

  /* tags load only when an ID is filled in */
  if (CONFIG.gtmId) { dl.push({ 'gtm.start': Date.now(), event: 'gtm.js' }); var s = document.createElement('script'); s.async = true; s.src = 'https://www.googletagmanager.com/gtm.js?id=' + encodeURIComponent(CONFIG.gtmId); document.head.appendChild(s); }
  if (CONFIG.metaPixelId) {
    var f = window.fbq = function () { f.callMethod ? f.callMethod.apply(f, arguments) : f.queue.push(arguments); }; f.queue = []; f.loaded = true; f.version = '2.0';
    var m = document.createElement('script'); m.async = true; m.src = 'https://connect.facebook.net/en_US/fbevents.js'; document.head.appendChild(m);
    f('init', CONFIG.metaPixelId); f('track', 'PageView');
  }
})();
