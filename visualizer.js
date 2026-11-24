/* Floor visualizer: 3D rooms lit by real light simulation, relit live in the browser.
   Every light in a room (the sun at three times of day, the sky, ceiling lights and lamps) was rendered on
   its own with white light. Light adds up, so mixing those renders with any brightness and color gives the
   same picture as rendering that lighting from scratch. The floor was rendered matte (to know how much light
   reaches each spot) and clear-coated (to capture its reflections), so any chip blend can be laid in. */
(function () {
  'use strict';

  var BLENDS = ['Armadillo', 'Basalt', 'Buckskin', 'Chestnut', 'Claystone', 'Denim', 'Dolphin', 'Domino', 'Driftwood', 'Garnet', 'Gunflint', 'Husky', 'Lanai Grey', 'Leopard', 'North Oaks', 'Oasis', 'Obsidian', 'Pebble Beach', 'Pecan', 'Pumice', 'Sandstone', 'Schist', 'Shale', 'Silver Creek', 'Slate', 'Slate Stone', 'Smoke', 'Tamarack', 'Thistle', 'Tidal Wave', 'Turquoise', 'Wombat Blue'];
  /* sample board groups, each ordered light to dark (measured from the real chip photos) */
  var GROUPS = {
    gray: ['Schist', 'Slate Stone', 'North Oaks', 'Denim', 'Husky', 'Smoke', 'Domino', 'Basalt', 'Tamarack', 'Wombat Blue', 'Lanai Grey', 'Silver Creek'],
    warm: ['Pumice', 'Dolphin', 'Armadillo', 'Oasis', 'Claystone', 'Tidal Wave', 'Shale', 'Obsidian', 'Turquoise', 'Slate', 'Leopard', 'Gunflint'],
    tan: ['Thistle', 'Buckskin', 'Driftwood', 'Pecan', 'Pebble Beach', 'Sandstone', 'Garnet', 'Chestnut']
  };
  var CONCRETE = 'Bare concrete';
  var slug = function (n) { return n.toLowerCase().replace(/ /g, '-'); };
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------------- light ---------------- */
  var LUM = [0.2126, 0.7152, 0.0722];
  function lum(c) { return c[0] * LUM[0] + c[1] * LUM[1] + c[2] * LUM[2]; }
  function norm(c) { var l = lum(c) || 1; return [c[0] / l, c[1] / l, c[2] / l]; }
  function scale(c, k) { return [c[0] * k, c[1] * k, c[2] * k]; }
  function kelvin(k) {
    var t = k / 100, r, g, b;
    r = t <= 66 ? 255 : 329.698727446 * Math.pow(t - 60, -0.1332047592);
    g = t <= 66 ? 99.4708025861 * Math.log(t) - 161.1195681661 : 288.1221695283 * Math.pow(t - 60, -0.0755148492);
    b = t >= 66 ? 255 : (t <= 19 ? 0 : 138.5177312231 * Math.log(t - 10) - 305.0447927307);
    return norm([r, g, b].map(function (v) { return Math.pow(Math.min(1, Math.max(0, v / 255)), 2.2); }));
  }
  function kName(k) { return k <= 2700 ? 'warm white' : k <= 3500 ? 'soft white' : k <= 4500 ? 'neutral white' : 'cool daylight'; }
  var SUNCOL = [norm([1, 0.86, 0.68]), norm([1, 0.96, 0.9]), norm([1, 0.62, 0.32])];
  var TIMES = {
    morning: { label: 'Morning', sun: [9, 0, 0], sky: 0.8, skyCol: norm([0.78, 0.87, 1]) },
    midday: { label: 'Midday', sun: [0, 12, 0], sky: 1.0, skyCol: norm([0.78, 0.87, 1]) },
    golden: { label: 'Golden hour', sun: [0, 0, 7], sky: 0.5, skyCol: norm([0.85, 0.8, 0.9]) },
    dusk: { label: 'Dusk', sun: [0, 0, 0], sky: 0.035, skyCol: norm([0.52, 0.56, 0.95]) },
    night: { label: 'Night', sun: [0, 0, 0], sky: 0.0012, skyCol: norm([0.42, 0.47, 0.7]) }
  };
  var CLOUDY_SKY = norm([0.8, 0.85, 0.95]);
  var PRESETS = {
    morning: { label: 'Sunny morning', time: 'morning', cloudy: false, ceil: 0, lamps: 0, k: 3000 },
    afternoon: { label: 'Bright afternoon', time: 'midday', cloudy: false, ceil: 0, lamps: 0, k: 4000 },
    cloudy: { label: 'Cloudy day', time: 'midday', cloudy: true, ceil: 0, lamps: 0, k: 4000 },
    golden: { label: 'Golden hour', time: 'golden', cloudy: false, ceil: 60, lamps: 60, k: 2700 },
    evening: { label: 'Evening, warm bulbs', time: 'dusk', cloudy: false, ceil: 100, lamps: 100, k: 2700 },
    nightcool: { label: 'Night, cool LEDs', time: 'night', cloudy: false, ceil: 100, lamps: 0, k: 5000 },
    dark: { label: 'Lights off', time: 'night', cloudy: false, ceil: 0, lamps: 0, k: 3000 }
  };

  /* six light groups in the order they are packed: sun_am, sun_noon, sun_pm, sky, ceiling, lamps */
  function lightWeights(s) {
    var t = TIMES[s.time], w = [];
    for (var i = 0; i < 3; i++) w.push(scale(SUNCOL[i], s.cloudy ? 0 : t.sun[i]));
    w.push(s.cloudy ? scale(CLOUDY_SKY, t.sky * 1.8) : scale(t.skyCol, t.sky));
    var bulb = kelvin(s.k);
    w.push(scale(bulb, s.ceilOn ? s.ceil / 100 : 0));
    w.push(scale(bulb, s.lampsOn ? s.lamps / 100 : 0));
    return w;
  }

  /* ---------------- WebGL ---------------- */
  var VS = 'attribute vec2 p;varying vec2 vUv;void main(){vUv=vec2(p.x*.5+.5,.5-p.y*.5);gl_Position=vec4(p,0.,1.);}';
  var FS = [
    'precision highp float;',
    'varying vec2 vUv;',
    'uniform sampler2D tB0,tB1,tG0,tG1,tMask,tChip,tPrev;',
    'uniform vec3 uW[6];uniform vec3 uG[6];',
    'uniform mat3 uM;uniform vec2 uSize;uniform vec4 uCrop;',
    'uniform float uTile,uWipe,uGlossK,uPrevGlossK;',
    'vec3 dec(vec3 c){return pow(c,vec3(2.2));}',
    'vec3 aces(vec3 x){return clamp((x*(2.51*x+0.03))/(x*(2.43*x+0.59)+0.14),0.0,1.0);}',
    'void main(){',
    '  vec2 a0=vec2(vUv.x,vUv.y/3.0),a1=vec2(vUv.x,(vUv.y+1.0)/3.0),a2=vec2(vUv.x,(vUv.y+2.0)/3.0);',
    '  vec3 bg=uW[0]*dec(texture2D(tB0,a0).rgb)+uW[1]*dec(texture2D(tB0,a1).rgb)+uW[2]*dec(texture2D(tB0,a2).rgb)',
    '         +uW[3]*dec(texture2D(tB1,a0).rgb)+uW[4]*dec(texture2D(tB1,a1).rgb)+uW[5]*dec(texture2D(tB1,a2).rgb);',
    '  float cover=texture2D(tMask,vUv).r;',
    '  vec3 c=bg;',
    '  if(cover>0.002){',
    '    vec2 px=vUv*uSize;',
    '    vec3 q=uM*vec3(px,1.0);',
    '    vec2 tc=(q.xy/q.z)/uTile;',
    '    vec3 al=pow(texture2D(tChip,tc).rgb,vec3(2.2));',
    '    vec3 bl=pow(texture2D(tPrev,tc).rgb,vec3(2.2));',
    '    float edge=uWipe*1.25*uSize.y-0.12*uSize.y;',
    '    float t=smoothstep(edge-24.0,edge+24.0,px.y);',
    '    vec3 alb=mix(al,bl,t);',
    '    float gk=mix(uGlossK,uPrevGlossK,t);',
    '    vec2 g=(px-uCrop.xy)/(uCrop.zw-uCrop.xy);',
    '    vec3 gl=vec3(0.0);',
    '    if(g.x>=0.0&&g.x<=1.0&&g.y>=0.0&&g.y<=1.0){',
    '      vec2 g0=vec2(g.x,g.y/3.0),g1=vec2(g.x,(g.y+1.0)/3.0),g2=vec2(g.x,(g.y+2.0)/3.0);',
    '      gl=uG[0]*dec(texture2D(tG0,g0).rgb)+uG[1]*dec(texture2D(tG0,g1).rgb)+uG[2]*dec(texture2D(tG0,g2).rgb)',
    '        +uG[3]*dec(texture2D(tG1,g0).rgb)+uG[4]*dec(texture2D(tG1,g1).rgb)+uG[5]*dec(texture2D(tG1,g2).rgb);',
    '    }',
    '    float wet=exp(-pow((px.y-edge)/16.0,2.0))*step(0.001,uWipe)*step(uWipe,0.999);',
    '    vec3 fl=alb*bg*2.0+gl*gk+wet*0.06*bg;',
    '    c=mix(bg,fl,cover);',
    '  }',
    '  gl_FragColor=vec4(pow(aces(c),vec3(1.0/2.2)),1.0);',
    '}'
  ].join('\n');

  function loadImg(src) {
    return new Promise(function (res, rej) { var i = new Image(); i.decoding = 'async'; i.onload = function () { res(i); }; i.onerror = rej; i.src = src; });
  }

  function Viz(root) {
    this.root = root;
    this.base = root.getAttribute('data-base') || 'img/studio/';
    this.stage = root.querySelector('.viz-stage');
    this.canvas = root.querySelector('canvas');
    this.poster = root.querySelector('.viz-photo');
    this.status = root.querySelector('.viz-status');
    this.state = { room: 0, blend: root.getAttribute('data-blend') || 'Domino', bare: false, time: 'midday', cloudy: false,
      ceilOn: false, ceil: 100, lampsOn: false, lamps: 100, k: 3000, preset: 'afternoon' };
    try { var saved = sessionStorage.getItem('ccBlend'); if (saved && BLENDS.indexOf(saved) >= 0) this.state.blend = saved; } catch (e) {}
    var asked = new URLSearchParams(location.search).get('blend');
    if (asked && BLENDS.indexOf(asked) >= 0) { this.state.blend = asked; try { sessionStorage.setItem('ccBlend', asked); sessionStorage.setItem('ccBlendPicked', '1'); } catch (e) {} }
    this.texCache = {}; this.roomCache = {};
    this.buildTiles();
    this.bind();
    this.syncControls();
    var self = this;
    fetch(this.base + 'rooms.json').then(function (r) { return r.json(); }).then(function (rooms) {
      self.rooms = rooms; self.buildRooms(); return self.initGL();
    }).then(function (ok) { if (ok) return self.setRoom(0, true); self.noGL(); }).catch(function () { self.noGL(); });
  }

  Viz.prototype.q = function (sel) { return this.root.querySelector(sel); };

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
    var lp = this.q('.viz-loupe'); if (lp) lp.style.backgroundImage = 'url(img/colors/tex-m/' + slug(n) + '.jpg)';
  };

  Viz.prototype.buildRooms = function () {
    var box = this.q('.viz-rooms'), self = this;
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
      else if (t.dataset.preset) self.applyPreset(t.dataset.preset);
      else if (t.dataset.time) self.setLight({ time: t.dataset.time });
      else if (t.dataset.sky) self.setLight({ cloudy: t.dataset.sky === 'cloud' });
      else if (t.classList.contains('viz-ceil-on')) self.setLight({ ceilOn: !self.state.ceilOn });
      else if (t.classList.contains('viz-lamps-on')) self.setLight({ lampsOn: !self.state.lampsOn });
      else if (t.classList.contains('viz-orig')) self.setBare(!self.state.bare);
    });
    var on = function (sel, fn) { var el = self.q(sel); if (el) el.addEventListener('input', function () { fn(+el.value); }); };
    on('.viz-ceil-dim', function (v) { self.setLight({ ceil: v, ceilOn: true }, true); });
    on('.viz-lamps-dim', function (v) { self.setLight({ lamps: v, lampsOn: true }, true); });
    on('.viz-k', function (v) { self.setLight({ k: v }, true); });
  };

  Viz.prototype.syncControls = function () {
    var s = this.state, root = this.root, self = this;
    var press = function (sel, fn) { Array.prototype.forEach.call(root.querySelectorAll(sel), function (b) { b.setAttribute('aria-pressed', String(fn(b))); }); };
    press('[data-time]', function (b) { return b.dataset.time === s.time; });
    press('[data-sky]', function (b) { return (b.dataset.sky === 'cloud') === s.cloudy; });
    press('[data-preset]', function (b) { return b.dataset.preset === s.preset; });
    press('.viz-ceil-on', function () { return s.ceilOn; });
    press('.viz-lamps-on', function () { return s.lampsOn; });
    press('.viz-orig', function () { return s.bare; });
    var set = function (inSel, outSel, v, txt) {
      var el = self.q(inSel), o = self.q(outSel);
      if (el) { if (document.activeElement !== el) el.value = v; el.setAttribute('aria-valuetext', txt); }
      if (o) o.textContent = txt;
    };
    set('.viz-ceil-dim', '.viz-ceil-out', s.ceil, s.ceil + '%');
    set('.viz-lamps-dim', '.viz-lamps-out', s.lamps, s.lamps + '%');
    set('.viz-k', '.viz-k-out', s.k, s.k + 'K, ' + kName(s.k));
    var tl = this.q('.viz-tag-light'); if (tl) tl.textContent = this.lightLabel();
  };

  Viz.prototype.lightLabel = function () {
    var s = this.state;
    if (s.preset && PRESETS[s.preset]) return PRESETS[s.preset].label;
    var day = s.time !== 'night' && s.time !== 'dusk';
    var parts = [TIMES[s.time].label + (s.cloudy && day ? ', cloudy' : '')];
    if (s.ceilOn || s.lampsOn) parts.push(kName(s.k) + ' bulbs');
    else if (!day) parts.push('lights off');
    return parts.join(', ');
  };

  Viz.prototype.announce = function () {
    if (!this.rooms) return;
    var r = this.rooms[this.state.room], floor = this.state.bare ? 'bare concrete' : 'a ' + this.state.blend + ' chip floor';
    var lab = this.lightLabel();
    var msg = r.name + ' with ' + floor + ', ' + lab.charAt(0).toLowerCase() + lab.slice(1);
    if (this.status) this.status.textContent = 'Showing the ' + msg.charAt(0).toLowerCase() + msg.slice(1) + '.';
    if (this.canvas) this.canvas.setAttribute('aria-label', msg);
    var tb = this.q('.viz-tag-blend'); if (tb) tb.textContent = this.state.bare ? 'Bare concrete' : this.state.blend;
  };

  Viz.prototype.applyPreset = function (key) {
    var p = PRESETS[key]; if (!p) return;
    this.setLight({ time: p.time, cloudy: p.cloudy, ceilOn: p.ceil > 0, ceil: p.ceil || this.state.ceil,
      lampsOn: p.lamps > 0, lamps: p.lamps || this.state.lamps, k: p.k, preset: key });
  };

  Viz.prototype.setLight = function (patch, instant) {
    var s = this.state;
    for (var k in patch) s[k] = patch[k];
    if (!('preset' in patch)) s.preset = null;
    this.syncControls();
    this.announce();
    if (this.gl && this.cur) this.fadeLights(instant ? 0 : 650);
  };

  /* per-room light scaling: indoor lights at full ~ 45% (ceiling) and 20% (lamps) of a bright afternoon */
  Viz.prototype.units = function (r) {
    var day = 0, w = lightWeights({ time: 'midday', cloudy: false, ceilOn: false, lampsOn: false, ceil: 0, lamps: 0, k: 4000 });
    for (var i = 0; i < 6; i++) day += lum(w[i]) * r.mean[i];
    return { day: day, u: [1, 1, 1, 1, 0.45 * day / Math.max(r.mean[4], 1e-9), 0.2 * day / Math.max(r.mean[5], 1e-9)] };
  };

  Viz.prototype.fadeLights = function (ms) {
    var self = this, r = this.rooms[this.state.room], un = this.units(r);
    var target = lightWeights(this.state).map(function (c, i) { return scale(c, un.u[i]); });
    var from = this.w, t0 = performance.now();
    cancelAnimationFrame(this.rafL);
    if (reduce || !ms || !from) { this.w = target; this.draw(); return; }
    (function tick(t) {
      var p = Math.min(1, (t - t0) / ms), e = p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2;
      self.w = from.map(function (c, i) { return [0, 1, 2].map(function (j) { return c[j] + (target[i][j] - c[j]) * e; }); });
      self.draw();
      if (p < 1) self.rafL = requestAnimationFrame(tick);
    })(t0);
  };

  Viz.prototype.initGL = function () {
    var c = this.canvas, gl = c.getContext('webgl', { antialias: false, preserveDrawingBuffer: true }) || c.getContext('experimental-webgl');
    if (!gl) return Promise.resolve(false);
    this.gl = gl;
    function sh(type, src) { var s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; }
    var p = gl.createProgram();
    gl.attachShader(p, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(p, sh(gl.FRAGMENT_SHADER, FS)); gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) return Promise.resolve(false);
    gl.useProgram(p);
    var buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    var loc = gl.getAttribLocation(p, 'p'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    var u = this.u = {};
    ['tB0', 'tB1', 'tG0', 'tG1', 'tMask', 'tChip', 'tPrev', 'uW', 'uG', 'uM', 'uSize', 'uCrop', 'uTile', 'uWipe', 'uGlossK', 'uPrevGlossK']
      .forEach(function (n) { u[n] = gl.getUniformLocation(p, n); });
    ['tB0', 'tB1', 'tG0', 'tG1', 'tMask', 'tChip', 'tPrev'].forEach(function (n, i) { gl.uniform1i(u[n], i); });
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
    if (!this.texCache[name]) this.texCache[name] = loadImg('img/colors/tex/' + slug(name) + '.jpg').then(function (img) { return self.tex(img, 5, true); });
    return this.texCache[name];
  };

  Viz.prototype.loadRoom = function (i) {
    var r = this.rooms[i], b = this.base + r.key, self = this;
    if (!this.roomCache[i]) {
      this.roomCache[i] = Promise.all(['-bg0.jpg', '-bg1.jpg', '-gl0.jpg', '-gl1.jpg', '-mask.png'].map(function (s) { return loadImg(b + s); }))
        .then(function (imgs) { return imgs.map(function (img, k) { return self.tex(img, k, false); }); });
    }
    return this.roomCache[i];
  };

  /* camera-like exposure: brighter scenes get a shorter exposure, but night still looks like night;
     white balance takes out about 60% of the light's color cast, the way a phone camera does */
  Viz.prototype.exposure = function (w, r) {
    var un = this.units(r), L = 0, cav = [0, 0, 0];
    for (var i = 0; i < 6; i++) { L += lum(w[i]) * r.mean[i]; for (var j = 0; j < 3; j++) cav[j] += w[i][j] * r.meanRGB[i][j]; }
    // the camera brightens dim scenes, but stops compensating in the dark so 'lights off' really looks dark
    var lr = Math.max(L / un.day, 1e-7), adapt = lr >= 0.05 ? Math.pow(lr, 0.75) : Math.pow(0.05, 0.75) * Math.pow(lr / 0.05, 0.35);
    var exp = 0.46 / adapt / un.day;
    cav = norm(cav.map(function (v) { return Math.max(v, 1e-9); }));
    var wb = norm(cav.map(function (v) { return 1 / Math.pow(Math.max(v, 1e-4), 0.6); }));
    return { exp: exp, wb: wb };
  };

  Viz.prototype.draw = function () {
    if (!this.cur || !this.w) return;
    var gl = this.gl, u = this.u, r = this.rooms[this.state.room], w = this.w, ex = this.exposure(w, r);
    this.cur.forEach(function (t, k) { this.bindTex(t, k); }, this);
    this.bindTex(this.chipTex, 5); this.bindTex(this.prevTex || this.chipTex, 6);
    var W = [], G = [];
    for (var i = 0; i < 6; i++) for (var j = 0; j < 3; j++) {
      var base = w[i][j] * ex.exp * ex.wb[j];
      W.push(base * r.bgScale[i]); G.push(base * r.glScale[i]);
    }
    gl.uniform3fv(u.uW, W); gl.uniform3fv(u.uG, G);
    var m = r.floor;
    gl.uniformMatrix3fv(u.uM, false, [m[0], m[3], m[6], m[1], m[4], m[7], m[2], m[5], m[8]]);
    gl.uniform2f(u.uSize, r.W, r.H); gl.uniform4f(u.uCrop, r.crop[0], r.crop[1], r.crop[2], r.crop[3]);
    gl.uniform1f(u.uTile, r.tile); gl.uniform1f(u.uWipe, this.wipe || 0);
    gl.uniform1f(u.uGlossK, this.lastBare ? 0.1 : 1.0); gl.uniform1f(u.uPrevGlossK, this.prevBare ? 0.1 : 1.0);
    gl.viewport(0, 0, this.canvas.width, this.canvas.height);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  };

  Viz.prototype.animateWipe = function () {
    var self = this, t0 = performance.now(), ms = 1100;
    cancelAnimationFrame(this.rafW);
    if (reduce) { this.prevTex = null; this.wipe = 0; this.draw(); return; }
    this.wipe = 0.0001;
    (function tick(t) {
      var p = Math.min(1, (t - t0) / ms);
      self.wipe = p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2; self.draw();
      if (p < 1) self.rafW = requestAnimationFrame(tick); else { self.prevTex = null; self.prevBare = self.lastBare; self.wipe = 0; self.draw(); }
    })(t0);
  };

  Viz.prototype.setRoom = function (i, first) {
    var self = this, r = this.rooms[i];
    this.state.room = i;
    (this.roomBtns || []).forEach(function (b, k) { b.setAttribute('aria-pressed', String(k === i)); });
    var cn = this.q('.viz-ceil-name'); if (cn) cn.textContent = r.ceiling;
    var ln = this.q('.viz-lamps-name'); if (ln) ln.textContent = r.lamps;
    if (this.poster) { this.poster.src = this.base + r.key + '-poster.jpg'; this.poster.alt = r.name + ' with a Domino chip floor in afternoon light'; }
    if (!this.gl) { this.announce(); return Promise.resolve(); }
    this.stage.classList.add('loading');
    var want = this.state.bare ? CONCRETE : this.state.blend;
    return Promise.all([this.loadRoom(i), this.chip(want)]).then(function (res) {
      if (self.state.room !== i) return;
      self.cur = res[0]; self.chipTex = res[1]; self.lastBare = self.prevBare = self.state.bare; self.prevTex = null; self.wipe = 0;
      self.canvas.width = r.W; self.canvas.height = r.H;
      self.stage.style.aspectRatio = r.W + ' / ' + r.H;
      self.w = null; self.fadeLights(0);
      self.stage.classList.remove('loading'); self.stage.classList.add('ready');
      self.announce();
      if (first) self.root.dispatchEvent(new CustomEvent('viz:ready'));
    });
  };

  Viz.prototype.swapChip = function (name) {
    var self = this;
    this.chip(name).then(function (t) {
      var want = self.state.bare ? CONCRETE : self.state.blend;
      if (want !== name || !self.cur) return;
      self.prevTex = self.chipTex; self.prevBare = self.lastBare; self.chipTex = t; self.lastBare = self.state.bare;
      self.animateWipe();
    });
  };

  Viz.prototype.setBlend = function (name) {
    if (name === this.state.blend && !this.state.bare) return;
    this.state.blend = name;
    try { sessionStorage.setItem('ccBlend', name); sessionStorage.setItem('ccBlendPicked', '1'); } catch (e) {}
    this.tiles.forEach(function (t) { t.setAttribute('aria-pressed', String(t.dataset.blend === name)); });
    this.showBlend();
    this.root.dispatchEvent(new CustomEvent('viz:blend', { detail: name, bubbles: true }));
    this.state.bare = false; this.syncControls(); this.announce();
    if (this.gl && this.cur) this.swapChip(name);
  };

  Viz.prototype.setBare = function (on) {
    this.state.bare = on; this.syncControls(); this.announce();
    if (this.gl && this.cur) this.swapChip(on ? CONCRETE : this.state.blend);
  };

  Viz.prototype.noGL = function () {
    this.stage.classList.add('nogl');
    if (this.status) this.status.textContent = 'This browser can’t run the visualizer, so you’re seeing a still picture. Tap a sample to see the blend up close.';
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
