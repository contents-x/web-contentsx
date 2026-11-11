/* Creative X landing — showreel HERO whose picture is the shared background of the stage
   (css/service-creative-hero.css): HERO, WORKS, 01 CREATIVE SOLUTION and 02 PRODUCTION FLOW sit on one layer
   (.cxg-reel: poster <img> + muted <video>), so the video is fetched and played once. The video source:
     1. The WordPress slot `cx-creative-hero` (cxWorks.slot, js/cx-works.js): up to three MP4s from the
        WordPress media library (cms.contentsx.jp/wp-content/uploads, ASCII file names), played in
        WordPress order and round again (one video loops); the first card's `thumb` becomes the poster.
     2. The slot is empty (200, no items: nothing chosen in WordPress), fails or answers later than WP_WAIT:
        `data-sources` (tools/build-services.py from data/service-groups.json heroMedia.videos, the site's
        own reel, none today), else the poster stays with the same scroll effect. No other work is used.
     3. The slot is missing (404, a WordPress without the Creative X slots yet): the older place,
        「CREATIVE X ビューワー動画」 rows of type `data-wp-type` (creative_hero) with an .mp4, then 2.
   Scroll (passive listener + one rAF): the copy fades and rises, its shade goes with it; the picture blurs
   (clear glass, not a navy fill: a light veil, a glass sheen, a little more colour) and zooms a little until
   WORKS reaches the top, then stays like that to the end of the stage, a little calmer (more veil) behind
   02 PRODUCTION FLOW ([data-cxg-calm]) and after. The video pauses when the stage is off screen, the tab is hidden,
   the work viewer is open (cxworks:viewer from js/cx-works.js), the visitor pressed pause, or a text-heavy section
   ([data-cxg-still], 03 FAQ / CONTACT) covers the middle of the screen: the picture is held still behind it.
   Reduced motion: no video and no scroll-linked change; the poster switches once from sharp to blurred.
   Save-Data / 2G: the scroll effect on the poster, no video. */
(function () {
  'use strict';
  var stage = document.querySelector('[data-cxg-stage]');
  var reel = stage && stage.querySelector('[data-cxg-reel]');
  var hero = stage && stage.querySelector('.cxg-reel-hero');
  var calmEl = stage && stage.querySelector('[data-cxg-calm]');
  var stillEl = stage && stage.querySelector('[data-cxg-still]');
  var video = reel && reel.querySelector('video');
  var toggle = hero && hero.querySelector('[data-cxg-reel-toggle]');
  if (!reel || !hero || !video || !toggle) return;

  var LOCAL = /^\/material\/[\w\/-]+\.(?:mp4|webm)$/;
  var REMOTE = /^https:\/\/cms\.contentsx\.jp\/wp-content\/uploads\/[\w\/.-]+\.(?:mp4|webm)$/;
  var WP_WAIT = 2500;   // the poster is already showing; do not hold the video longer for WordPress
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  var narrow = window.matchMedia('(max-width: 768px)');
  // Tuned on the real poster and video: a clear blur that keeps the picture's colour and light.
  var BLUR = { pc: 22, sp: 14 };       // px at the end of the HERO
  var VEIL = 0.3, CALM = 0.14;         // ink veil behind the sections / extra behind PRODUCTION FLOW
  var live = false, inView = true, viewerOpen = false, userPaused = false, still = false, hasVideo = false, requested = false;
  var ticking = false;
  var written = {};

  function clamp(v) { return v < 0 ? 0 : v > 1 ? 1 : v; }
  function setVar(node, name, value) {
    if (written[name] === value) return;
    written[name] = value;
    node.style.setProperty(name, value);
  }

  /* ---------- scroll ---------- */
  function frame() {
    ticking = false;
    if (!live) return;
    var vh = window.innerHeight;
    var h = hero.getBoundingClientRect();
    var y = Math.max(0, -h.top);
    var copy = clamp((y - h.height * 0.02) / (h.height * 0.3));
    var blur = clamp((y - h.height * 0.06) / (h.height * 0.7));
    var calm = calmEl ? clamp((vh - calmEl.getBoundingClientRect().top) / (vh * 0.6)) : 0;
    if (stillEl) { var sr = stillEl.getBoundingClientRect(); still = sr.top < vh * 0.5 && sr.bottom > vh * 0.5; }
    // Reduced motion: the copy stays, and the picture switches once (sharp → blurred, then calmer).
    if (reduced.matches) { copy = 0; blur = y > h.height * 0.5 ? 1 : 0; calm = calm > 0.5 ? 1 : 0; }
    setVar(hero, '--cxg-copy', (1 - copy).toFixed(3));
    setVar(reel, '--cxg-shade', (reduced.matches ? 1 - blur : 1 - copy).toFixed(3));
    setVar(reel, '--cxg-blur', (blur * (narrow.matches ? BLUR.sp : BLUR.pc)).toFixed(1) + 'px');
    setVar(reel, '--cxg-glass', blur.toFixed(3));
    setVar(reel, '--cxg-veil', (blur * VEIL + calm * CALM).toFixed(3));
    setVar(reel, '--cxg-zoom', (1 + blur * 0.06).toFixed(4));
    reel.classList.toggle('is-sharp', blur === 0);
    stage.classList.toggle('is-copy-gone', copy > 0.95);
    playback();
  }
  function request() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(frame);
  }
  function setLive(on) {
    live = on;
    stage.classList.toggle('is-live', on);
    if (on) { request(); return; }
    ['--cxg-blur', '--cxg-veil', '--cxg-zoom', '--cxg-glass', '--cxg-shade'].forEach(function (name) { reel.style.removeProperty(name); });
    hero.style.removeProperty('--cxg-copy');
    written = {};
    reel.classList.remove('is-sharp');
    stage.classList.remove('is-copy-gone');
  }

  /* ---------- video ---------- */
  function playback() {
    if (!hasVideo) return;
    var run = live && inView && !viewerOpen && !userPaused && !still && !document.hidden;
    if (run && video.paused) video.play().catch(function () {});
    else if (!run && !video.paused) video.pause();
  }
  function staticSources() {
    try {
      var list = JSON.parse(reel.getAttribute('data-sources') || '[]');
      return Array.isArray(list) ? list : [];
    } catch (e) { return []; }
  }
  function wpSources(data) {
    var type = reel.getAttribute('data-wp-type');
    var rows = (data && Array.isArray(data.viewer) ? data.viewer : []).filter(function (v) {
      return v && v.type === type && v.provider === 'mp4' && REMOTE.test(String(v.src || ''));
    });
    if (!rows.length) return [];
    var list = [{ src: rows[0].src, type: 'video/mp4' }];
    if (rows[1]) list.unshift({ src: rows[1].src, type: 'video/mp4', media: '(max-width: 768px)' });
    return list;
  }
  /** The first source that is allowed, matches the screen and can be played here; '' if none. */
  function pick(list) {
    for (var i = 0; i < list.length; i++) {
      var s = list[i] || {};
      var src = String(s.src || '');
      if (!LOCAL.test(src) && !REMOTE.test(src)) continue;
      if (s.media && !window.matchMedia(s.media).matches) continue;
      if (s.type && !video.canPlayType(s.type)) continue;
      return src;
    }
    return '';
  }
  function fail() {
    hasVideo = false;
    reel.classList.remove('is-playing');
    toggle.hidden = true;
    video.removeAttribute('src');
  }
  /* Up to three videos play in turn (WordPress order) and the list starts again; one video loops.
     A file that cannot be played is dropped and the next one plays; with none left, the poster stays. */
  var reelList = [], reelAt = 0;
  function cue() {
    video.loop = reelList.length === 1;
    video.src = reelList[reelAt];
    playback();
  }
  function start(list) {
    reelList = (list || []).filter(Boolean);
    if (!reelList.length) return;
    reelAt = 0;
    hasVideo = true;
    video.addEventListener('playing', function () {
      if (reduced.matches) return;
      reel.classList.add('is-playing');
      toggle.hidden = false;
    });
    video.addEventListener('ended', function () {
      if (reelList.length < 2) return;
      reelAt = (reelAt + 1) % reelList.length;
      cue();
    });
    video.addEventListener('error', function () {
      reelList.splice(reelAt, 1);
      if (!reelList.length) { fail(); return; }
      reelAt %= reelList.length;
      cue();
    });
    cue();
  }
  /** WordPress's still for the first video replaces the built-in poster once it has loaded (no blank frame). */
  function usePoster(src) {
    var poster = reel.querySelector('.cxg-reel__poster');
    src = window.cxDom && window.cxDom.safeImage(src);
    if (!poster || !src || poster.getAttribute('src') === src) return;
    var img = new Image();
    img.onload = function () { poster.src = src; };
    img.src = src;
  }
  function quiet() {
    var c = navigator.connection;
    return !!(c && (c.saveData || /(^|-)2g$/.test(c.effectiveType || '')));
  }
  function load() {
    if (requested || quiet()) return;
    requested = true;
    var fallback = function () { start([pick(staticSources())]); };
    var wp = typeof WP_CONFIG !== 'undefined' && WP_CONFIG.enabled !== false && WP_CONFIG.apiBase && window.cxDom && window.cxWorks;
    if (!wp) { fallback(); return; }
    var late = new Promise(function (resolve) { setTimeout(function () { resolve({ state: 'late', items: [] }); }, WP_WAIT); });
    Promise.race([window.cxWorks.slot('cx-creative-hero'), late]).then(function (res) {
      if (res.state === 'ok') {
        // Only MP4s in the WordPress media library (the slot sends no other kind), in WordPress order.
        var list = res.items.filter(function (it) { return it.media && REMOTE.test(it.media.src) && (!video.canPlayType || video.canPlayType('video/mp4')); }).slice(0, 3);
        if (list.length) { usePoster(list[0].poster); start(list.map(function (it) { return it.media.src; })); return; }
      }
      if (res.state === 'missing' && reel.getAttribute('data-wp-type')) {
        // A WordPress without the Creative X slots yet: the older place (the WORKS fallback asks for the same list).
        window.cxDom.getJSON('/bizanime-videos', 8000, 'Creative X HERO').then(function (d) {
          var src = pick(wpSources(d));
          if (src) start([src]); else fallback();
        });
        return;
      }
      fallback();     // empty (nothing set in WordPress), failed or late: the poster, or the site's own reel
    });
  }

  toggle.addEventListener('click', function () {
    userPaused = !userPaused;
    toggle.setAttribute('data-paused', String(userPaused));
    toggle.setAttribute('aria-label', userPaused ? '背景の動画を再生' : '背景の動画を一時停止');
    playback();
  });

  /* ---------- mode ---------- */
  function apply() {
    setLive(true);
    written = {};
    request();
    if (!reduced.matches) { load(); playback(); return; }
    if (hasVideo) video.pause();
    reel.classList.remove('is-playing');
    toggle.hidden = true;
  }
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (entries) {
      inView = entries[entries.length - 1].isIntersecting;
      playback();
    }).observe(stage);
  }
  document.addEventListener('visibilitychange', playback);
  // The work viewer covers the page: the background video does not play behind it.
  document.addEventListener('cxworks:viewer', function (e) { viewerOpen = !!(e.detail && e.detail.open); playback(); });
  window.addEventListener('scroll', request, { passive: true });
  window.addEventListener('resize', request);
  window.addEventListener('load', request);
  if (reduced.addEventListener) reduced.addEventListener('change', apply);
  else if (reduced.addListener) reduced.addListener(apply);
  apply();
})();
