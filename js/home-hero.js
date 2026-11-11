/* HERO Creative card (Issue #108; picture-only card since Issue #114).
   - The card shows the videos' pictures (YouTube thumbnails) and its own line; the three pictures
     sit in one row that scrolls sideways (swipe / trackpad). The picture in view slowly zooms in.
   - PC moving preview (2026-10-10, same method as bizmanga.contentsx.jp/bizanime, chosen by the site
     owner knowing it hides YouTube's own overlay): once the page has loaded and while the card is in
     view, a muted, looping, control-less YouTube player starts behind the picture in view. The
     picture stays on top for REVEAL_MS (YouTube shows its title at start-up) and then fades out.
     The player cannot be pointed at or clicked (so YouTube's overlay never returns); a click opens
     the card. The next video comes in every PREVIEW_ADVANCE_MS (paused on hover). Phones/tablets,
     reduced motion, a hidden tab or a Hero scrolled away keep the still pictures.
   - Pressing a picture opens the video: PC moves the card to the centre of the Hero's right half at
     about 1.5× (smaller if it would not fit) with ‹ › and × outside the picture; tablet/SP open it in
     place across the card area with ‹ › × below. Only then is the YouTube player loaded, with sound
     (falls back to muted when the browser blocks it) and YouTube's own controls. Scrolling sideways,
     ‹ › or ← → move to the other videos; Esc / × closes.
   - Leaving the Hero (scrolling on, js/hero-about.js), hiding the tab or closing stops the player.
     Only one player exists at a time.
   Videos are the [data-cxhv-slide] elements in index.html (YouTube ID + title), in that order.
   Since 2026-11-07 WordPress can replace them: 「サイトの表示 → ContentsX → トップページ → ヒーローの動画」
   (GET /slots/cx-top-hero — YouTube only, up to 3). An empty slot, a failed or slow request (SLOT_TIMEOUT)
   or WordPress being off keeps the videos in index.html. The moving preview waits for this answer so it
   never starts a video that is about to be replaced.
   YouTube is embedded with the official IFrame Player API on youtube-nocookie.com. While a video is
   open its own controls, logo and links are visible and nothing is laid over it. */
(function () {
  'use strict';
  var ADVANCE_MS = 7000;
  var PREVIEW_ADVANCE_MS = 10000;
  var REVEAL_MS = 5000;
  var API_TIMEOUT = 10000;
  var SLOT_TIMEOUT = 4000;
  var YT_ID = /^[\w-]{11}$/;
  var SCALE = 1.5;

  var hero = document.getElementById('hero');
  var card = document.querySelector('[data-cxhv-creative]');
  var stage = document.querySelector('[data-cxhv-stage]');
  if (!hero || !card || !stage) return;
  var track = card.querySelector('[data-cxhv-track]');
  var slides = Array.prototype.slice.call(card.querySelectorAll('[data-cxhv-slide]'));
  var prevBtn = card.querySelector('[data-cxhv-prev]');
  var nextBtn = card.querySelector('[data-cxhv-next]');
  var closeBtn = card.querySelector('[data-cxhv-close]');
  var status = card.querySelector('[data-cxhv-status]');
  if (!track || !slides.length) return;

  var pc = window.matchMedia('(min-width: 1101px) and (hover: hover)');
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  var state = { index: 0, open: false, player: null, playerIndex: -1, timer: 0, visible: false, heroActive: true, hover: false, token: null, loaded: document.readyState === 'complete', slotReady: false };
  var preview = { player: null, index: -1, token: null, revealTimer: 0 };
  var TEXT = {
    ja: { fail: '動画を読み込めませんでした。時間をおいて、もう一度お試しください。' },
    en: { fail: 'The video could not be loaded. Please try again later.' }
  };
  function t(key) {
    var lang = window.i18n && window.i18n.getLang ? window.i18n.getLang() : 'ja';
    return (TEXT[lang] || TEXT.ja)[key];
  }

  /* ---------- YouTube IFrame API (loaded only when a video is opened) ---------- */
  var apiPromise = null;
  function loadApi() {
    if (apiPromise) return apiPromise;
    apiPromise = new Promise(function (resolve, reject) {
      if (window.YT && window.YT.Player) { resolve(window.YT); return; }
      var timer = setTimeout(function () { reject(new Error('timeout')); }, API_TIMEOUT);
      var previous = window.onYouTubeIframeAPIReady;
      window.onYouTubeIframeAPIReady = function () {
        clearTimeout(timer);
        if (typeof previous === 'function') previous();
        resolve(window.YT);
      };
      var s = document.createElement('script');
      s.src = 'https://www.youtube.com/iframe_api';
      s.async = true;
      s.onerror = function () { clearTimeout(timer); reject(new Error('load')); };
      document.head.appendChild(s);
    });
    apiPromise.catch(function () { apiPromise = null; });
    return apiPromise;
  }
  function destroyPlayer() {
    state.token = null;
    if (state.player && state.player.destroy) { try { state.player.destroy(); } catch (e) { /* already gone */ } }
    state.player = null;
    state.playerIndex = -1;
    slides.forEach(function (s) {
      var holder = s.querySelector('.cxhv-player');
      if (holder) holder.remove();
      s.classList.remove('has-player');
    });
    status.textContent = '';
  }
  function mountPlayer(i, startSeconds) {
    if (state.playerIndex === i && state.player) return;
    destroyPlayer();
    var slide = slides[i];
    var holder = document.createElement('div');
    holder.className = 'cxhv-player';
    var target = document.createElement('div');
    holder.appendChild(target);
    slide.appendChild(holder);
    slide.classList.add('has-player');
    state.playerIndex = i;
    var token = {};
    state.token = token;
    loadApi().then(function (YT) {
      if (state.token !== token) return;
      state.player = new YT.Player(target, {
        host: 'https://www.youtube-nocookie.com',
        videoId: slide.getAttribute('data-video'),
        width: '100%', height: '100%',
        playerVars: { autoplay: 1, mute: 0, controls: 1, playsinline: 1, rel: 0, enablejsapi: 1, origin: location.origin, iv_load_policy: 3, start: Math.max(0, Math.floor(startSeconds || 0)) },
        events: {
          onReady: function (e) {
            if (state.token !== token) return;
            var frame = e.target.getIframe && e.target.getIframe();
            if (frame) frame.title = 'Creative 動画: ' + slide.getAttribute('data-title');
            e.target.playVideo();
          },
          // Sound needs the browser's permission; without it the video still starts, muted.
          onAutoplayBlocked: function (e) { if (state.token === token) { e.target.mute(); e.target.playVideo(); } },
          onError: function () { if (state.token === token) failed(); }
        }
      });
    }).catch(function () { if (state.token === token) failed(); });
  }
  function failed() {
    destroyPlayer();
    status.textContent = t('fail');
  }

  /* ---------- PC moving preview (behind the picture, see the header) ---------- */
  function previewAllowed() {
    return pc.matches && !reduced.matches && state.loaded && state.slotReady && !document.hidden && state.visible && state.heroActive && !state.open;
  }
  function destroyPreview() {
    preview.token = null;
    clearTimeout(preview.revealTimer);
    preview.revealTimer = 0;
    if (preview.player && preview.player.destroy) { try { preview.player.destroy(); } catch (e) { /* already gone */ } }
    preview.player = null;
    preview.index = -1;
    slides.forEach(function (s) {
      var holder = s.querySelector('.cxhv-preview');
      if (holder) holder.remove();
      s.classList.remove('has-preview', 'is-revealed');
    });
  }
  function mountPreview(i) {
    if (preview.index === i && preview.player) return;
    destroyPreview();
    var slide = slides[i];
    var id = slide.getAttribute('data-video');
    var holder = document.createElement('div');
    holder.className = 'cxhv-player cxhv-preview';
    holder.setAttribute('aria-hidden', 'true');
    var target = document.createElement('div');
    holder.appendChild(target);
    slide.insertBefore(holder, slide.firstChild);
    slide.classList.add('has-preview');
    preview.index = i;
    var token = {};
    preview.token = token;
    loadApi().then(function (YT) {
      if (preview.token !== token) return;
      preview.player = new YT.Player(target, {
        host: 'https://www.youtube-nocookie.com',
        videoId: id,
        width: '100%', height: '100%',
        playerVars: { autoplay: 1, mute: 1, controls: 0, loop: 1, playlist: id, playsinline: 1, rel: 0, iv_load_policy: 3, disablekb: 1, fs: 0, enablejsapi: 1, origin: location.origin },
        events: {
          onReady: function (e) {
            if (preview.token !== token) return;
            var frame = e.target.getIframe && e.target.getIframe();
            if (frame) { frame.tabIndex = -1; frame.title = 'Creative 動画（プレビュー）'; }
            e.target.mute();
            e.target.playVideo();
          },
          onStateChange: function (e) {
            // Playing: keep the picture on top until YouTube's start-up title has gone, then fade it.
            if (e.data !== 1 || preview.token !== token || preview.revealTimer || slide.classList.contains('is-revealed')) return;
            preview.revealTimer = setTimeout(function () { if (preview.token === token) slide.classList.add('is-revealed'); }, REVEAL_MS);
          },
          onAutoplayBlocked: function () { if (preview.token === token) destroyPreview(); },
          onError: function () { if (preview.token === token) destroyPreview(); }
        }
      });
    }).catch(function () { if (preview.token === token) destroyPreview(); });
  }

  /* ---------- the row of pictures ---------- */
  function width() { return track.clientWidth || 1; }
  function mark(i) {
    state.index = i;
    slides.forEach(function (s, k) {
      var on = k === i;
      // Re-adding the class restarts the slow zoom on the picture that came into view.
      if (on && !s.classList.contains('is-current')) { void s.offsetWidth; }
      s.classList.toggle('is-current', on);
      s.setAttribute('aria-hidden', String(!on));
      s.querySelector('.cxhv-slide-btn').tabIndex = on ? 0 : -1;
    });
    prevBtn.disabled = i === 0;
    nextBtn.disabled = i === slides.length - 1;
  }
  function go(i, instant) {
    i = Math.max(0, Math.min(slides.length - 1, i));
    track.scrollTo({ left: i * width(), behavior: instant || reduced.matches ? 'auto' : 'smooth' });
    mark(i);
    settleSoon();
  }
  // The player (open) or preview (at rest) follows the picture in view once the row stops moving.
  var settleTimer = 0;
  function settleSoon() {
    clearTimeout(settleTimer);
    settleTimer = setTimeout(function () {
      if (state.open) mountPlayer(state.index);
      else if (previewAllowed()) mountPreview(state.index);
    }, 300);
  }
  var frame = 0;
  track.addEventListener('scroll', function () {
    if (frame) return;
    frame = requestAnimationFrame(function () {
      frame = 0;
      var i = Math.round(track.scrollLeft / width());
      if (i !== state.index) mark(i);
      if (state.open || preview.index !== -1 || previewAllowed()) settleSoon();
    });
  }, { passive: true });

  /* ---------- automatic advance (PC, card at rest) ---------- */
  function advanceAllowed() {
    return pc.matches && !reduced.matches && !document.hidden && state.visible && state.heroActive && !state.open && !state.hover;
  }
  function update() {
    clearInterval(state.timer);
    state.timer = 0;
    if (previewAllowed()) mountPreview(state.index);
    else destroyPreview();
    if (advanceAllowed()) {
      state.timer = setInterval(function () {
        if (!advanceAllowed()) return;
        go(state.index + 1 < slides.length ? state.index + 1 : 0);
      }, previewAllowed() ? PREVIEW_ADVANCE_MS : ADVANCE_MS);
    }
  }

  /* ---------- open / close ---------- */
  function placeExpanded() {
    // Centre of the Hero's right half, about 1.5× wider, leaving room for ‹ › and × outside.
    var heroBox = hero.getBoundingClientRect();
    var stageBox = stage.getBoundingClientRect();
    var k = stageBox.width / stage.offsetWidth || 1;
    var half = heroBox.width / 2;
    var w = Math.min(parseFloat(card.dataset.baseWidth) * SCALE, half - 2 * 64, (heroBox.height - 2 * 72) * 16 / 9);
    var h = w * 9 / 16;
    card.style.left = ((heroBox.left + half + (half - w) / 2 - stageBox.left) / k) + 'px';
    card.style.top = ((heroBox.top + (heroBox.height - h) / 2 - stageBox.top) / k) + 'px';
    card.style.width = (w / k) + 'px';
  }
  function open(i) {
    if (state.open) { go(i); return; }
    var from = preview.index === i && preview.player && preview.player.getCurrentTime ? preview.player.getCurrentTime() : 0;
    state.open = true;
    update();
    card.dataset.baseWidth = String(card.offsetWidth);
    // Tablet/SP open in place: keep the card area's height so the page below does not jump
    // (a shorter Hero would also look like the visitor had scrolled on).
    if (!pc.matches) stage.style.minHeight = stage.offsetHeight + 'px';
    card.classList.add('is-expanded');
    stage.classList.add('is-expanded', 'is-open');
    prevBtn.hidden = nextBtn.hidden = closeBtn.hidden = false;
    Array.prototype.forEach.call(stage.querySelectorAll('a.cxhv-card'), function (a) { a.inert = true; });
    if (pc.matches) placeExpanded();
    mark(i);
    track.scrollLeft = i * width();
    mountPlayer(i, from);
    closeBtn.focus({ preventScroll: true });
  }
  function close(restoreFocus) {
    if (!state.open) return;
    state.open = false;
    clearTimeout(settleTimer);
    destroyPlayer();
    prevBtn.hidden = nextBtn.hidden = closeBtn.hidden = true;
    card.style.left = card.style.top = card.style.width = '';
    stage.style.minHeight = '';
    card.classList.remove('is-expanded');
    stage.classList.remove('is-expanded', 'is-open');
    Array.prototype.forEach.call(stage.querySelectorAll('a.cxhv-card'), function (a) { a.inert = false; });
    if (restoreFocus) slides[state.index].querySelector('.cxhv-slide-btn').focus({ preventScroll: true });
    update();
  }

  /* ---------- videos chosen in WordPress (2026-11-07) ---------- */
  function applySlot(items) {
    var list = (Array.isArray(items) ? items : []).filter(function (c) {
      return c && c.video && c.video.provider === 'youtube' && YT_ID.test(String(c.video.video_id || ''));
    }).slice(0, slides.length);
    if (!list.length || state.open) return;
    var same = list.length === slides.length && list.every(function (c, k) { return slides[k].getAttribute('data-video') === c.video.video_id; });
    if (same) return;
    var n = list.length;
    list.forEach(function (c, k) {
      var id = c.video.video_id;
      var title = String(c.title || '').trim() || 'Creative';
      var thumb = /^https:\/\/[^\s"'<>]+$/.test(String(c.thumb || '')) ? c.thumb : 'https://i.ytimg.com/vi/' + id + '/hqdefault.jpg';
      var btn = slides[k].querySelector('.cxhv-slide-btn');
      slides[k].setAttribute('data-video', id);
      slides[k].setAttribute('data-title', title);
      btn.setAttribute('aria-label', 'Creative 動画 ' + (k + 1) + '/' + n + '「' + title + '」を拡大して再生');
      var img = btn.querySelector('img');
      if (img) img.src = thumb;
    });
    slides.splice(n).forEach(function (s) { s.remove(); });
    mark(Math.min(state.index, n - 1));
    track.scrollLeft = state.index * width();
  }
  function loadSlot() {
    function done() {
      if (state.slotReady) return;
      state.slotReady = true;
      update();
    }
    if (typeof WP_CONFIG === 'undefined' || WP_CONFIG.enabled === false || !WP_CONFIG.apiBase || !window.fetch) { done(); return; }
    var ctrl = 'AbortController' in window ? new AbortController() : null;
    var timer = setTimeout(function () { if (ctrl) ctrl.abort(); done(); }, SLOT_TIMEOUT);
    fetch(WP_CONFIG.apiBase + '/slots/cx-top-hero', ctrl ? { signal: ctrl.signal } : {})
      .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(function (d) { if (!state.slotReady) applySlot(d && d.items); })
      .catch(function (e) { console.warn('[Hero] /slots/cx-top-hero failed:', e.message); })
      .then(function () { clearTimeout(timer); done(); });
  }

  /* ---------- events ---------- */
  slides.forEach(function (s, i) {
    s.querySelector('.cxhv-slide-btn').addEventListener('click', function () { open(i); });
  });
  prevBtn.addEventListener('click', function () { go(state.index - 1); });
  nextBtn.addEventListener('click', function () { go(state.index + 1); });
  closeBtn.addEventListener('click', function () { close(true); });
  // ← → move between videos: on the card at rest, and anywhere while a video is open
  // (a ‹ › button that becomes disabled at the end drops the focus out of the card).
  function arrows(e) {
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
    if (/^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)) return;
    e.preventDefault();
    go(state.index + (e.key === 'ArrowRight' ? 1 : -1));
  }
  card.addEventListener('keydown', function (e) { if (!state.open) arrows(e); });
  document.addEventListener('keydown', function (e) {
    if (!state.open) return;
    if (e.key === 'Escape') close(true);
    else arrows(e);
  });
  card.addEventListener('pointerenter', function () { state.hover = true; update(); });
  card.addEventListener('pointerleave', function () { state.hover = false; update(); });
  // The row keeps the picture in view aligned when its width changes (opening, closing, resizing).
  if ('ResizeObserver' in window) {
    new ResizeObserver(function () { track.scrollLeft = state.index * width(); }).observe(track);
  }
  // Card 3 scrolls to Sales X on this page.
  Array.prototype.forEach.call(stage.querySelectorAll('[data-cxhv-scroll]'), function (a) {
    a.addEventListener('click', function (e) {
      var target = document.querySelector(a.getAttribute('href'));
      if (!target || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      e.preventDefault();
      history.pushState(null, '', a.getAttribute('href'));
      target.scrollIntoView({ behavior: reduced.matches ? 'auto' : 'smooth', block: 'start' });
    });
  });
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (entries) {
      state.visible = entries[0].intersectionRatio >= 0.5;
      update();
    }, { threshold: [0, 0.5, 1] }).observe(card);
  } else {
    state.visible = true;
  }
  // js/hero-about.js reports whether the Hero is still the scene (scrolling on hides it).
  document.addEventListener('cxha:hero', function (e) {
    state.heroActive = !!e.detail.active;
    if (!state.heroActive) close(false);
    update();
  });
  document.addEventListener('visibilitychange', function () {
    if (document.hidden && state.player && state.player.pauseVideo) state.player.pauseVideo();
    update();
  });
  window.addEventListener('resize', function () {
    if (state.open && pc.matches) placeExpanded();
    else if (state.open) card.style.left = card.style.top = card.style.width = '';
  }, { passive: true });
  pc.addEventListener('change', function () { close(false); update(); });
  reduced.addEventListener('change', update);
  mark(0);
  loadSlot();
  if (!state.loaded) {
    window.addEventListener('load', function () {
      // Give the first paint and the rest of the page room before YouTube loads.
      (window.requestIdleCallback || function (fn) { return setTimeout(fn, 600); })(function () { state.loaded = true; update(); }, { timeout: 2500 });
    }, { once: true });
  }
  update();
})();
