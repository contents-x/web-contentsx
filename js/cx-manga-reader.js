/* CxMangaReader — inline manga reader for contentsx.jp (Issue #97).
   Reuses BizManga's data (WordPress `gallery` / `view_type`) and reading rules without loading
   BizManga's own scripts (BizManga/js/works.js, bm-view-type.js are not changed):
   - Right-bound (Japanese): spreads are [1,2],[3,4]… with the lower page on the RIGHT; an odd last
     page is paired with /material/manga/thanks_v02.webp (works.js buildSpreads / showSpread).
   - Vertical reading when view_type is vertical_only/vertical or the first page is taller than
     1.8× its width (bm-view-type.js isForcedVertical / isVerticalByRatio).
   - Spread on wide frames, one page at a time on narrow ones; swipe left = next, right = previous;
     ← = next, → = previous; a click/tap on the left half of the pages = next, right half = previous
     (same direction as the ‹ › buttons; not in vertical reading).
   - 「拡大」 opens the reader over the whole screen, like BizManga's biz-library reader (2026-10-14):
     the reader element moves to <body> while open (the Creative X section clips and transforms its
     contents, so a fixed box inside it would stay small), the page behind stops scrolling, and
     「閉じる」/ Esc puts it back where it was.
     Pages are never cropped (object-fit: contain).
   The vertical rule is copied rather than delegated to window.bmViewType because contentsx.jp does
   not load BizManga's scripts (another site; Issue #97 keeps the sites independent). If BizManga
   changes bm-view-type.js (ratio 1.8, view_type values), change VERTICAL_RATIO / forcedVertical here.
   Like bm-view-type.js, a first page that fails to load counts as "not vertical".
   Usage: var r = CxMangaReader(container, work, { wide: function () { return true; } }); r.destroy(); */
(function () {
  'use strict';
  if (!window.cxDom) return; // js/cx-dom.js が先に読まれていない（Creative X は HTML のリンクのまま）
  var THANKS = '/material/manga/thanks_v02.webp';
  var VERTICAL_RATIO = 1.8;
  var PAGE_HOSTS = ['cms.contentsx.jp', 'contentsx.jp'];

  var el = window.cxDom.el;
  var iconButton = window.cxDom.iconButton;
  var safeImage = window.cxDom.safeImage;
  function forcedVertical(work) {
    var vt = work && (work.view_type || work.viewType || work.mode);
    return vt === 'vertical_only' || vt === 'vertical';
  }
  function probeRatio(src) {
    return new Promise(function (resolve) {
      var img = new Image();
      img.onload = function () { resolve(img.naturalHeight / Math.max(1, img.naturalWidth)); };
      img.onerror = function () { resolve(0); };
      img.src = src;
    });
  }

  window.CxMangaReader = function (root, work, opts) {
    opts = opts || {};
    var pages = (Array.isArray(work && work.gallery) ? work.gallery : []).map(function (u) { return safeImage(u, PAGE_HOSTS); }).filter(Boolean);
    var wide = opts.wide || function () { return window.innerWidth >= 769; };
    var title = (work && work.title_ja) || 'マンガ';
    var state = { mode: 'single', index: 0, full: false, vertical: false, destroyed: false };
    var placeholder = null;
    root.textContent = '';
    root.classList.add('cxmr');
    var stage = el('div', 'cxmr-stage');
    stage.tabIndex = 0;
    stage.setAttribute('role', 'region');
    stage.setAttribute('aria-label', title + '（←で次のページ、→で前のページ）');
    var status = el('div', 'cxmr-status', '読み込み中…');
    status.setAttribute('role', 'status');
    var bar = el('div', 'cxmr-bar');
    // Right-bound book: "next" sits on the left, "previous" on the right.
    var next = iconButton('cxmr-btn cxmr-next', '次のページ', '‹');
    var count = el('span', 'cxmr-count');
    count.setAttribute('aria-live', 'polite');
    var prev = iconButton('cxmr-btn cxmr-prev', '前のページ', '›');
    var zoom = el('button', 'cxmr-zoom', '拡大');
    zoom.type = 'button';
    zoom.setAttribute('aria-pressed', 'false');
    bar.appendChild(next); bar.appendChild(count); bar.appendChild(prev); bar.appendChild(zoom);
    root.appendChild(stage); root.appendChild(bar); root.appendChild(status);

    function fail() {
      status.textContent = '漫画を表示できませんでした。時間をおいて、もう一度お試しください。';
      root.classList.add('is-error');
    }
    if (!pages.length) { fail(); return { stop: function () {}, destroy: function () { root.textContent = ''; } }; }

    function units() {
      if (state.mode !== 'spread') return pages.map(function (_, i) { return [i]; });
      var arr = [];
      for (var i = 0; i < pages.length; i += 2) arr.push(i + 1 < pages.length ? [i, i + 1] : [i, 'thanks']);
      return arr;
    }
    function pageImg(i) {
      var img = el('img', 'cxmr-page');
      img.alt = i === 'thanks' ? '' : title + ' ' + (i + 1) + 'ページ';
      img.decoding = 'async';
      img.src = i === 'thanks' ? THANKS : pages[i];
      img.addEventListener('error', function () { img.classList.add('is-broken'); });
      return img;
    }
    function preload(list) {
      list.forEach(function (i) { if (typeof i === 'number' && pages[i]) { var im = new Image(); im.src = pages[i]; } });
    }
    function render() {
      if (state.destroyed) return;
      var u = units();
      state.index = Math.max(0, Math.min(state.index, u.length - 1));
      stage.textContent = '';
      stage.className = 'cxmr-stage is-' + state.mode;
      if (state.mode === 'vertical') {
        pages.forEach(function (_, i) { var img = pageImg(i); if (i > 2) img.loading = 'lazy'; stage.appendChild(img); });
        count.textContent = '1 / ' + pages.length;
        next.hidden = true; prev.hidden = true;
        return;
      }
      next.hidden = false; prev.hidden = false;
      var cur = u[state.index];
      var spread = el('div', 'cxmr-spread');
      // Lower page number on the RIGHT: left image is cur[1] (or thanks), right image cur[0].
      cur.slice().reverse().forEach(function (i) { spread.appendChild(pageImg(i)); });
      stage.appendChild(spread);
      var nums = cur.filter(function (i) { return typeof i === 'number'; }).map(function (i) { return i + 1; });
      count.textContent = nums.join('-') + ' / ' + pages.length;
      next.disabled = state.index >= u.length - 1;
      prev.disabled = state.index <= 0;
      preload((u[state.index + 1] || []).concat(u[state.index + 2] || []));
    }
    function go(step) {
      if (state.mode === 'vertical') return;
      var to = state.index + step;
      if (to < 0 || to >= units().length) return;
      state.index = to;
      render();
    }
    function layoutMode() {
      if (state.vertical) return 'vertical';
      return wide() ? 'spread' : 'single';
    }
    function relayout() {
      var mode = layoutMode();
      if (mode === state.mode) return;
      // Keep the same first page when switching between spread and single page.
      var cur = units()[state.index];
      var firstPage = cur && typeof cur[0] === 'number' ? cur[0] : 0;
      state.mode = mode;
      state.index = mode === 'spread' ? Math.floor(firstPage / 2) : firstPage;
      render();
    }

    next.addEventListener('click', function () { go(1); });
    prev.addEventListener('click', function () { go(-1); });
    function openFull() {
      if (state.full || state.destroyed) return;
      state.full = true;
      // Keep the space in the page so nothing below jumps while the reader is away.
      placeholder = el('div', 'cxmr-placeholder');
      placeholder.style.height = root.offsetHeight + 'px';
      root.parentNode.insertBefore(placeholder, root);
      document.body.appendChild(root);
      root.classList.add('is-full');
      root.setAttribute('role', 'dialog');
      root.setAttribute('aria-modal', 'true');
      root.setAttribute('aria-label', title);
      document.documentElement.classList.add('cxmr-lock');
      zoom.setAttribute('aria-pressed', 'true');
      zoom.textContent = '閉じる';
      stage.scrollTop = 0;
      stage.focus({ preventScroll: true });
    }
    function closeFull(restoreFocus) {
      if (!state.full) return;
      state.full = false;
      if (placeholder && placeholder.parentNode) placeholder.parentNode.replaceChild(root, placeholder);
      placeholder = null;
      root.classList.remove('is-full');
      root.removeAttribute('role');
      root.removeAttribute('aria-modal');
      root.removeAttribute('aria-label');
      document.documentElement.classList.remove('cxmr-lock');
      zoom.setAttribute('aria-pressed', 'false');
      zoom.textContent = '拡大';
      if (restoreFocus) zoom.focus({ preventScroll: true });
    }
    zoom.addEventListener('click', function () { if (state.full) closeFull(true); else openFull(); });
    var onKey = function (e) { if (e.key === 'Escape' && state.full) closeFull(true); };
    document.addEventListener('keydown', onKey);
    stage.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowLeft') { go(1); e.preventDefault(); }
      if (e.key === 'ArrowRight') { go(-1); e.preventDefault(); }
    });
    // Touch: swipe left = next, right = previous (BizManga mobileFlipTo); vertical scrolling stays native.
    var sx = null, sy = 0;
    stage.addEventListener('pointerdown', function (e) { if (e.pointerType !== 'mouse') { sx = e.clientX; sy = e.clientY; } });
    stage.addEventListener('pointerup', function (e) {
      if (sx === null) return;
      var dx = e.clientX - sx, dy = e.clientY - sy;
      sx = null;
      if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.2) { swiped = true; setTimeout(function () { swiped = false; }, 400); go(dx < 0 ? 1 : -1); }
    });
    stage.addEventListener('pointercancel', function () { sx = null; });
    // Click/tap on the pages: left half = next, right half = previous (right-bound book).
    var swiped = false;
    stage.addEventListener('click', function (e) {
      if (swiped) { swiped = false; return; }
      if (state.mode === 'vertical' || e.button !== 0) return;
      var box = stage.getBoundingClientRect();
      go(e.clientX - box.left < box.width / 2 ? 1 : -1);
    });
    stage.addEventListener('scroll', function () {
      if (state.mode !== 'vertical') return;
      var imgs = stage.querySelectorAll('.cxmr-page');
      var line = stage.getBoundingClientRect().top + stage.clientHeight * 0.4;
      var n = 1;
      for (var i = 0; i < imgs.length; i++) { if (imgs[i].getBoundingClientRect().top <= line) n = i + 1; }
      count.textContent = n + ' / ' + pages.length;
    }, { passive: true });
    var onResize = function () { relayout(); };
    window.addEventListener('resize', onResize, { passive: true });

    (forcedVertical(work) ? Promise.resolve(Infinity) : probeRatio(pages[0])).then(function (ratio) {
      if (state.destroyed) return;
      state.vertical = ratio > VERTICAL_RATIO;
      state.mode = layoutMode();
      render();
      status.textContent = '';
      root.classList.add('is-ready');
    });

    // Leaving the service destroys the reader; coming back builds a new one at page 1, not enlarged.
    return {
      stop: function () { closeFull(false); },
      destroy: function () {
        closeFull(false);
        state.destroyed = true;
        window.removeEventListener('resize', onResize);
        document.removeEventListener('keydown', onKey);
        root.textContent = '';
      }
    };
  };
})();
