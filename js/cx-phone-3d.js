/* cx-phone-3d — the 3D phone of the Creative X work viewer (js/cx-works.js, css/cx-works.css; 2026-11).
   An ES module, loaded with import() when a video work is opened (or when the visitor points at an open
   button), never on page load.
   Dependency: three.js r170 only — js/vendor/three/three.module.min.js, the unchanged build/three.module.min.js
   of npm three@0.170.0 (MIT, js/vendor/three/LICENSE; tarball sha512 checked against the npm registry,
   see SPEC.md §3.0). No add-ons, no CDN, no eval: the page CSP (script-src 'self') is enough.

   The phone lies on its side: metal side frame with rounded edges, black glass front and bezel, front camera
   and earpiece, power and volume keys, USB-C port and speaker holes on the short side, antenna bands and a
   soft shadow, lit by a small studio environment (PMREM) for reflections on the metal and glass.
   The scene is laid out in CSS pixels: at z = 0 one unit is one CSS pixel. The 3D screen is built from the
   rectangle and radius of the HTML screen element (`screen`, where the player lives), so when the phone is
   straight on, the 3D screen and the player are the same rectangle. While the phone comes in (tilted →
   straight on, ENTER_MS) its screen shows the work's poster; then onSettle() lets the caller show the
   player on top, and nothing is drawn again except after a resize or scroll. The YouTube player is never
   drawn into WebGL: it stays the real <iframe>, with all its controls.
   Reduced motion: no entrance, the phone is drawn straight on at once.

   mount({ host, frame, screen, poster, reduced, onSettle, onLost }) → { destroy() } or null
     host    the element the canvas covers (the dialog, fixed to the screen)
     frame   the CSS phone's frame box (outer size and corner radius of the body)
     screen  the player's box
     null when WebGL2 is missing or would run in software (failIfMajorPerformanceCaveat), or on any error:
     the caller keeps its CSS phone. onLost() is called if the GPU drops the context later. */
import * as THREE from './vendor/three/three.module.min.js';

var ENTER_MS = 900;
var FOV = 30;                  // degrees: a calm perspective
var MAX_PIXELS = 4e6;          // device pixels per frame; the pixel ratio is lowered on big screens

function clamp(v, lo, hi) { return v < lo ? lo : v > hi ? hi : v; }
/** Ease in and out: the tilted phone is seen while it fades in, then turns and slows into place. */
function ease(t) { return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }

/** A rectangle centred on 0 with circular corners (CSS border-radius). */
function roundedRect(w, h, r) {
  r = clamp(r, 0, Math.min(w, h) / 2);
  var x = -w / 2, y = -h / 2, s = new THREE.Shape();
  s.moveTo(x + r, y);
  s.lineTo(x + w - r, y);
  if (r) s.absarc(x + w - r, y + r, r, -Math.PI / 2, 0, false);
  s.lineTo(x + w, y + h - r);
  if (r) s.absarc(x + w - r, y + h - r, r, 0, Math.PI / 2, false);
  s.lineTo(x + r, y + h);
  if (r) s.absarc(x + r, y + h - r, r, Math.PI / 2, Math.PI, false);
  s.lineTo(x, y + r);
  if (r) s.absarc(x + r, y + r, r, Math.PI, Math.PI * 1.5, false);
  return s;
}

/** A dim studio for reflections: dark room, a soft box above, strip lights at the sides, a warm bounce. */
function studio(renderer) {
  var env = new THREE.Scene();
  var parts = [];
  function add(geometry, color, side) {
    var mesh = new THREE.Mesh(geometry, new THREE.MeshBasicMaterial({ color: color, side: side || THREE.DoubleSide }));
    parts.push(mesh);
    env.add(mesh);
    return mesh;
  }
  add(new THREE.BoxGeometry(30, 20, 30), new THREE.Color(0.1, 0.11, 0.13), THREE.BackSide);
  [[new THREE.Color(7, 7, 7), [0, 8, 7], [14, 4]],
   [new THREE.Color(3.2, 3.3, 3.6), [-12, 2, 3], [2.4, 11]],
   [new THREE.Color(2.6, 2.7, 3), [12, 1, 3], [2.4, 11]],
   [new THREE.Color(1.6, 0.75, 0.35), [0, -9, 5], [16, 3]]].forEach(function (p) {
    var m = add(new THREE.PlaneGeometry(p[2][0], p[2][1]), p[0]);
    m.position.set(p[1][0], p[1][1], p[1][2]);
    m.lookAt(0, 0, 0);
  });
  var pmrem = new THREE.PMREMGenerator(renderer);
  var target = pmrem.fromScene(env, 0.035);
  pmrem.dispose();
  parts.forEach(function (m) { m.geometry.dispose(); m.material.dispose(); });
  return target;
}

function shadowTexture() {
  var c = document.createElement('canvas');
  c.width = c.height = 128;
  var ctx = c.getContext('2d');
  var g = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
  g.addColorStop(0, 'rgba(0,0,0,.6)');
  g.addColorStop(0.5, 'rgba(0,0,0,.3)');
  g.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 128, 128);
  return new THREE.CanvasTexture(c);
}

export function mount(opts) {
  var host = opts.host, frameEl = opts.frame, screenEl = opts.screen;
  var canvas = document.createElement('canvas');
  canvas.className = 'cxwv-gl';
  canvas.setAttribute('aria-hidden', 'true');
  var gl = canvas.getContext('webgl2', { alpha: true, antialias: true, premultipliedAlpha: true, failIfMajorPerformanceCaveat: true, powerPreference: 'high-performance' });
  if (!gl) return null;
  var renderer;
  try {
    renderer = new THREE.WebGLRenderer({ canvas: canvas, context: gl, alpha: true, antialias: true });
  } catch (e) { return null; }
  renderer.setClearColor(0x000000, 0);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  host.insertBefore(canvas, host.firstChild);

  var dead = false, raf = 0, started = 0, settled = false, dirty = false, compiling = null;
  var scene = new THREE.Scene();
  var envTarget = studio(renderer);
  scene.environment = envTarget.texture;
  var key = new THREE.DirectionalLight(0xffffff, 1.6);
  key.position.set(-0.6, 1, 1.4);
  scene.add(key);
  var rim = new THREE.DirectionalLight(0xdfe8ff, 0.9);
  rim.position.set(1.2, -0.2, 0.4);
  scene.add(rim);
  var camera = new THREE.PerspectiveCamera(FOV, 1, 1, 10000);

  /* ---------- materials ---------- */
  var metal = new THREE.MeshPhysicalMaterial({ color: 0xb4bac4, metalness: 1, roughness: 0.26, clearcoat: 0.4, clearcoatRoughness: 0.15, envMapIntensity: 1.35 });
  var glass = new THREE.MeshPhysicalMaterial({ color: 0x040507, metalness: 0, roughness: 0.08, clearcoat: 1, clearcoatRoughness: 0.04 });
  var matte = new THREE.MeshStandardMaterial({ color: 0x050506, metalness: 0, roughness: 0.7 });
  var band = new THREE.MeshStandardMaterial({ color: 0x2b2e34, metalness: 0.2, roughness: 0.55 });
  var lens = new THREE.MeshPhysicalMaterial({ color: 0x0b1424, metalness: 0.2, roughness: 0.1, clearcoat: 1 });
  var ring = new THREE.MeshStandardMaterial({ color: 0x1b1e25, metalness: 0.6, roughness: 0.35 });
  // The screen: the poster (contain, as the player shows a 16:9 video) under a clear coat that catches the light.
  var poster = document.createElement('canvas');
  var first = screenEl.getBoundingClientRect();
  poster.width = 1024;
  poster.height = Math.round(clamp(1024 * first.height / Math.max(1, first.width), 256, 1024));
  var pctx = poster.getContext('2d');
  idle();
  var screenTex = new THREE.CanvasTexture(poster);
  screenTex.colorSpace = THREE.SRGBColorSpace;
  var screenMat = new THREE.MeshPhysicalMaterial({ color: 0x000000, emissive: 0xffffff, emissiveMap: screenTex, roughness: 0.06, metalness: 0, clearcoat: 1, clearcoatRoughness: 0.03, toneMapped: false });
  var shadowTex = shadowTexture();
  var shadow = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: shadowTex, transparent: true, depthWrite: false, opacity: 0 }));
  scene.add(shadow);
  var phone = new THREE.Group();      // origin: the centre of the screen, on the glass
  scene.add(phone);

  /* ---------- poster ---------- */
  var img = null;
  var posterReady = new Promise(function (resolve) {
    if (!opts.poster) { resolve(); return; }
    img = new Image();
    img.crossOrigin = 'anonymous';
    img.decoding = 'async';
    img.onload = function () {
      // YouTube answers a missing maxresdefault with a 120×90 grey picture: use hqdefault instead.
      if (img.naturalWidth <= 120 && /\/maxresdefault\.jpg$/.test(img.src)) { img.src = img.src.replace(/maxresdefault\.jpg$/, 'hqdefault.jpg'); return; }
      drawPoster();
      resolve();
    };
    img.onerror = function () { resolve(); };
    img.src = opts.poster;
  });
  /** The screen before (or without) a picture: a dim glow and a play mark, never a black slab. Used when the
      work has no picture WebGL may read (the caller passes only CORS-safe hosts) or it fails to load. */
  function idle() {
    var w = poster.width, h = poster.height, g = pctx.createRadialGradient(w / 2, h * 0.45, h * 0.05, w / 2, h / 2, w * 0.62);
    g.addColorStop(0, '#26355f');
    g.addColorStop(0.55, '#111a36');
    g.addColorStop(1, '#070b18');
    pctx.fillStyle = g;
    pctx.fillRect(0, 0, w, h);
    var r = h * 0.11;
    pctx.lineWidth = Math.max(2, r * 0.08);
    pctx.strokeStyle = 'rgba(255,255,255,.55)';
    pctx.beginPath();
    pctx.arc(w / 2, h / 2, r, 0, Math.PI * 2);
    pctx.stroke();
    pctx.fillStyle = 'rgba(255,255,255,.7)';
    pctx.beginPath();
    pctx.moveTo(w / 2 - r * 0.32, h / 2 - r * 0.45);
    pctx.lineTo(w / 2 + r * 0.5, h / 2);
    pctx.lineTo(w / 2 - r * 0.32, h / 2 + r * 0.45);
    pctx.closePath();
    pctx.fill();
  }
  function drawPoster() {
    if (dead || !img || !img.naturalWidth) return;
    var sw = img.naturalWidth, sh = img.naturalHeight, sy = 0;
    // hqdefault is 4:3 with the bars of a 16:9 video baked in: keep the picture only.
    if (/\/hqdefault\.jpg$/.test(img.src) && sw * 3 === sh * 4) { sy = (sh - sw * 9 / 16) / 2; sh = sw * 9 / 16; }
    var w = poster.width, h = poster.height, k = Math.min(w / sw, h / sh);
    pctx.fillStyle = '#000';
    pctx.fillRect(0, 0, w, h);
    try { pctx.drawImage(img, 0, sy, sw, sh, (w - sw * k) / 2, (h - sh * k) / 2, sw * k, sh * k); } catch (e) { return; }
    screenTex.needsUpdate = true;
  }

  /* ---------- layout (CSS pixels) ---------- */
  var m = null, built = '';
  function measure() {
    var hr = host.getBoundingClientRect(), sr = screenEl.getBoundingClientRect(), fr = frameEl.getBoundingClientRect();
    return {
      w: hr.width, h: hr.height,
      x: sr.left + sr.width / 2 - (hr.left + hr.width / 2),            // screen centre from the canvas centre, y up
      y: hr.top + hr.height / 2 - (sr.top + sr.height / 2),
      sw: sr.width, sh: sr.height, sr: parseFloat(getComputedStyle(screenEl).borderTopLeftRadius) || 0,
      fw: fr.width, fh: fr.height, fr: parseFloat(getComputedStyle(frameEl).borderTopLeftRadius) || 0,
      ox: fr.left + fr.width / 2 - (sr.left + sr.width / 2),          // frame centre from the screen centre
      oy: sr.top + sr.height / 2 - (fr.top + fr.height / 2)
    };
  }
  function clear() {
    for (var i = phone.children.length - 1; i >= 0; i--) {
      var o = phone.children[i];
      phone.remove(o);
      if (o.geometry) o.geometry.dispose();
      if (o.isInstancedMesh) o.dispose();
    }
  }
  function mesh(geometry, material, x, y, z) {
    var o = new THREE.Mesh(geometry, material);
    o.position.set(x || 0, y || 0, z || 0);
    phone.add(o);
    return o;
  }
  function build() {
    clear();
    var D = clamp(m.fw * 0.056, 7, 66);                      // a real phone: about 8 mm on 147 mm
    var b = Math.max(1, Math.min((m.fw - m.sw) / 2, (m.fh - m.sh) / 2));
    var s = Math.min(D * 0.16, b * 0.45);                    // the metal edge seen from the front
    var t = D * 0.22;
    var zMid = -D / 2 - 0.6;
    var left = m.ox - m.fw / 2, right = m.ox + m.fw / 2, top = m.oy + m.fh / 2, bottom = m.oy - m.fh / 2;
    // Body: caps (front bezel and back) in black glass, sides and rounded edges in metal.
    var body = new THREE.ExtrudeGeometry(roundedRect(m.fw - 2 * s, m.fh - 2 * s, Math.max(0, m.fr - s)),
      { depth: Math.max(0.1, D - 2 * t), bevelEnabled: true, bevelThickness: t, bevelSize: s, bevelSegments: 8, curveSegments: 32 });
    body.translate(m.ox, m.oy, -(D - t) - 0.6);              // front just behind the glass plane, back at -D
    mesh(body, [glass, metal]);
    // Screen on the glass plane (z = 0): the player's rectangle.
    var sg = new THREE.ShapeGeometry(roundedRect(m.sw, m.sh, m.sr), 24);
    var uv = sg.attributes.uv, pos = sg.attributes.position;
    for (var i = 0; i < uv.count; i++) uv.setXY(i, pos.getX(i) / m.sw + 0.5, pos.getY(i) / m.sh + 0.5);
    mesh(sg, screenMat);
    // Front camera and earpiece in the bezel at the left (the phone's top).
    var bezelX = (left + s - m.sw / 2) / 2;
    var cr = clamp(b * 0.2, 1.2, 4.5);
    var slit = m.sh * 0.17;
    mesh(new THREE.ShapeGeometry(roundedRect(clamp(b * 0.16, 0.8, 2.6), slit, 2), 6), matte, bezelX, 0, -0.3);
    mesh(new THREE.RingGeometry(cr, cr * 1.45, 32), ring, bezelX, slit / 2 + cr * 3, -0.35);
    mesh(new THREE.CircleGeometry(cr, 32), lens, bezelX, slit / 2 + cr * 3, -0.3);
    // Keys on the long edges: power on the top, volume on the bottom (CSS phone: 20% / 15% / 23%).
    var keyH = D * 0.34, keyP = clamp(D * 0.06, 1.2, 3.2);
    function sideKey(from, len, onTop) {
      var g = new THREE.ExtrudeGeometry(roundedRect(len * m.fw, keyH, keyH / 2),
        { depth: keyP, bevelEnabled: true, bevelThickness: keyP * 0.3, bevelSize: Math.min(keyH * 0.15, 1.2), bevelSegments: 3, curveSegments: 12 });
      g.rotateX(onTop ? -Math.PI / 2 : Math.PI / 2);         // extrude outwards from the edge
      mesh(g, metal, left + (from + len / 2) * m.fw, onTop ? top - keyP * 0.5 : bottom + keyP * 0.5, zMid);
    }
    sideKey(0.20, 0.09, true);
    sideKey(0.15, 0.065, false);
    sideKey(0.23, 0.065, false);
    // Antenna bands where the long edges meet the corners.
    [[left + m.fr * 1.15, true], [right - m.fr * 1.15, true], [left + m.fr * 1.15, false], [right - m.fr * 1.15, false]].forEach(function (a) {
      var g = new THREE.PlaneGeometry(clamp(D * 0.06, 1, 2.4), D - 2 * t);
      g.rotateX(a[1] ? -Math.PI / 2 : Math.PI / 2);
      mesh(g, band, a[0], a[1] ? top + 0.15 : bottom - 0.15, zMid);
    });
    // The short edge at the right (the phone's bottom): USB-C port between two rows of speaker holes.
    var port = new THREE.ShapeGeometry(roundedRect(D * 0.3, m.fh * 0.12, D * 0.15), 8);
    port.rotateY(Math.PI / 2);
    mesh(port, matte, right + 0.15, m.oy, zMid);
    var holeR = D * 0.05;
    var hole = new THREE.CircleGeometry(holeR, 10);
    hole.rotateY(Math.PI / 2);
    var holes = new THREE.InstancedMesh(hole, matte, 12);
    var at = new THREE.Matrix4();
    for (var n = 0; n < 6; n++) {
      var dy = m.fh * 0.06 + holeR * 3 + n * holeR * 3.2;
      holes.setMatrixAt(n, at.makeTranslation(right + 0.15, m.oy + dy, zMid));
      holes.setMatrixAt(n + 6, at.makeTranslation(right + 0.15, m.oy - dy, zMid));
    }
    phone.add(holes);
    // Soft shadow on the backdrop, below and behind.
    shadow.scale.set(m.fw * 1.22, m.fh * 1.05, 1);
    built = [m.sw, m.sh, m.sr, m.fw, m.fh, m.fr].map(Math.round).join(',');
  }
  function layout() {
    m = measure();
    var key2 = [m.sw, m.sh, m.sr, m.fw, m.fh, m.fr].map(Math.round).join(',');
    if (key2 !== built) build();
    var ratio = Math.min(window.devicePixelRatio || 1, 2);
    ratio = Math.min(ratio, Math.sqrt(MAX_PIXELS / Math.max(1, m.w * m.h)));
    renderer.setPixelRatio(ratio);
    renderer.setSize(m.w, m.h, false);
    camera.aspect = m.w / Math.max(1, m.h);
    camera.position.set(0, 0, (m.h / 2) / Math.tan(THREE.MathUtils.degToRad(FOV / 2)));
    camera.near = camera.position.z / 20;
    camera.far = camera.position.z * 4;
    camera.updateProjectionMatrix();
  }
  /** p: 0 = tilted and further away, 1 = straight on, where the player is. */
  function pose(p) {
    var q = 1 - p, wide = m.w > 768;
    phone.rotation.set((wide ? 0.24 : 0.14) * q, (wide ? -0.62 : -0.32) * q, -0.05 * q);
    phone.position.set(m.x + q * m.fw * 0.04, m.y - q * m.fh * 0.06, -q * m.fw * (wide ? 0.35 : 0.34));
    shadow.position.set(m.x, m.y - m.fh * 0.09, -Math.max(20, m.fw * 0.06) - q * m.fw * 0.2);
    shadow.material.opacity = p;
    canvas.style.opacity = String(Math.min(1, p * 4));
  }
  function draw() { if (!dead) renderer.render(scene, camera); }

  /* ---------- entrance ---------- */
  function tick(now) {
    if (dead) return;
    if (!started) started = now;
    var t = Math.min(1, (now - started) / ENTER_MS);
    pose(ease(t));
    draw();
    if (t < 1) { raf = requestAnimationFrame(tick); return; }
    raf = 0;
    settle();
  }
  function settle() {
    settled = true;
    layout();                                   // the final rectangle, measured again
    pose(1);
    draw();
    if (opts.onSettle) opts.onSettle();
    // Under the player the 3D screen goes dark, so no poster edge can show around it.
    setTimeout(function () { if (dead) return; screenMat.emissive.setHex(0x000000); draw(); }, 320);
  }
  function onChange() {
    if (dead || dirty) return;
    dirty = true;
    requestAnimationFrame(function () {
      dirty = false;
      if (dead || !settled) return;             // the entrance measures again when it ends
      layout();
      pose(1);
      draw();
    });
  }
  function onLost(e) {
    e.preventDefault();
    if (dead) return;
    destroy();
    if (opts.onLost) opts.onLost();
  }

  function destroy() {
    if (dead) return;
    dead = true;
    cancelAnimationFrame(raf);
    window.removeEventListener('resize', onChange);
    host.removeEventListener('scroll', onChange, true);
    canvas.removeEventListener('webglcontextlost', onLost);
    if (img) { img.onload = img.onerror = null; img.removeAttribute('src'); }
    canvas.remove();
    // compileAsync polls the shader programs until they are ready: release the GPU objects after it ends.
    if (compiling) compiling.then(release, release);
    else release();
  }
  function release() {
    clear();
    shadow.geometry.dispose();
    [metal, glass, matte, band, lens, ring, screenMat, shadow.material].forEach(function (mat) { mat.dispose(); });
    screenTex.dispose();
    shadowTex.dispose();
    envTarget.dispose();
    renderer.dispose();
    renderer.forceContextLoss();
  }

  try {
    layout();
    pose(opts.reduced ? 1 : 0);
  } catch (e) {
    destroy();
    return null;
  }
  window.addEventListener('resize', onChange);
  host.addEventListener('scroll', onChange, true);
  canvas.addEventListener('webglcontextlost', onLost);
  // Shaders compile before the first frame, and the poster gets a moment: the entrance then runs smoothly.
  var compiled = renderer.compileAsync ? renderer.compileAsync(scene, camera) : Promise.resolve();
  compiling = compiled;
  compiled.then(function () { compiling = null; }, function () { compiling = null; });
  Promise.all([compiled, Promise.race([posterReady, new Promise(function (r) { setTimeout(r, 350); })])]).then(function () {
    if (dead) return;
    if (opts.reduced) { settle(); return; }
    raf = requestAnimationFrame(tick);
  }, function () { if (!dead) settle(); });
  return { destroy: destroy };
}
