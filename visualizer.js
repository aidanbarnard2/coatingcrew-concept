/* Floor visualizer: lays a real chip blend onto a real room photo.
   The floor in each photo was measured once (camera, floor plane, walls), and the room's own light,
   shadows and reflections were lifted out of the old floor. The new blend is drawn in perspective and
   lit by that same light, so it sits in the photo the way a real coating would. */
(function () {
  'use strict';

  var BLENDS = ['Armadillo', 'Basalt', 'Buckskin', 'Chestnut', 'Claystone', 'Denim', 'Dolphin', 'Domino', 'Driftwood', 'Garnet', 'Gunflint', 'Husky', 'Lanai Grey', 'Leopard', 'North Oaks', 'Oasis', 'Obsidian', 'Pebble Beach', 'Pecan', 'Pumice', 'Sandstone', 'Schist', 'Shale', 'Silver Creek', 'Slate', 'Slate Stone', 'Smoke', 'Tamarack', 'Thistle', 'Tidal Wave', 'Turquoise', 'Wombat Blue'];
  var slug = function (n) { return n.toLowerCase().replace(/ /g, '-'); };
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var VS = 'attribute vec2 p;varying vec2 vUv;void main(){vUv=vec2(p.x*.5+.5,.5-p.y*.5);gl_Position=vec4(p,0.,1.);}';
  var FS = [
    'precision highp float;',
    'varying vec2 vUv;',
    'uniform sampler2D tDay,tEve,tMask,tLight,tGloss,tChip,tPrev;',
    'uniform mat3 uM0,uM1,uM2;',
    'uniform vec2 uSize;',
    'uniform float uTile,uEve,uWipe,uOrig,uLS,uGS,uExp;',
    'vec3 toLin(vec3 c){return pow(c,vec3(2.2));}',
    'vec3 toSrgb(vec3 c){return pow(c,vec3(1.0/2.2));}',
    'vec3 tone(vec3 c){vec3 k=max(c-0.8,0.0);return min(c,vec3(0.8))+0.2*(1.0-exp(-k/0.2));}',
    'void main(){',
    '  vec3 bg=mix(texture2D(tDay,vUv).rgb,texture2D(tEve,vUv).rgb,uEve);',
    '  vec4 m=texture2D(tMask,vUv);',
    '  float cover=m.r*(1.0-uOrig);',
    '  if(cover<0.003){gl_FragColor=vec4(bg,1.0);return;}',
    '  vec2 px=vUv*uSize;',
    '  float sid=m.g*3.0;',
    '  vec3 q=sid<0.5?uM0*vec3(px,1.0):(sid<1.5?uM1*vec3(px,1.0):uM2*vec3(px,1.0));',
    '  vec2 tc=(q.xy/q.z)/uTile;',
    '  vec3 a=toLin(texture2D(tChip,tc,0.0).rgb);',
    '  vec3 b=toLin(texture2D(tPrev,tc,0.0).rgb);',
    '  float edge=uWipe*1.25*uSize.y-0.12*uSize.y;',
    '  float t=smoothstep(edge-26.0,edge+26.0,px.y);',
    '  vec3 alb=mix(a,b,t);',
    '  float wet=exp(-pow((px.y-edge)/18.0,2.0))*step(0.001,uWipe)*step(uWipe,0.999);',
    '  vec2 d=vec2(vUv.x,vUv.y*0.5),e=vec2(vUv.x,0.5+vUv.y*0.5);',
    '  vec3 sh=mix(toLin(texture2D(tLight,d).rgb),toLin(texture2D(tLight,e).rgb),uEve)*uLS;',
    '  vec3 gl=mix(toLin(texture2D(tGloss,d).rgb),toLin(texture2D(tGloss,e).rgb),uEve)*uGS;',
    '  vec3 c=alb*sh*uExp+gl+wet*0.10*sh;',
    '  c=toSrgb(tone(c));',
    '  gl_FragColor=vec4(mix(bg,c,cover),1.0);',
    '}'
  ].join('\n');

  function loadImg(src) {
    return new Promise(function (res, rej) { var i = new Image(); i.decoding = 'async'; i.onload = function () { res(i); }; i.onerror = rej; i.src = src; });
  }

  function Viz(root) {
    this.root = root;
    this.base = root.getAttribute('data-base') || 'img/viz/';
    this.stage = root.querySelector('.viz-stage');
    this.canvas = root.querySelector('canvas');
    this.fallback = root.querySelector('.viz-photo');
    this.status = root.querySelector('.viz-status');
    this.state = { room: 0, blend: root.getAttribute('data-blend') || 'Domino', eve: 0, orig: false };
    try { var saved = sessionStorage.getItem('ccBlend'); if (saved && BLENDS.indexOf(saved) >= 0) this.state.blend = saved; } catch (e) {}
    var asked = new URLSearchParams(location.search).get('blend');
    if (asked && BLENDS.indexOf(asked) >= 0) { this.state.blend = asked; try { sessionStorage.setItem('ccBlend', asked); sessionStorage.setItem('ccBlendPicked', '1'); } catch (e) {} }
    this.texCache = {}; this.roomCache = {};
    this.buildTiles();
    this.bind();
    var self = this;
    fetch(this.base + 'rooms.json').then(function (r) { return r.json(); }).then(function (rooms) {
      self.rooms = rooms; self.buildRooms(); return self.initGL();
    }).then(function (ok) { if (ok) return self.setRoom(0, true); self.noGL(); }).catch(function () { self.noGL(); });
  }

  /* sample board groups, each ordered light to dark (measured from the real chip photos) */
  var GROUPS = {
    gray: ['Schist', 'Slate Stone', 'North Oaks', 'Denim', 'Husky', 'Smoke', 'Domino', 'Basalt', 'Tamarack', 'Wombat Blue', 'Lanai Grey', 'Silver Creek'],
    warm: ['Pumice', 'Dolphin', 'Armadillo', 'Oasis', 'Claystone', 'Tidal Wave', 'Shale', 'Obsidian', 'Turquoise', 'Slate', 'Leopard', 'Gunflint'],
    tan: ['Thistle', 'Buckskin', 'Driftwood', 'Pecan', 'Pebble Beach', 'Sandstone', 'Garnet', 'Chestnut']
  };

  Viz.prototype.buildTiles = function () {
    var self = this;
    Array.prototype.forEach.call(this.root.querySelectorAll('.viz-tiles'), function (box) {
      (GROUPS[box.getAttribute('data-group')] || BLENDS).forEach(function (n) {
        var b = document.createElement('button');
        b.type = 'button'; b.className = 'sample'; b.dataset.blend = n;
        b.setAttribute('aria-pressed', String(n === self.state.blend));
        var face = document.createElement('span'); face.className = 'face';
        face.style.backgroundImage = 'url(img/colors/' + slug(n) + '.jpg)';
        var lab = document.createElement('span'); lab.className = 'lab'; lab.textContent = n;
        b.appendChild(face); b.appendChild(lab); box.appendChild(b);
      });
    });
    this.tiles = Array.prototype.slice.call(this.root.querySelectorAll('.sample'));
    this.showBlend();
  };

  Viz.prototype.showBlend = function () {
    var n = this.state.blend;
    Array.prototype.forEach.call(this.root.querySelectorAll('.viz-blend-name'), function (el) { el.textContent = n; });
    var lp = this.root.querySelector('.viz-loupe'); if (lp) lp.style.backgroundImage = 'url(img/colors/tex-m/' + slug(n) + '.jpg)';
  };

  Viz.prototype.buildRooms = function () {
    var box = this.root.querySelector('.viz-rooms'), self = this;
    this.rooms.forEach(function (r, i) {
      var b = document.createElement('button');
      b.type = 'button'; b.className = 'room'; b.dataset.i = i;
      b.setAttribute('aria-pressed', String(i === 0));
      var im = document.createElement('img'); im.alt = ''; im.loading = 'lazy'; im.src = self.base + r.key + '-thumb.jpg';
      var s = document.createElement('span'); s.textContent = r.name;
      b.appendChild(im); b.appendChild(s); box.appendChild(b);
    });
    this.roomBtns = Array.prototype.slice.call(box.querySelectorAll('.room'));
  };

  Viz.prototype.bind = function () {
    var self = this, root = this.root;
    root.addEventListener('click', function (e) {
      var t = e.target.closest('button'); if (!t || !root.contains(t)) return;
      if (t.classList.contains('sample')) self.setBlend(t.dataset.blend);
      else if (t.classList.contains('room')) self.setRoom(+t.dataset.i);
      else if (t.dataset.light) self.setLight(t.dataset.light === 'eve' ? 1 : 0);
      else if (t.classList.contains('viz-orig')) self.setOrig(!self.state.orig);
    });
  };

  Viz.prototype.announce = function () {
    if (!this.rooms) return;
    var r = this.rooms[this.state.room];
    var msg = this.state.orig ? 'Showing the original floor in the ' + r.name.toLowerCase() + '.' :
      'Showing ' + this.state.blend + ' in the ' + r.name.toLowerCase() + ', ' + (this.state.eve ? 'evening light' : 'daylight') + '.';
    if (this.status) this.status.textContent = msg;
    if (this.canvas) this.canvas.setAttribute('aria-label', 'Real job photo of a ' + r.name.toLowerCase() + (this.state.orig ? ' with its original floor' : ' re-coated in the ' + this.state.blend + ' blend') + ', ' + (this.state.eve ? 'evening light' : 'daylight'));
    var tag = this.root.querySelector('.viz-room-name'); if (tag) tag.textContent = r.name;
    var tb = this.root.querySelector('.viz-tag-blend'); if (tb) tb.textContent = this.state.orig ? 'Original floor' : this.state.blend;
  };

  Viz.prototype.initGL = function () {
    var c = this.canvas, gl = c.getContext('webgl', { antialias: false, preserveDrawingBuffer: true }) || c.getContext('experimental-webgl');
    if (!gl) return Promise.resolve(false);
    this.gl = gl;
    function sh(type, src) { var s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; }
    var p = gl.createProgram();
    gl.attachShader(p, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(p, sh(gl.FRAGMENT_SHADER, FS)); gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) return Promise.resolve(false);
    gl.useProgram(p); this.prog = p;
    var buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    var loc = gl.getAttribLocation(p, 'p'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    this.u = {};
    var self = this;
    ['tDay', 'tEve', 'tMask', 'tLight', 'tGloss', 'tChip', 'tPrev', 'uM0', 'uM1', 'uM2', 'uSize', 'uTile', 'uEve', 'uWipe', 'uOrig', 'uLS', 'uGS', 'uExp'].forEach(function (n) { self.u[n] = gl.getUniformLocation(p, n); });
    ['tDay', 'tEve', 'tMask', 'tLight', 'tGloss', 'tChip', 'tPrev'].forEach(function (n, i) { gl.uniform1i(self.u[n], i); });
    this.aniso = gl.getExtension('EXT_texture_filter_anisotropic') || gl.getExtension('WEBKIT_EXT_texture_filter_anisotropic');
    gl.pixelStorei(gl.UNPACK_COLORSPACE_CONVERSION_WEBGL, gl.NONE);
    return Promise.resolve(true);
  };

  Viz.prototype.tex = function (img, unit, repeat) {
    var gl = this.gl, t = gl.createTexture();
    gl.activeTexture(gl.TEXTURE0 + unit); gl.bindTexture(gl.TEXTURE_2D, t);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, gl.RGB, gl.UNSIGNED_BYTE, img);
    if (repeat) {
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.REPEAT); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.REPEAT);
      gl.generateMipmap(gl.TEXTURE_2D);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
      if (this.aniso) gl.texParameterf(gl.TEXTURE_2D, this.aniso.TEXTURE_MAX_ANISOTROPY_EXT, Math.min(16, gl.getParameter(this.aniso.MAX_TEXTURE_MAX_ANISOTROPY_EXT)));
    } else {
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    }
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    return t;
  };

  Viz.prototype.bindTex = function (t, unit) { var gl = this.gl; gl.activeTexture(gl.TEXTURE0 + unit); gl.bindTexture(gl.TEXTURE_2D, t); };

  Viz.prototype.chip = function (name) {
    var self = this;
    if (!this.texCache[name]) {
      this.texCache[name] = loadImg('img/colors/tex/' + slug(name) + '.jpg').then(function (img) { return self.tex(img, 5, true); });
    }
    return this.texCache[name];
  };

  Viz.prototype.loadRoom = function (i) {
    var r = this.rooms[i], b = this.base + r.key, self = this;
    if (!this.roomCache[i]) {
      this.roomCache[i] = Promise.all(['-day.jpg', '-eve.jpg', '-mask.png', '-light.jpg', '-gloss.jpg'].map(function (s) { return loadImg(b + s); }))
        .then(function (imgs) { return imgs.map(function (img, k) { return self.tex(img, k, false); }); });
    }
    return this.roomCache[i];
  };

  Viz.prototype.draw = function () {
    if (!this.cur) return;
    var gl = this.gl, u = this.u, r = this.rooms[this.state.room], s = this.state;
    this.cur.forEach(function (t, k) { this.bindTex(t, k); }, this);
    this.bindTex(this.chipTex, 5); this.bindTex(this.prevTex || this.chipTex, 6);
    var m = r.mats, I = [1, 0, 0, 0, 1, 0, 0, 0, 1];
    function T(a) { return [a[0], a[3], a[6], a[1], a[4], a[7], a[2], a[5], a[8]]; }
    gl.uniformMatrix3fv(u.uM0, false, T(m[0] || I)); gl.uniformMatrix3fv(u.uM1, false, T(m[1] || I)); gl.uniformMatrix3fv(u.uM2, false, T(m[2] || I));
    gl.uniform2f(u.uSize, r.W, r.H); gl.uniform1f(u.uTile, r.tile); gl.uniform1f(u.uLS, r.lightScale); gl.uniform1f(u.uGS, r.glossScale);
    gl.uniform1f(u.uExp, r.exposure || 1.0);
    gl.uniform1f(u.uEve, this.eveT); gl.uniform1f(u.uWipe, this.wipe); gl.uniform1f(u.uOrig, s.orig ? 1 : 0);
    gl.viewport(0, 0, this.canvas.width, this.canvas.height);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  };

  Viz.prototype.animate = function (key, to, ms, done) {
    var self = this, from = this[key], t0 = performance.now();
    if (reduce || ms === 0) { this[key] = to; this.draw(); if (done) done(); return; }
    cancelAnimationFrame(this['raf_' + key]);
    (function tick(t) {
      var p = Math.min(1, (t - t0) / ms), e = p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2;
      self[key] = from + (to - from) * e; self.draw();
      if (p < 1) self['raf_' + key] = requestAnimationFrame(tick); else if (done) done();
    })(t0);
  };

  Viz.prototype.setRoom = function (i, first) {
    var self = this, r = this.rooms[i];
    this.state.room = i;
    (this.roomBtns || []).forEach(function (b, k) { b.setAttribute('aria-pressed', String(k === i)); });
    if (this.fallback) { this.fallback.src = this.base + r.key + '-day.jpg'; this.fallback.alt = 'Real job photo: ' + r.name.toLowerCase(); }
    this.stage.classList.add('loading');
    return Promise.all([this.loadRoom(i), this.chip(this.state.blend)]).then(function (res) {
      if (self.state.room !== i) return;
      self.cur = res[0]; self.chipTex = res[1]; self.prevTex = null;
      self.canvas.width = r.W; self.canvas.height = r.H;
      self.stage.style.aspectRatio = r.W + ' / ' + r.H;
      if (self.eveT === undefined) self.eveT = self.state.eve;
      self.wipe = 0;
      self.draw();
      self.stage.classList.remove('loading'); self.stage.classList.add('ready');
      self.announce();
      if (first) self.root.dispatchEvent(new CustomEvent('viz:ready'));
    });
  };

  Viz.prototype.setBlend = function (name) {
    var self = this;
    if (name === this.state.blend && this.chipTex) return;
    this.state.blend = name;
    try { sessionStorage.setItem('ccBlend', name); sessionStorage.setItem('ccBlendPicked', '1'); } catch (e) {}
    this.tiles.forEach(function (t) { t.setAttribute('aria-pressed', String(t.dataset.blend === name)); });
    this.showBlend();
    this.root.dispatchEvent(new CustomEvent('viz:blend', { detail: name, bubbles: true }));
    if (!this.gl) return;
    if (this.state.orig) this.setOrig(false, true);
    this.chip(name).then(function (t) {
      if (self.state.blend !== name) return;
      self.prevTex = self.chipTex; self.chipTex = t;
      self.wipe = 0.0001;
      self.animate('wipe', 1, 1100, function () { self.prevTex = null; self.wipe = 0; self.draw(); });
      self.announce();
    });
  };

  Viz.prototype.setLight = function (v) {
    this.state.eve = v;
    Array.prototype.forEach.call(this.root.querySelectorAll('[data-light]'), function (b) { b.setAttribute('aria-pressed', String((b.dataset.light === 'eve') === !!v)); });
    this.stage.classList.toggle('is-eve', !!v);
    if (this.gl) this.animate('eveT', v, 700);
    this.announce();
  };

  Viz.prototype.setOrig = function (on, quiet) {
    this.state.orig = on;
    var b = this.root.querySelector('.viz-orig'); if (b) b.setAttribute('aria-pressed', String(on));
    this.draw(); if (!quiet) this.announce();
  };

  Viz.prototype.noGL = function () {
    this.stage.classList.add('nogl');
    if (this.status) this.status.textContent = 'This browser can’t run the visualizer, so you’re seeing the real job photo. Tap a sample to see the blend up close.';
  };

  window.CCViz = Viz;
  Array.prototype.forEach.call(document.querySelectorAll('[data-viz]'), function (el) {
    var start = function () { if (!el._viz) el._viz = new Viz(el); };
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (es) { if (es[0].isIntersecting) { io.disconnect(); start(); } }, { rootMargin: '600px 0px' });
      io.observe(el);
    } else start();
  });
})();
