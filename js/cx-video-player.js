/* CxVideoPlayer — inline 16:9 video carousel (Issue #97, carousel since Issue #102). Shared by
   BizAnime and BizVideo; only the data differs. The videos sit side by side in one row that the
   visitor scrolls sideways (swipe / trackpad / ‹ › buttons / ← → keys); each video uses the whole
   width of the frame. Nothing plays until the visitor presses play (no autoplay on load); the embed
   is then created in place (no popup). Scrolling to another video, switching service or calling
   stop() removes the embed, so the previous video stops.
   items: [{ title, description, provider: youtube|youtube_playlist|drive|mp4, video_id, src, poster }]
   Embed URLs are rebuilt from validated IDs; nothing from the data is written as HTML.
   CxVideoPlayer.playable(items) returns the items that can be played (the caller decides what to
   show when there are none).
   The returned player has stop(), destroy() and play(i): play(i) starts video i at once, for a caller
   whose own button the visitor just pressed (the Creative X page's WORKS opens its viewer that way). */
(function () {
  'use strict';
  if (!window.cxDom) return; // js/cx-dom.js が先に読まれていない
  var YT_ID = /^[A-Za-z0-9_-]{6,20}$/;
  var LIST_ID = /^[A-Za-z0-9_-]{10,64}$/;
  var DRIVE_ID = /^[A-Za-z0-9_-]{10,}$/;
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)');

  var el = window.cxDom.el;
  var iconButton = window.cxDom.iconButton;
  var safeImage = window.cxDom.safeImage;
  /** Build the embed for a user-initiated play. Returns null when the item is not playable. */
  function embedFor(item) {
    var id = String(item.video_id || '');
    if (item.provider === 'youtube' && YT_ID.test(id)) return { kind: 'iframe', src: 'https://www.youtube-nocookie.com/embed/' + id + '?autoplay=1&rel=0&playsinline=1' };
    if (item.provider === 'youtube_playlist' && LIST_ID.test(id)) return { kind: 'iframe', src: 'https://www.youtube-nocookie.com/embed/videoseries?list=' + id + '&autoplay=1&rel=0&playsinline=1' };
    if (item.provider === 'drive' && DRIVE_ID.test(id)) return { kind: 'iframe', src: 'https://drive.google.com/file/d/' + id + '/preview' };
    if (item.provider === 'mp4' && /^https:\/\/[^\s"'<>]+\.mp4(\?[^\s"'<>]*)?$/i.test(item.src || '')) return { kind: 'video', src: item.src };
    return null;
  }
  function posterFor(item) {
    var p = safeImage(item.poster);
    if (p) return p;
    if ((item.provider === 'youtube') && YT_ID.test(String(item.video_id || ''))) return 'https://i.ytimg.com/vi/' + item.video_id + '/hqdefault.jpg';
    return '';
  }
  /** YouTube answers a missing maxresdefault with a 120×90 grey placeholder: fall back to hqdefault. */
  function poster(img, src) {
    img.src = src;
    img.addEventListener('load', function () {
      if (img.naturalWidth <= 120 && /\/maxresdefault\.jpg$/.test(img.src)) img.src = img.src.replace(/maxresdefault\.jpg$/, 'hqdefault.jpg');
    });
  }
  function playable(items) {
    return (Array.isArray(items) ? items : []).filter(function (it) { return it && embedFor(it); });
  }

  window.CxVideoPlayer = function (root, items, opts) {
    opts = opts || {};
    items = playable(items).slice(0, opts.max || 3);
    var n = items.length;
    var current = 0;
    var playing = -1;
    root.textContent = '';
    root.classList.add('cxvp');
    if (!n) return { stop: function () {}, play: function () {}, destroy: function () { root.textContent = ''; } };

    var track = el('div', 'cxvp-track');
    track.setAttribute('role', 'group');
    track.setAttribute('aria-label', n > 1 ? '動画（横にスクロールして切り替え）' : '動画');
    root.appendChild(track);
    var slides = items.map(function (item, i) {
      var slide = el('div', 'cxvp-stage');
      slide.setAttribute('role', 'group');
      slide.setAttribute('aria-roledescription', 'スライド');
      slide.setAttribute('aria-label', (i + 1) + ' / ' + n + '：' + (item.title || '動画'));
      track.appendChild(slide);
      return slide;
    });
    var prevBtn = null, nextBtn = null, dots = [];
    if (n > 1) {
      prevBtn = iconButton('cxvp-arrow cxvp-arrow-prev', '前の動画', '‹');
      nextBtn = iconButton('cxvp-arrow cxvp-arrow-next', '次の動画', '›');
      prevBtn.addEventListener('click', function () { go(current - 1); });
      nextBtn.addEventListener('click', function () { go(current + 1); });
      var dotBox = el('div', 'cxvp-dots');
      dotBox.setAttribute('aria-hidden', 'true');
      dots = items.map(function () { var d = el('span', 'cxvp-dot'); dotBox.appendChild(d); return d; });
      root.appendChild(prevBtn); root.appendChild(nextBtn); root.appendChild(dotBox);
    }

    function showPoster(i) {
      var item = items[i], stage = slides[i];
      stage.textContent = '';
      stage.classList.remove('is-playing', 'is-loading', 'is-error');
      var src = posterFor(item);
      if (src) {
        var img = el('img', 'cxvp-poster');
        img.alt = ''; img.decoding = 'async';
        if (i > 0) img.loading = 'lazy';
        img.addEventListener('error', function () { img.remove(); });
        poster(img, src);
        stage.appendChild(img);
      }
      var cap = el('div', 'cxvp-caption');
      var t = el('p', 'cxvp-title', item.title || '');
      t.setAttribute('data-i18n-skip', '');
      cap.appendChild(t);
      if (item.description) {
        var d = el('p', 'cxvp-desc', item.description);
        d.setAttribute('data-i18n-skip', '');
        cap.appendChild(d);
      }
      stage.appendChild(cap);
      var play = el('button', 'cxvp-play');
      play.type = 'button';
      play.setAttribute('aria-label', (item.title || '動画') + 'を再生');
      var ring = el('span', 'cxvp-play-ring');
      ring.setAttribute('aria-hidden', 'true');
      play.appendChild(ring);
      play.addEventListener('click', function () { if (i !== current) go(i); start(i); });
      stage.appendChild(play);
    }
    function stop() {
      if (playing < 0) return;
      var was = playing;
      playing = -1;
      root.classList.remove('is-playing');
      showPoster(was);
    }
    function start(i) {
      var item = items[i], e = embedFor(item), stage = slides[i];
      if (!e) return;
      stop();
      playing = i;
      root.classList.add('is-playing');
      stage.textContent = '';
      stage.classList.add('is-playing', 'is-loading');
      var spinner = el('div', 'cxvp-loading', '読み込み中…');
      spinner.setAttribute('role', 'status');
      stage.appendChild(spinner);
      var node;
      if (e.kind === 'video') {
        node = el('video', 'cxvp-media');
        node.src = e.src; node.controls = true; node.playsInline = true; node.preload = 'metadata';
        var p = posterFor(item); if (p) node.poster = p;
        node.addEventListener('loadeddata', function () { stage.classList.remove('is-loading'); spinner.remove(); });
        node.addEventListener('error', showError);
        stage.appendChild(node);
        var pr = node.play(); if (pr && pr.catch) pr.catch(function () {});
      } else {
        node = el('iframe', 'cxvp-media');
        node.src = e.src;
        node.title = item.title || '動画';
        node.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen';
        node.allowFullscreen = true;
        node.referrerPolicy = 'strict-origin-when-cross-origin';
        node.addEventListener('load', function () { stage.classList.remove('is-loading'); spinner.remove(); });
        stage.appendChild(node);
      }
      function showError() {
        stage.classList.remove('is-loading');
        stage.classList.add('is-error');
        spinner.textContent = '動画を再生できませんでした。時間をおいて、もう一度お試しください。';
      }
    }
    /** Mark slide i as the one in view; leaving a playing video stops it. */
    function settle(i) {
      i = Math.max(0, Math.min(n - 1, i));
      if (i !== current && playing >= 0 && playing !== i) stop();
      current = i;
      slides.forEach(function (s, k) { s.setAttribute('aria-hidden', String(k !== i)); s.inert = k !== i; });
      dots.forEach(function (d, k) { d.classList.toggle('is-active', k === i); });
      if (prevBtn) { prevBtn.disabled = i === 0; nextBtn.disabled = i === n - 1; }
    }
    function go(i) {
      i = Math.max(0, Math.min(n - 1, i));
      track.scrollTo({ left: i * track.clientWidth, behavior: reduced.matches ? 'auto' : 'smooth' });
      settle(i);
    }
    // Swipes and trackpad scrolling: the slide whose centre is in view becomes current.
    var frame = 0;
    track.addEventListener('scroll', function () {
      if (frame) return;
      frame = requestAnimationFrame(function () {
        frame = 0;
        var i = Math.round(track.scrollLeft / Math.max(1, track.clientWidth));
        if (i !== current) settle(i);
      });
    }, { passive: true });
    root.addEventListener('keydown', function (e) {
      if (n < 2 || (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight')) return;
      e.preventDefault();
      go(current + (e.key === 'ArrowRight' ? 1 : -1));
    });
    // Keep the current video aligned when the frame changes size.
    var onResize = function () { track.scrollLeft = current * track.clientWidth; };
    window.addEventListener('resize', onResize, { passive: true });

    items.forEach(function (_, i) { showPoster(i); });
    settle(0);

    return {
      stop: stop,
      play: function (i) { if (i >= 0 && i < n) { go(i); start(i); } },
      destroy: function () { window.removeEventListener('resize', onResize); if (frame) cancelAnimationFrame(frame); root.textContent = ''; }
    };
  };
  window.CxVideoPlayer.playable = playable;
})();
