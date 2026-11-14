/* cxWorks — Creative X works from WordPress, and the one work viewer of the Creative X landing (2026-11).
   Used by the HERO (js/service-creative-hero.js), WORKS (js/service-creative-works.js) and 01 CREATIVE
   SOLUTION (js/service-creative-solution.js): they read their works here and open them with cxWorks.open,
   so the page has one data mapping and one viewer.
   Load after js/wp-config.js, js/cx-dom.js, js/cx-manga-reader.js and js/cx-video-player.js (defer, in order).

   Data — WordPress placement slots (「サイトの表示 ＞ ContentsX ＞ Creative X」, plugin docs/DESIGN-content-library.md
     §17): cxWorks.slot(key) → GET /slots/<key> once per key, resolves (never rejects) to { state, items }:
       ok       200 with works to show (items in WordPress order; WordPress neither re-orders nor fills in)
       empty    200 with items: [] — nothing is set there in WordPress: show nothing in its place, never a
                stand-in work (each section has its own empty look)
       missing  404 — this WordPress does not have the key (the plugin with the Creative X slots is not
                released yet, or a typo). A console warning; the sections then use the older lists below
                (cxWorks.load) so the page still works. Not a finished state: check the real API after release.
       error    network error, time-out, 5xx or an answer without `items`: the sections keep their own
                failure look (the static links in the HTML), distinct from "empty"
     Keys: cx-creative-hero (MP4s for the HERO, ≤3, in play order), cx-creative-works (WORKS, manga and
     video mixed; `format_key` manga / anime / video), cx-creative-solution-{manga,anime,video} (≤1 each).
     A card becomes the item below (fromCard): manga reads `manga.gallery` / `manga.view_type` (the reader's
     work, no /manga/{id} call); video reads `video.provider` / `video_id` / `src`, and `file` (a WordPress
     media MP4) plays as `mp4` with `src`. Cards that cannot be shown or played are left out (warning).
   Older lists (the 404 transition only) — cxWorks.load() asks WordPress once per page and resolves to
     { manga: [...], anime: [...], video: [...], failed: { works: bool, videos: bool } }
     manga  GET /works?site=contentsx — works that have pages (`gallery`), in WordPress order
     anime  GET /bizanime-videos — `viewer` rows of type bizanime → `cases` (YouTube) → `playlists` of type bizanime
     video  the same response — `viewer` rows of type bizvideo → `playlists` of type bizvideo
     Videos the shared player cannot play are left out; a title seen twice is kept once (YouTube wins over
     Drive / MP4). Nothing is written as HTML. cxWorks.find(data, kind, id) returns one item or null.
     Every item has one shape, whatever it came from:
       kind         'manga' | 'anime' | 'video' (a HERO card, which has no format, is 'video')
       id           work ID / slug (manga), video_id or playlist_id (video); postId: the WordPress post (slots)
       title, description, tags[], uses[]          text only
       visual       large picture (manga: page 1; YouTube: maxresdefault; else the poster)
       thumb        small picture (manga: the thumbnail or page 1; YouTube: hqdefault)
       portrait     true for manga (page 1 is shown whole)
       manga only   cover (page 1), work (the WordPress work: gallery, view_type, title_ja … for the reader)
                    — or pages[] + viewType instead of work
       video only   media (CxVideoPlayer item: provider youtube | youtube_playlist | drive | mp4, video_id, src,
                    poster), poster (= visual), playlist (bool)
   Viewer — cxWorks.open(item, opener) shows the work in a dialog on the page (title, kind, dark backdrop,
     close button, the shared loading / error states), with a view that fits the format:
     MANGA  an open book — CxMangaReader in book mode (BizManga biz-library's 3D page flip, right-bound
            spreads on wide screens, one page with the mobile flip on phones, vertical works keep their
            scroll; page number, ‹ ›, ← →, click halves, swipe, 拡大). css/cx-manga-book.css
     ANIME / VIDEO  a phone lying on its side, with CxVideoPlayer on its screen, started at once because the
            visitor just asked for it (the YouTube embed is created now, never on page load).
            The phone is 3D (js/cx-phone-3d.js, three.js, imported now): it comes in tilted and turns to face
            the visitor (0.9s), then stands still and the player shows exactly on its screen, with all its
            controls. The CSS phone (css/cx-works.css) is used instead when WebGL2 is missing or would run in
            software, on Save-Data / 2G or a low-end device, if the module does not arrive within PHONE_WAIT,
            or if the GPU drops the context. Reduced motion: no entrance. On a phone the frame thins to a
            bezel so the video gets the width. Only pictures whose host allows CORS are drawn on the 3D
            screen (YouTube stills, this site); WordPress uploads do not (2026-11), so for those the screen
            shows a quiet placeholder until the player appears — never a black or broken texture.
     There is one dialog for the page: opening a work replaces the one that is open. 閉じる / Esc / a click
     outside close it; the embed is removed (the video and its sound stop), the 3D phone and its WebGL
     context are released, the page goes back to where it was and focus returns to the opener. While it is
     open the rest of the page is inert and does not scroll, and the document gets
     `cxworks:viewer` { open, kind } (the HERO background video pauses). Esc during 拡大 closes 拡大 first. */
(function () {
  'use strict';
  if (!window.cxDom) return; // js/cx-dom.js が先に読まれていない（カードはサービスへのリンクのまま）
  var el = window.cxDom.el;
  var text = window.cxDom.text;
  var safeImage = window.cxDom.safeImage;
  var iconButton = window.cxDom.iconButton;
  var TIMEOUT = 8000;
  var MANGA_HOSTS = ['cms.contentsx.jp', 'contentsx.jp'];
  var KIND_LABELS = { manga: 'MANGA', anime: 'ANIME', video: 'VIDEO' };
  var CASE_LABELS = { MUSIC_VIDEO: 'ミュージックビデオ', IP: 'オリジナルIP', ADVERTISING: '広告', VTUBER: 'VTuber・配信', VFX: 'VFX' };
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)');

  /* ---------- data ---------- */
  function uniq(list) {
    var seen = {};
    return list.filter(function (v) { if (!v || seen[v]) return false; seen[v] = 1; return true; });
  }
  function ytImage(id, size) { return 'https://i.ytimg.com/vi/' + id + '/' + size + '.jpg'; }
  function mangaItems(works) {
    return (Array.isArray(works) ? works : []).map(function (w) {
      if (!w || !Array.isArray(w.gallery) || !w.gallery.length) return null;
      var cover = safeImage(w.gallery[0], MANGA_HOSTS);
      var title = text(w.title_ja);
      if (!cover || !title) return null;
      var pages = w.spec && /^\d{1,3}P$/.test(text(w.spec.pages)) ? text(w.spec.pages).replace('P', 'ページ') : '';
      return {
        kind: 'manga', id: text(w.id), title: title, work: w, portrait: true,
        cover: cover, visual: cover, thumb: safeImage(w.thumbnail, MANGA_HOSTS) || cover,
        tags: uniq([text(w.subtitle_ja)].concat(Array.isArray(w.categories) ? w.categories.map(text) : [], [pages])).slice(0, 4),
        description: text(w.point),
        uses: uniq(Array.isArray(w.media) ? w.media.map(text) : []).slice(0, 6)
      };
    }).filter(Boolean);
  }
  function videoItem(kind, v, tags, provider) {
    if (!v) return null;
    var list = provider === 'youtube_playlist';
    var media = { title: text(v.title), description: text(v.description), provider: provider || v.provider,
      video_id: text(list ? v.playlist_id : v.video_id), src: text(v.src), poster: text(v.poster) };
    if (!media.title || !window.CxVideoPlayer || !window.CxVideoPlayer.playable([media]).length) return null;
    var yt = media.provider === 'youtube';
    var visual = yt ? ytImage(media.video_id, 'maxresdefault') : safeImage(media.poster);
    return {
      kind: kind, id: media.video_id, title: media.title, description: media.description, media: media, playlist: list,
      portrait: false, visual: visual, poster: visual, thumb: yt ? ytImage(media.video_id, 'hqdefault') : visual,
      tags: (tags || []).filter(Boolean), uses: []
    };
  }
  /** Keep the first of each title; a YouTube copy replaces a Drive / MP4 one in place. */
  function dedupe(items) {
    var out = [], at = {};
    items.forEach(function (it) {
      if (!it) return;
      var key = it.title.replace(/\s+/g, '');
      if (!(key in at)) { at[key] = out.length; out.push(it); return; }
      if (out[at[key]].media.provider !== 'youtube' && it.media.provider === 'youtube') out[at[key]] = it;
    });
    return out;
  }
  function videoGroups(videos) {
    var viewer = videos && Array.isArray(videos.viewer) ? videos.viewer : [];
    var cases = videos && Array.isArray(videos.cases) ? videos.cases : [];
    var lists = videos && Array.isArray(videos.playlists) ? videos.playlists : [];
    function fromViewer(type, kind) {
      return viewer.filter(function (v) { return v && v.type === type; }).map(function (v) { return videoItem(kind, v, []); });
    }
    function fromLists(type, kind) {
      return lists.filter(function (p) { return p && p.type === type; })
        .map(function (p) { return videoItem(kind, p, ['プレイリスト'], 'youtube_playlist'); });
    }
    return {
      anime: dedupe(fromViewer('bizanime', 'anime')
        .concat(cases.map(function (c) { return c && c.provider === 'youtube' ? videoItem('anime', c, [CASE_LABELS[text(c.category)]]) : null; }))
        .concat(fromLists('bizanime', 'anime'))),
      video: dedupe(fromViewer('bizvideo', 'video').concat(fromLists('bizvideo', 'video')))
    };
  }
  var loading = null;
  function load() {
    if (loading) return loading;
    var wp = typeof WP_CONFIG !== 'undefined' && WP_CONFIG.enabled !== false && WP_CONFIG.apiBase;
    var ask = function (path) { return wp ? window.cxDom.getJSON(path, TIMEOUT, 'Creative X works') : Promise.resolve(null); };
    loading = Promise.all([ask('/works?site=contentsx'), ask('/bizanime-videos')]).then(function (res) {
      var vids = videoGroups(res[1]);
      return { manga: mangaItems(res[0]), anime: vids.anime, video: vids.video,
        failed: { works: !Array.isArray(res[0]), videos: !res[1] || typeof res[1] !== 'object' } };
    });
    return loading;
  }
  function find(data, kind, id) {
    var list = data && Array.isArray(data[kind]) ? data[kind] : [];
    for (var i = 0; i < list.length; i++) { if (id && list[i].id === id) return list[i]; }
    return null;
  }
  /* ---------- placement slots ---------- */
  /** One card of GET /slots/<key> → an item of the shape above; null when it cannot be shown or played. */
  function fromCard(c) {
    if (!c || typeof c !== 'object') return null;
    var title = text(c.title);
    if (!title) return null;
    var description = text(c.description);
    var postId = typeof c.id === 'number' || typeof c.id === 'string' ? String(c.id) : '';
    if (c.kind === 'manga') {
      var m = c.manga && typeof c.manga === 'object' ? c.manga : {};
      var pages = (Array.isArray(m.gallery) ? m.gallery : []).map(function (u) { return safeImage(u, MANGA_HOSTS); }).filter(Boolean);
      if (!pages.length) return null;
      return {
        kind: 'manga', id: text(c.slug) || postId, postId: postId, title: title, description: description, portrait: true,
        cover: pages[0], visual: pages[0], thumb: safeImage(c.thumb, MANGA_HOSTS) || pages[0],
        work: { title_ja: title, gallery: pages, view_type: text(m.view_type) },
        tags: uniq(Array.isArray(c.category) ? c.category.map(text) : []).slice(0, 4), uses: []
      };
    }
    if (c.kind !== 'video') return null;
    var v = c.video && typeof c.video === 'object' ? c.video : {};
    var provider = text(v.provider);
    var file = provider === 'file';                // a WordPress media MP4: the player knows it as mp4
    var media = { title: title, description: description, provider: file ? 'mp4' : provider, video_id: text(v.video_id),
      src: file || provider === 'mp4' ? text(v.src) : '', poster: text(c.thumb) };
    if (!window.CxVideoPlayer || !window.CxVideoPlayer.playable([media]).length) return null;
    var visual = safeImage(c.thumb);
    var playlist = provider === 'youtube_playlist';
    return {
      kind: c.format_key === 'anime' || c.format_key === 'video' ? c.format_key : 'video',
      id: media.video_id || postId, postId: postId, title: title, description: description, media: media, playlist: playlist,
      portrait: false, visual: visual, poster: visual, thumb: provider === 'youtube' ? ytImage(media.video_id, 'hqdefault') : visual,
      tags: playlist ? ['プレイリスト'] : [], uses: []
    };
  }
  var slots = {};
  function slot(key) {
    if (slots[key]) return slots[key];
    var wp = typeof WP_CONFIG !== 'undefined' && WP_CONFIG.enabled !== false && WP_CONFIG.apiBase && window.cxDom.getJSONStatus;
    if (!wp) return (slots[key] = Promise.resolve({ state: 'error', items: [] }));
    slots[key] = window.cxDom.getJSONStatus('/slots/' + encodeURIComponent(key), TIMEOUT, 'Creative X ' + key).then(function (r) {
      if (r.status === 404) {
        console.warn('[Creative X] WordPress has no slot "' + key + '" (404): the Creative X slots are not released there yet. Using the older lists.');
        return { state: 'missing', items: [] };
      }
      if (!r.data || !Array.isArray(r.data.items)) return { state: 'error', items: [] };
      var items = r.data.items.map(fromCard).filter(Boolean);
      if (items.length < r.data.items.length) console.warn('[Creative X] ' + (r.data.items.length - items.length) + ' card(s) of "' + key + '" cannot be shown here and were left out.');
      return { state: items.length ? 'ok' : 'empty', items: items };
    });
    return slots[key];
  }
  /** The 3D phone draws its screen in WebGL, which needs CORS: YouTube's stills and this site (GitHub Pages
      sends Access-Control-Allow-Origin: *) have it; WordPress uploads do not (2026-11). '' = no picture. */
  var GL_HOSTS = ['i.ytimg.com', 'contentsx.jp', 'www.contentsx.jp'];
  function glPicture(src) {
    if (!src) return '';
    try {
      var u = new URL(src, location.href);
      return u.origin === location.origin || (u.protocol === 'https:' && GL_HOSTS.indexOf(u.hostname) !== -1) ? u.href : '';
    } catch (e) { return ''; }
  }

  /** YouTube answers a missing maxresdefault with a 120×90 grey placeholder: fall back to hqdefault. */
  function poster(img, src) {
    img.addEventListener('load', function () {
      if (img.naturalWidth <= 120 && /\/maxresdefault\.jpg$/.test(img.src)) img.src = img.src.replace(/maxresdefault\.jpg$/, 'hqdefault.jpg');
    });
    img.src = src;
  }

  /* ---------- viewer dialog ---------- */
  var dialog = null, kindEl, titleEl, body, closeBtn, instance = null, opener = null, inerted = [], scrollTop = 0, hideTimer = 0;
  var CLOSE_MS = 200;   // the fade-out in css/cx-works.css
  function announce(open, kind) {
    var e;
    try { e = new CustomEvent('cxworks:viewer', { detail: { open: open, kind: kind || '' } }); } catch (x) { return; }
    document.dispatchEvent(e);
  }
  function build() {
    dialog = el('div', 'cxwv');
    dialog.hidden = true;
    dialog.setAttribute('role', 'dialog');
    dialog.setAttribute('aria-modal', 'true');
    dialog.setAttribute('aria-labelledby', 'cxwv-title');
    var panel = el('div', 'cxwv-panel');
    var head = el('div', 'cxwv-head');
    var heading = el('div', 'cxwv-heading');
    kindEl = el('p', 'cxwv-kind');
    kindEl.setAttribute('data-i18n-skip', '');
    titleEl = el('h2', 'cxwv-title');
    titleEl.id = 'cxwv-title';
    titleEl.setAttribute('data-i18n-skip', '');
    heading.appendChild(kindEl); heading.appendChild(titleEl);
    closeBtn = iconButton('cxwv-close', '閉じる', '×');
    head.appendChild(heading); head.appendChild(closeBtn);
    body = el('div', 'cxwv-body');
    panel.appendChild(head); panel.appendChild(body);
    dialog.appendChild(panel);
    closeBtn.addEventListener('click', function () { close(); });
    dialog.addEventListener('click', function (e) { if (e.target === dialog) close(); });
    // The reader turns pages with ← → while its page area has focus; in the dialog they work from the
    // buttons and the close button too.
    dialog.addEventListener('keydown', function (e) {
      if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
      var stage = body.querySelector('.cxmr-stage');
      if (!stage || stage.contains(e.target)) return;
      e.preventDefault();
      stage.dispatchEvent(new KeyboardEvent('keydown', { key: e.key }));
    });
    document.body.appendChild(dialog);
  }
  function lock(on) {
    var html = document.documentElement;
    if (on) {
      // Focus stays in the dialog: everything else is inert. The reader's 拡大 moves itself to <body>
      // later, so it is not caught by this.
      inerted = Array.prototype.filter.call(document.body.children, function (n) {
        return n !== dialog && !n.inert && n.tagName !== 'SCRIPT';
      });
      inerted.forEach(function (n) { n.inert = true; });
      html.classList.add('cxwv-lock');
      return;
    }
    inerted.forEach(function (n) { n.inert = false; });
    inerted = [];
    html.classList.remove('cxwv-lock');
  }
  function close() {
    if (!dialog || dialog.hidden || dialog.classList.contains('is-closing')) return;
    if (instance) { if (instance.stop) instance.stop(); instance.destroy(); instance = null; }
    flat();                                      // releases the 3D phone and its WebGL context
    body.textContent = '';                       // removes the embed: the video and its sound stop now
    dialog.classList.remove('is-open');
    dialog.classList.add('is-closing');
    hideTimer = setTimeout(function () { dialog.hidden = true; dialog.classList.remove('is-closing'); }, CLOSE_MS);
    lock(false);
    if (Math.abs(window.scrollY - scrollTop) > 1) {
      // 'instant' beats a page-wide smooth scroll; browsers that do not know it throw, so fall back.
      try { window.scrollTo({ top: scrollTop, behavior: 'instant' }); } catch (e) { window.scrollTo(0, scrollTop); }
    }
    if (opener && document.contains(opener)) opener.focus({ preventScroll: true });
    opener = null;
    announce(false);
  }
  function open(item, from) {
    if (!item || !window.CxMangaReader || !window.CxVideoPlayer) return false;
    if (!dialog) build();
    var back = from || document.activeElement;
    close();                                     // one dialog at a time
    clearTimeout(hideTimer);
    dialog.classList.remove('is-closing');
    opener = back;
    scrollTop = window.scrollY;
    dialog.setAttribute('data-kind', item.kind);
    kindEl.textContent = KIND_LABELS[item.kind] + (item.playlist ? ' / PLAYLIST' : '');
    titleEl.textContent = item.title;
    lock(true);
    announce(true, item.kind);
    dialog.hidden = false;
    requestAnimationFrame(function () { if (!dialog.hidden) dialog.classList.add('is-open'); });
    if (item.kind === 'manga') {
      var box = el('div', 'cxwv-reader');
      body.appendChild(box);
      var work = item.work || { title_ja: item.title, gallery: item.pages, view_type: item.viewType };
      instance = window.CxMangaReader(box, work, { wide: function () { return window.innerWidth >= 769; }, book: true });
      (box.querySelector('.cxmr-stage') || closeBtn).focus({ preventScroll: true });
    } else {
      var device = phone();
      var screen = device.querySelector('.cxwv-phone__screen');
      instance = window.CxVideoPlayer(screen, [item.media], { max: 1 });
      if (instance.play) instance.play(0);       // the visitor just pressed 「動画を見る」
      closeBtn.focus({ preventScroll: true });
      if (can3d()) depth(device, item);
    }
    return true;
  }
  /** A phone lying on its side: frame, camera and keys are drawing only; the player goes on the screen. */
  function phone() {
    var device = el('div', 'cxwv-phone');
    var frame = el('div', 'cxwv-phone__frame');
    var screen = el('div', 'cxwv-phone__screen');
    var camera = el('span', 'cxwv-phone__camera');
    camera.setAttribute('aria-hidden', 'true');
    frame.appendChild(camera);
    frame.appendChild(screen);
    device.appendChild(frame);
    ['vol-up', 'vol-down', 'power'].forEach(function (key) {
      var k = el('span', 'cxwv-phone__key cxwv-phone__key--' + key);
      k.setAttribute('aria-hidden', 'true');
      device.appendChild(k);
    });
    body.appendChild(device);
    return device;
  }

  /* ---------- the 3D phone (js/cx-phone-3d.js) ----------
     The CSS phone above keeps its layout; with .is-3d its drawing gives way to the WebGL phone, and its
     screen (the player) shows once the 3D phone faces the visitor (.is-settled). */
  var PHONE_3D = '/js/cx-phone-3d.js';
  var PHONE_WAIT = 4000;   // ms: the CSS phone is shown if the module has not arrived by then
  var phoneModule = null, phone3d = null, phoneToken = 0, phoneTimer = 0;
  function can3d() {
    if (typeof window.WebGL2RenderingContext !== 'function') return false;
    var c = navigator.connection;
    if (c && (c.saveData || /(^|-)2g$/.test(c.effectiveType || ''))) return false;
    if (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 2) return false;
    if (navigator.deviceMemory && navigator.deviceMemory <= 1) return false;
    return true;
  }
  /** Fetch the module ahead (pointer or focus on an open button); it builds nothing until a video opens. */
  function warm() {
    if (!phoneModule && can3d()) {
      phoneModule = import(PHONE_3D);
      phoneModule.catch(function () {});
    }
    return phoneModule;
  }
  function depth(device, item) {
    var mine = ++phoneToken;
    device.classList.add('is-3d');
    dialog.classList.add('is-3d');
    clearTimeout(phoneTimer);
    phoneTimer = setTimeout(function () { if (mine === phoneToken && !phone3d) flat(); }, PHONE_WAIT);
    warm().then(function (mod) {
      if (mine !== phoneToken || !device.classList.contains('is-3d')) return;
      clearTimeout(phoneTimer);
      try {
        phone3d = mod.mount({
          host: dialog, frame: device.querySelector('.cxwv-phone__frame'), screen: device.querySelector('.cxwv-phone__screen'),
          poster: glPicture(item.poster), reduced: reduced.matches,
          onSettle: function () { if (mine === phoneToken) device.classList.add('is-settled'); },
          onLost: function () { if (mine === phoneToken) { phone3d = null; flat(); } }
        });
      } catch (e) { phone3d = null; }
      if (!phone3d) flat();
    }, function () { if (mine === phoneToken) flat(); });
  }
  /** Back to the CSS phone (and the end of the 3D one: on close, or when it cannot be used). */
  function flat() {
    phoneToken++;
    clearTimeout(phoneTimer);
    if (phone3d) { phone3d.destroy(); phone3d = null; }
    if (!dialog) return;
    dialog.classList.remove('is-3d');
    Array.prototype.forEach.call(dialog.querySelectorAll('.cxwv-gl'), function (c) { c.remove(); });   // left by a failed start
    var device = body.querySelector('.cxwv-phone');
    if (device) device.classList.remove('is-3d', 'is-settled');
  }
  // Capture phase: while the reader is enlarged, its own Esc handler closes 拡大 first.
  window.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape' || !window.cxWorks.isOpen()) return;
    if (document.querySelector('.cxmr.is-full')) return;
    e.preventDefault();
    close();
  }, true);

  window.cxWorks = {
    slot: slot, load: load, find: find, poster: poster, open: open, close: close, warm: warm,
    isOpen: function () { return !!dialog && !dialog.hidden && !dialog.classList.contains('is-closing'); }
  };
})();
