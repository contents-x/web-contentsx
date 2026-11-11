/* Creative X landing — WORKS gallery (css/service-creative-works.css, SPEC.md §3.0).
   One selected work is shown large (picture left, title / kind / text / open button right) over a blurred
   copy of its thumbnail; a film strip of all works below picks it. ALL / MANGA / ANIME / VIDEO filter
   the strip; a filter change selects its first work.
   Data: the WordPress slot `cx-creative-works` (cxWorks.slot, js/cx-works.js; the same item shape as
   01 CREATIVE SOLUTION). ALL keeps WordPress's order; MANGA / ANIME / VIDEO keep it too, by `format_key`.
   Empty slot (200, no items): 「作品は準備中です」 and the static links. Failure (network, time-out, 5xx):
   「作品を読み込めませんでした」 and the static links. 404 (a WordPress without the Creative X slots yet):
   the older lists (cxWorks.load: /works?site=contentsx and /bizanime-videos), whose ALL mixes the kinds
   round-robin in the order of the section's `data-cxw-mix` (default "manga,anime,video"). Nothing is
   written as HTML.
   Open: the big picture, 「マンガを読む / 動画を見る」 or Enter in the strip open the work in the page's one
   work viewer, cxWorks.open (js/cx-works.js; 03 CREATIVE SOLUTION uses the same): manga as a book with
   BizManga's page flip, video on a phone lying on its side. Choosing a work never plays anything. Closing
   returns focus to what opened it; the filter and the selected work stay as they were.
   On the stage (.cxg-stage) the section has no background of its own: the blurred HERO picture shows
   through, tinted by the selected work's blurred backdrop (css/service-creative-works.css).
   Without JS, without WordPress or with no works, the static links in the HTML stay. */
(function () {
  'use strict';
  var root = document.querySelector('[data-cxw]');
  if (!root || !window.cxDom || !window.CxVideoPlayer || !window.cxWorks) return;
  if (typeof WP_CONFIG === 'undefined' || WP_CONFIG.enabled === false || !WP_CONFIG.apiBase) return;
  var gallery = root.querySelector('[data-cxw-gallery]');
  var filterBar = root.querySelector('[data-cxw-filters]');
  var backdrop = root.querySelector('.cxw-backdrop');
  if (!gallery || !filterBar || !backdrop) return;

  var el = window.cxDom.el;
  var iconButton = window.cxDom.iconButton;
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  var FADE = 160;
  var KINDS = {
    manga: { label: 'MANGA', open: 'マンガを読む' },
    anime: { label: 'ANIME', open: '動画を見る' },
    video: { label: 'VIDEO', open: '動画を見る' }
  };
  var groups = null;
  var all = [];
  var state = { filter: 'all', list: [], index: -1 };
  var token = 0;

  /* ---------- order of ALL ---------- */
  function mixPattern() {
    var p = (root.getAttribute('data-cxw-mix') || '').split(',').map(function (s) { return s.trim(); })
      .filter(function (k) { return Object.prototype.hasOwnProperty.call(KINDS, k); });
    return p.length ? p : ['manga', 'anime', 'video'];
  }
  /** ALL: take one work of each kind in pattern order, again and again, until every kind is used up. */
  function mix(byKind, pattern) {
    var queues = {}, out = [];
    Object.keys(byKind).forEach(function (k) { queues[k] = byKind[k].slice(); });
    var left = function () { return pattern.some(function (k) { return queues[k] && queues[k].length; }); };
    while (left()) pattern.forEach(function (k) { if (queues[k] && queues[k].length) out.push(queues[k].shift()); });
    Object.keys(queues).forEach(function (k) { if (pattern.indexOf(k) < 0) out = out.concat(queues[k]); });
    return out;
  }

  /* ---------- backdrop (two layers, cross-faded) ---------- */
  var layers = Array.prototype.slice.call(backdrop.querySelectorAll('.cxw-backdrop__img'));
  var front = 0;
  function setBackdrop(src) {
    if (!src || layers.length < 2 || layers[front].getAttribute('src') === src) return;
    var next = layers[1 - front];
    var mine = ++token;
    next.onload = function () {
      if (mine !== token) return;
      next.classList.add('is-active');
      layers[front].classList.remove('is-active');
      front = 1 - front;
    };
    next.onerror = function () {};
    next.src = src;
  }

  /* ---------- build ---------- */
  var feature, visual, visualFill, visualImg, visualPlay, kindEl, countEl, titleEl, tagsEl, descEl, moreBtn, usesEl, usesList, openBtn;
  var strip, track, prevBtn, nextBtn, stripCount;
  function buildGallery() {
    gallery.textContent = '';
    feature = el('div', 'cxw-feature');
    visual = el('button', 'cxw-visual');
    visual.type = 'button';
    visual.tabIndex = -1;                       // the 「マンガを読む / 動画を見る」 button is the keyboard route
    visual.setAttribute('aria-hidden', 'true');
    visualFill = el('img', 'cxw-visual__fill'); visualFill.alt = ''; visualFill.decoding = 'async';
    visualImg = el('img', 'cxw-visual__img'); visualImg.alt = ''; visualImg.decoding = 'async';
    visualPlay = el('span', 'cxw-visual__play');
    visual.appendChild(visualFill); visual.appendChild(visualImg); visual.appendChild(visualPlay);
    visualImg.addEventListener('load', function () {
      // YouTube answers a missing maxresdefault with a 120×90 grey picture: use hqdefault instead.
      if (visualImg.naturalWidth <= 120 && /\/maxresdefault\.jpg$/.test(visualImg.src)) visualImg.src = visualImg.src.replace(/maxresdefault\.jpg$/, 'hqdefault.jpg');
    });
    var info = el('div', 'cxw-info');
    var meta = el('p', 'cxw-info__meta');
    kindEl = el('span', 'cxw-kind');
    countEl = el('span', 'cxw-count');
    meta.appendChild(kindEl); meta.appendChild(countEl);
    titleEl = el('h3', 'cxw-info__title');
    titleEl.id = 'cxw-work-title';
    titleEl.setAttribute('data-i18n-skip', '');
    tagsEl = el('ul', 'cxw-tags');
    tagsEl.setAttribute('aria-label', '種類・用途');
    descEl = el('p', 'cxw-desc');
    descEl.id = 'cxw-work-desc';
    descEl.setAttribute('data-i18n-skip', '');
    moreBtn = el('button', 'cxw-more', '続きを読む');
    moreBtn.type = 'button';
    moreBtn.setAttribute('aria-controls', 'cxw-work-desc');
    usesEl = el('div', 'cxw-uses');
    usesEl.appendChild(el('p', 'cxw-uses__label', '活用場面'));
    usesList = el('ul', 'cxw-uses__list');
    usesEl.appendChild(usesList);
    openBtn = el('button', 'cxw-open');
    openBtn.type = 'button';
    openBtn.setAttribute('aria-describedby', 'cxw-work-title');
    [meta, titleEl, tagsEl, descEl, moreBtn, usesEl, openBtn].forEach(function (n) { info.appendChild(n); });
    feature.appendChild(visual); feature.appendChild(info);

    strip = el('div', 'cxw-strip');
    var bar = el('div', 'cxw-strip__bar');
    var label = el('p', 'cxw-strip__label');
    label.appendChild(el('span', '', '作品一覧'));
    stripCount = el('span', 'cxw-strip__count');
    label.appendChild(stripCount);
    prevBtn = iconButton('cxw-strip__arrow', '前の作品群へ', '‹');
    nextBtn = iconButton('cxw-strip__arrow', '次の作品群へ', '›');
    var arrows = el('div', 'cxw-strip__arrows');
    arrows.appendChild(prevBtn); arrows.appendChild(nextBtn);
    bar.appendChild(label); bar.appendChild(arrows);
    track = el('div', 'cxw-strip__track');
    track.setAttribute('role', 'listbox');
    track.setAttribute('aria-orientation', 'horizontal');
    track.setAttribute('aria-label', '作品一覧（左右キーで選ぶ、Enterで開く）');
    strip.appendChild(bar); strip.appendChild(track);
    gallery.appendChild(feature); gallery.appendChild(strip);

    visual.addEventListener('click', function () { open(openBtn); });
    openBtn.addEventListener('click', function () { open(openBtn); });
    // About to open a video: fetch the 3D phone module ahead (it builds nothing yet).
    var warm = function () { var it = state.list[state.index]; if (it && it.kind !== 'manga' && window.cxWorks.warm) window.cxWorks.warm(); };
    [visual, openBtn].forEach(function (n) { n.addEventListener('pointerenter', warm); n.addEventListener('focus', warm); });
    moreBtn.addEventListener('click', function () {
      var on = !descEl.classList.contains('is-open');
      descEl.classList.toggle('is-open', on);
      moreBtn.textContent = on ? '閉じる' : '続きを読む';
      moreBtn.setAttribute('aria-expanded', String(on));
    });
    prevBtn.addEventListener('click', function () { page(-1); });
    nextBtn.addEventListener('click', function () { page(1); });
    track.addEventListener('scroll', arrowsLater, { passive: true });
    window.addEventListener('resize', arrowsLater, { passive: true });
    track.addEventListener('keydown', onStripKey);
    bindDrag();
  }
  function thumbFor(item, i) {
    var opt = el('div', 'cxw-thumb cxw-thumb--' + item.kind);
    opt.id = 'cxw-work-' + i;
    opt.setAttribute('role', 'option');
    opt.setAttribute('aria-selected', 'false');
    opt.tabIndex = -1;
    opt.setAttribute('data-index', String(i));
    var media = el('span', 'cxw-thumb__media');
    if (item.thumb) {
      var img = el('img');
      img.alt = '';
      // No width/height: the frame's CSS aspect-ratio holds the space, and covers / video stills differ in shape.
      img.decoding = 'async';
      if (i > 5) img.loading = 'lazy';
      img.draggable = false;
      img.addEventListener('error', function () { img.remove(); });
      img.src = item.thumb;
      media.appendChild(img);
    }
    opt.appendChild(media);
    var kind = el('span', 'cxw-thumb__kind', KINDS[item.kind].label);
    var name = el('span', 'cxw-thumb__title', item.title);
    name.setAttribute('data-i18n-skip', '');
    opt.appendChild(kind); opt.appendChild(name);
    return opt;
  }
  function renderStrip() {
    track.textContent = '';
    state.list.forEach(function (item, i) { track.appendChild(thumbFor(item, i)); });
    stripCount.textContent = state.list.length + '件';
    track.scrollLeft = 0;
    arrowsLater();
  }

  /* ---------- selection ---------- */
  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function setSrc(img, src) { if (src) img.src = src; else img.removeAttribute('src'); }
  function fill(item, i) {
    var kind = KINDS[item.kind];
    feature.setAttribute('data-kind', item.kind);
    feature.classList.toggle('is-portrait', !!item.portrait);
    setSrc(visualImg, item.visual || item.thumb);
    setSrc(visualFill, item.portrait ? (item.thumb || item.visual) : '');
    visualPlay.textContent = item.kind === 'manga' ? '読む' : '再生';
    kindEl.textContent = kind.label;
    countEl.textContent = pad(i + 1) + ' / ' + pad(state.list.length);
    titleEl.textContent = item.title;
    tagsEl.textContent = '';
    item.tags.forEach(function (t) { tagsEl.appendChild(el('li', '', t)); });
    tagsEl.hidden = !item.tags.length;
    descEl.textContent = item.description;
    descEl.hidden = !item.description;
    descEl.classList.remove('is-open');
    moreBtn.textContent = '続きを読む';
    moreBtn.setAttribute('aria-expanded', 'false');
    usesList.textContent = '';
    item.uses.forEach(function (u) { usesList.appendChild(el('li', '', u)); });
    usesEl.hidden = !item.uses.length;
    openBtn.textContent = item.playlist ? 'プレイリストを見る' : kind.open;
    var arrow = el('span', 'cxw-open__icon', item.kind === 'manga' ? '→' : '▶');
    arrow.setAttribute('aria-hidden', 'true');
    openBtn.appendChild(arrow);
    // 「続きを読む」 only when the text is longer than the clamp.
    moreBtn.hidden = true;
    if (item.description) requestAnimationFrame(function () { moreBtn.hidden = descEl.scrollHeight <= descEl.clientHeight + 2; });
    setBackdrop(item.thumb || item.visual);
  }
  var switching = 0;
  function select(i, opts) {
    opts = opts || {};
    if (!state.list.length) return;
    i = Math.max(0, Math.min(state.list.length - 1, i));
    var opts_ = Array.prototype.slice.call(track.children);
    opts_.forEach(function (o, k) {
      o.setAttribute('aria-selected', String(k === i));
      o.tabIndex = k === i ? 0 : -1;
    });
    if (opts.focus && opts_[i]) opts_[i].focus({ preventScroll: true });
    if (opts_[i] && opts.reveal !== false) reveal(opts_[i]);
    if (i === state.index && !opts.force) return;
    state.index = i;
    var item = state.list[i];
    var mine = ++switching;
    if (reduced.matches || opts.instant) { fill(item, i); feature.classList.remove('is-switching'); return; }
    feature.classList.add('is-switching');
    setTimeout(function () {
      if (mine !== switching) return;
      fill(item, i);
      requestAnimationFrame(function () { if (mine === switching) feature.classList.remove('is-switching'); });
    }, FADE);
  }
  /** Scroll the strip (only the strip, never the page) so the option is fully in view. */
  function reveal(opt) {
    var gap = 24;
    var left = opt.offsetLeft, right = left + opt.offsetWidth;
    var to = null;
    if (left < track.scrollLeft + gap) to = left - gap;
    else if (right > track.scrollLeft + track.clientWidth - gap) to = right - track.clientWidth + gap;
    if (to !== null) track.scrollTo({ left: Math.max(0, to), behavior: reduced.matches ? 'auto' : 'smooth' });
  }
  function page(dir) {
    track.scrollBy({ left: dir * track.clientWidth * 0.8, behavior: reduced.matches ? 'auto' : 'smooth' });
  }
  var arrowFrame = 0;
  function arrowsLater() {
    if (arrowFrame || !track) return;
    arrowFrame = requestAnimationFrame(function () {
      arrowFrame = 0;
      var max = track.scrollWidth - track.clientWidth;
      prevBtn.disabled = track.scrollLeft <= 2;
      nextBtn.disabled = track.scrollLeft >= max - 2;
      strip.classList.toggle('is-scrollable', max > 2);
    });
  }
  function onStripKey(e) {
    var to = null;
    if (e.key === 'ArrowRight') to = state.index + 1;
    else if (e.key === 'ArrowLeft') to = state.index - 1;
    else if (e.key === 'Home') to = 0;
    else if (e.key === 'End') to = state.list.length - 1;
    else if (e.key === 'Enter') { e.preventDefault(); open(e.target.closest('[role="option"]') || openBtn); return; }
    else if (e.key === ' ') { e.preventDefault(); return; }
    if (to === null) return;
    e.preventDefault();
    select(to, { focus: true });
  }
  /** Mouse drag scrolls the strip sideways; touch keeps native swipe. A drag never selects. */
  function bindDrag() {
    var drag = null, swallow = false;
    track.addEventListener('pointerdown', function (e) {
      swallow = false;
      if (e.pointerType !== 'mouse' || e.button !== 0) return;
      drag = { x: e.clientX, left: track.scrollLeft, id: e.pointerId, moved: false };
    });
    track.addEventListener('pointermove', function (e) {
      if (!drag) return;
      var dx = e.clientX - drag.x;
      if (!drag.moved && Math.abs(dx) > 6) {
        drag.moved = true;
        track.classList.add('is-dragging');
        try { track.setPointerCapture(drag.id); } catch (err) { /* pointer already gone */ }
      }
      if (drag.moved) track.scrollLeft = drag.left - dx;
    });
    function end() {
      if (!drag) return;
      if (drag.moved) swallow = true;
      track.classList.remove('is-dragging');
      drag = null;
    }
    track.addEventListener('pointerup', end);
    track.addEventListener('pointercancel', end);
    track.addEventListener('lostpointercapture', end);
    track.addEventListener('click', function (e) {
      if (swallow) { swallow = false; return; }
      var opt = e.target.closest('[role="option"]');
      if (opt) select(Number(opt.getAttribute('data-index')), { focus: true });
    });
  }

  /* ---------- filters (tabs) ---------- */
  var tabs = Array.prototype.slice.call(filterBar.querySelectorAll('[data-cxw-filter]'));
  function listFor(filter) { return filter === 'all' ? all : (groups[filter] || []); }
  function setFilter(filter, focus) {
    var visible = tabs.filter(function (t) { return !t.hidden; });
    visible.forEach(function (t) {
      var on = t.getAttribute('data-cxw-filter') === filter;
      t.setAttribute('aria-selected', String(on));
      t.tabIndex = on ? 0 : -1;
      if (on && focus) t.focus();
    });
    if (filter === state.filter && state.index >= 0) return;
    state.filter = filter;
    state.list = listFor(filter);
    state.index = -1;
    gallery.setAttribute('aria-labelledby', 'cxw-tab-' + filter);
    var swap = function () { renderStrip(); select(0, { force: true, instant: true, reveal: false }); };
    if (reduced.matches || !track.children.length) { swap(); return; }
    gallery.classList.add('is-switching');
    setTimeout(function () {
      swap();
      requestAnimationFrame(function () { gallery.classList.remove('is-switching'); });
    }, FADE);
  }
  tabs.forEach(function (t) {
    t.addEventListener('click', function () { setFilter(t.getAttribute('data-cxw-filter'), false); });
    t.addEventListener('keydown', function (e) {
      var visible = tabs.filter(function (x) { return !x.hidden; });
      var i = visible.indexOf(t), to = null;
      if (e.key === 'ArrowRight') to = (i + 1) % visible.length;
      if (e.key === 'ArrowLeft') to = (i - 1 + visible.length) % visible.length;
      if (e.key === 'Home') to = 0;
      if (e.key === 'End') to = visible.length - 1;
      if (to === null) return;
      e.preventDefault();
      setFilter(visible[to].getAttribute('data-cxw-filter'), true);
    });
  });

  /* ---------- open: the page's one work viewer (js/cx-works.js) ---------- */
  function open(trigger) {
    var item = state.list[state.index];
    if (item) window.cxWorks.open(item, trigger || openBtn);
  }

  /* ---------- start ---------- */
  function fail(message) {
    gallery.removeAttribute('aria-busy');
    var note = el('p', 'cxw-message', message);
    note.setAttribute('role', 'status');
    gallery.insertBefore(note, gallery.firstChild);
  }
  var EMPTY = '作品は準備中です。各サービスのページからご覧ください。';
  var FAILED = '作品を読み込めませんでした。各サービスのページからご覧ください。';
  function byKind(items) {
    var out = { manga: [], anime: [], video: [] };
    items.forEach(function (it) { if (out[it.kind]) out[it.kind].push(it); });
    return out;
  }
  function show(list, kinds, note) {
    all = list;
    groups = kinds;
    tabs.forEach(function (t) {
      var f = t.getAttribute('data-cxw-filter');
      var n = listFor(f).length;
      t.hidden = !n;
      var count = t.querySelector('.cxw-filters__count');
      if (count) count.textContent = String(n);
    });
    buildGallery();
    filterBar.hidden = false;
    gallery.setAttribute('role', 'tabpanel');
    gallery.removeAttribute('aria-busy');
    root.classList.add('cxw-ready');
    setFilter('all', false);
    if (note) fail(note);
  }
  /** WordPress without the Creative X slots (404): the older lists, mixed round-robin. */
  function older() {
    window.cxWorks.load().then(function (data) {
      var failed = data.failed;
      var kinds = { manga: data.manga, anime: data.anime, video: data.video };
      var list = mix(kinds, mixPattern());
      if (!list.length) { fail(failed.works && failed.videos ? FAILED : EMPTY); return; }
      show(list, kinds, failed.works || failed.videos ? (failed.works ? 'マンガ' : '動画') + 'を読み込めませんでした。表示できる作品だけを並べています。' : '');
    });
  }
  gallery.setAttribute('aria-busy', 'true');
  window.cxWorks.slot('cx-creative-works').then(function (res) {
    if (res.state === 'missing') { older(); return; }
    if (res.state === 'error') { fail(FAILED); return; }
    if (res.state === 'empty') { fail(EMPTY); return; }
    show(res.items.slice(), byKind(res.items), '');
  });
})();
