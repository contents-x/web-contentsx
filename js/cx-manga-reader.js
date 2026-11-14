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
   Book mode (opts.book, 2026-11, the Creative X work viewer — js/cx-works.js): the same pages and reading
   rules, but a page turn is BizManga biz-library's 3D page flip (js/works.js goNext / goPrev / mobileFlipTo,
   css/works.css .flip-overlay / .flip-face / .page-shadow; web-bizmanga is not changed). Spreads lie open
   as a book with a spine; next lifts the left page and lays it over to the right (right-bound), previous
   the right page to the left. One page at a time, the page turns on its left edge as in mobileFlipTo.
   500ms, cubic-bezier(.3,0,.2,1), shadows at 15–65% of the turn, the pages underneath change at 45%.
   Vertical reading keeps its scroll (no book). Reduced motion: pages change without the turn.
   Styles: css/cx-manga-book.css. Without opts.book nothing changes (the homepage Creative X reader).
   Usage: var r = CxMangaReader(container, work, { wide: function () { return true; }, book: false }); r.destroy(); */
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
    var book = !!opts.book;
    var reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    var FLIP_MS = 500;                            // BizManga works.js FLIP_DURATION
    var FLIP_EASE = 'cubic-bezier(0.3, 0.0, 0.2, 1)';
    var flipping = false, timers = [], bk = null;  // bk: the parts of the book on the stage
    var title = (work && work.title_ja) || 'マンガ';
    var state = { mode: 'single', index: 0, full: false, vertical: false, destroyed: false, aspect: 0 };
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
      list.forEach(function (i) {
        if (typeof i !== 'number' || !pages[i]) return;
        var im = new Image();
        im.src = pages[i];
        // Book mode swaps the pages under a turning leaf: have them decoded before the turn, so no blank paper shows.
        if (book && im.decode) im.decode().catch(function () {});
      });
    }
    function render() {
      if (state.destroyed) return;
      bk = null;
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
      if (book) {
        stage.classList.add('is-book');
        if (state.mode === 'spread') renderBook(cur); else renderPageBook(cur);
        counts(cur, u);
        return;
      }
      var spread = el('div', 'cxmr-spread');
      // Lower page number on the RIGHT: left image is cur[1] (or thanks), right image cur[0].
      cur.slice().reverse().forEach(function (i) { spread.appendChild(pageImg(i)); });
      stage.appendChild(spread);
      counts(cur, u);
    }
    function counts(cur, u) {
      var nums = cur.filter(function (i) { return typeof i === 'number'; }).map(function (i) { return i + 1; });
      count.textContent = nums.join('-') + ' / ' + pages.length;
      next.disabled = state.index >= u.length - 1;
      prev.disabled = state.index <= 0;
      preload((u[state.index + 1] || []).concat(u[state.index + 2] || []));
    }

    /* ---------- book mode (BizManga biz-library's page flip) ---------- */
    function src(i) { return i === 'thanks' ? THANKS : pages[i]; }
    function later(fn, ms) { timers.push(setTimeout(fn, ms)); }
    function face(cls) {
      var f = el('div', cls);
      var img = el('img');
      img.alt = ''; img.decoding = 'async';
      f.appendChild(img);
      return f;
    }
    function setPage(img, i) {
      img.decoding = 'sync';                       // already preloaded: paint it in the same frame
      img.src = src(i);
      img.alt = i === 'thanks' ? '' : title + ' ' + (i + 1) + 'ページ';
    }
    /** The open book: right page (lower number), left page, spine, the turning leaf and its shadows. */
    function renderBook(cur) {
      var bookEl = el('div', 'cxmr-book');
      var right = el('div', 'cxmr-leaf cxmr-leaf--right');
      var left = el('div', 'cxmr-leaf cxmr-leaf--left');
      var imgR = pageImg(cur[0]), imgL = pageImg(cur[1]);
      right.appendChild(imgR); left.appendChild(imgL);
      var flip = el('div', 'cxmr-flip');
      var front = face('cxmr-flip__face cxmr-flip__front'), back = face('cxmr-flip__face cxmr-flip__back');
      flip.appendChild(front); flip.appendChild(back);
      var spine = el('div', 'cxmr-spine');
      var shadeL = el('div', 'cxmr-shade cxmr-shade--left'), shadeR = el('div', 'cxmr-shade cxmr-shade--right');
      [spine, flip, shadeL, shadeR].forEach(function (n) { n.setAttribute('aria-hidden', 'true'); });
      [right, left, spine, flip, shadeL, shadeR].forEach(function (n) { bookEl.appendChild(n); });
      stage.appendChild(bookEl);
      bk = { right: right, left: left, imgR: imgR, imgL: imgL, flip: flip,
        front: front.firstChild, back: back.firstChild, shadeL: shadeL, shadeR: shadeR };
      sizeBook();
    }
    /** Two pages as large as the stage allows, leaving the side space for ‹ ›; one page (phones) as large
        as the stage. The page shape comes from page 1 (BizManga uses 0.707). */
    function sizeBook() {
      if (!bk) return;
      var aspect = state.aspect || 0.707;
      if (bk.page) {
        var oneW = Math.min(stage.clientWidth, Math.round(stage.clientHeight * aspect));
        bk.page.style.width = oneW + 'px';
        bk.page.style.height = Math.round(oneW / aspect) + 'px';
        return;
      }
      var h = Math.max(stage.clientHeight - 24, 160);
      var w = Math.max(stage.clientWidth - 128, 240);
      var pageW = Math.min(Math.round(h * aspect), Math.floor((w - 6) / 2));
      var pageH = Math.round(pageW / aspect);
      [bk.right, bk.left].forEach(function (leaf) { leaf.style.width = pageW + 'px'; leaf.style.height = pageH + 'px'; });
    }
    /** One page (phones): the page, the leaf that turns over it, and its shadow. */
    function renderPageBook(cur) {
      var box = el('div', 'cxmr-pbook');
      var page = pageImg(cur[0]);
      page.classList.add('cxmr-pbook__page');
      var flip = el('div', 'cxmr-pflip');
      var front = face('cxmr-pflip__face cxmr-pflip__front'), back = face('cxmr-pflip__face cxmr-pflip__back');
      flip.appendChild(front); flip.appendChild(back);
      var shade = el('div', 'cxmr-pshade');
      flip.setAttribute('aria-hidden', 'true'); shade.setAttribute('aria-hidden', 'true');
      box.appendChild(page); box.appendChild(flip); box.appendChild(shade);
      stage.appendChild(box);
      bk = { page: page, flip: flip, front: front.firstChild, back: back.firstChild, shade: shade };
      sizeBook();
    }
    function shadow(node) {
      node.style.transition = 'none';
      node.style.opacity = '0';
      later(function () { node.style.transition = 'opacity ' + FLIP_MS * 0.3 + 'ms ease'; node.style.opacity = '0.6'; }, FLIP_MS * 0.15);
      later(function () { node.style.opacity = '0'; }, FLIP_MS * 0.65);
    }
    function turn(leaf, from, to) {
      leaf.style.transition = 'none';
      leaf.style.transform = 'rotateY(' + from + 'deg)';
      requestAnimationFrame(function () {
        requestAnimationFrame(function () {
          leaf.style.transition = 'transform ' + FLIP_MS + 'ms ' + FLIP_EASE;
          leaf.style.transform = 'rotateY(' + to + 'deg)';
        });
      });
    }
    function settle(to) {
      later(function () {
        flipping = false;
        state.index = to;
        render();
      }, FLIP_MS + 30);
    }
    /** goNext / goPrev: next lifts the left page over to the right, previous the right page over to the left. */
    function flipSpread(step, to) {
      var u = units(), cur = u[state.index], nxt = u[to], forward = step > 0;
      bk.flip.className = 'cxmr-flip is-active ' + (forward ? 'is-left' : 'is-right');
      bk.front.src = src(forward ? cur[1] : cur[0]);
      bk.back.src = src(forward ? nxt[0] : nxt[1]);
      (forward ? bk.shadeR : bk.shadeL).classList.add('is-active');
      shadow(forward ? bk.shadeR : bk.shadeL);
      later(function () { setPage(bk.imgR, nxt[0]); setPage(bk.imgL, nxt[1]); }, FLIP_MS * 0.45);
      turn(bk.flip, 0, forward ? 180 : -180);
      settle(to);
    }
    /** mobileFlipTo: the page turns on its left edge; forward 0 → -180°, back -180° → 0. */
    function flipPage(step, to) {
      var u = units(), forward = step > 0, curSrc = src(u[state.index][0]), toSrc = src(u[to][0]);
      bk.front.src = forward ? curSrc : toSrc;
      bk.back.src = forward ? toSrc : curSrc;
      setPage(bk.page, u[to][0]);
      bk.shade.style.background = 'linear-gradient(to ' + (forward ? 'right' : 'left') + ', rgba(0,0,0,0.35), transparent 50%)';
      bk.flip.classList.add('is-active');
      bk.shade.classList.add('is-active');
      shadow(bk.shade);
      turn(bk.flip, forward ? 0 : -180, forward ? -180 : 0);
      settle(to);
    }
    function go(step) {
      if (state.mode === 'vertical' || flipping) return;
      var to = state.index + step;
      if (to < 0 || to >= units().length) return;
      if (book && bk && !reduced.matches) {
        flipping = true;
        if (state.mode === 'spread') flipSpread(step, to); else flipPage(step, to);
        return;
      }
      state.index = to;
      render();
    }
    function layoutMode() {
      if (state.vertical) return 'vertical';
      return wide() ? 'spread' : 'single';
    }
    function relayout() {
      var mode = layoutMode();
      if (mode === state.mode) { if (book) sizeBook(); return; }
      if (flipping) return;
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
      if (book) requestAnimationFrame(sizeBook);
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
      if (book) requestAnimationFrame(sizeBook);
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
      if (ratio > 0 && isFinite(ratio)) state.aspect = Math.min(Math.max(1 / ratio, 0.5), 1);
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
        timers.forEach(clearTimeout);
        window.removeEventListener('resize', onResize);
        document.removeEventListener('keydown', onKey);
        root.textContent = '';
      }
    };
  };
})();
