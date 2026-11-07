/* Creative X: the three cards below switch the main viewer above (Issue #97).
   - BizManga: an inline manga reader (js/cx-manga-reader.js) for the manga chosen in WordPress
     (「サイトの表示 → ContentsX → トップページ → Creative X のマンガ」 GET /slots/cx-top-manga → its work ID →
     GET /manga/{ID}; 2026-11-07). When that slot is empty or cannot be read: the first ContentsX manga in
     WordPress order (GET /works?site=contentsx — `gallery` / `view_type`).
   - BizAnime / BizVideo: the shared inline player (js/cx-video-player.js) with three videos each.
     Source: GET /bizanime-videos → `viewer` (WP「CREATIVE X ビューワー動画」, enabled + admin order;
     the player shows the first three playable per type). Until a type has viewer videos: BizAnime
     uses its playlists and then the existing `cases`, BizVideo its playlists.
   In the HTML the cards are plain links to each service and the panel links to BizAnime, so the
   section still works without JS. This script turns the cards into tabs (initial: BizAnime).
   Switching fades the panel (200ms) and rebuilds it, which stops any video and resets the reader.
   Nothing autoplays. When the data cannot be loaded the panel says so and links to the service. */
(function () {
  'use strict';
  var root = document.querySelector('[data-cxcx]');
  if (!root || typeof WP_CONFIG === 'undefined' || WP_CONFIG.enabled === false || !WP_CONFIG.apiBase) return;
  var panel = root.querySelector('[data-cxcx-panel]');
  var list = root.querySelector('.cxcx-cards');
  var tabs = Array.prototype.slice.call(root.querySelectorAll('.cxcx-card[data-cxcx-service]'));
  if (!panel || !list || !tabs.length || !window.CxVideoPlayer || !window.CxMangaReader || !window.cxDom) return;

  var TIMEOUT = 8000;
  var FADE = 200;
  var LINKS = {
    manga: { label: 'ビズマンガで作品を見る', href: 'https://bizmanga.contentsx.jp/biz-library' },
    bizanime: { label: 'ビズアニメの作品を見る', href: 'https://bizmanga.contentsx.jp/bizanime' },
    bizvideo: { label: 'ビズビデオを見る', href: '/services/#bizvideo' }
  };
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  var data = null;
  var active = null;
  var instance = null;
  var token = 0;

  function getJSON(path) { return window.cxDom.getJSON(path, TIMEOUT, 'Creative X'); }
  var text = window.cxDom.text;
  var el = window.cxDom.el;

  /* ---------- data ---------- */
  function viewerItems(videos, type) {
    return (videos && Array.isArray(videos.viewer) ? videos.viewer : []).filter(function (v) { return v && v.type === type; })
      .map(function (v) {
        return { title: text(v.title), description: text(v.description), provider: v.provider, video_id: text(v.video_id), src: text(v.src), poster: text(v.poster) };
      });
  }
  function playlists(videos, type) {
    return (videos && Array.isArray(videos.playlists) ? videos.playlists : []).filter(function (p) { return p && p.type === type; })
      .map(function (p) { return { title: text(p.title), description: '', provider: 'youtube_playlist', video_id: text(p.playlist_id), poster: text(p.poster) }; });
  }
  function cases(videos) {
    return (videos && Array.isArray(videos.cases) ? videos.cases : []).filter(function (v) { return v && v.provider === 'youtube'; })
      .map(function (v) { return { title: text(v.title), description: '', provider: 'youtube', video_id: text(v.video_id), poster: text(v.poster) }; });
  }
  function readable(w) { return !!(w && Array.isArray(w.gallery) && w.gallery.length); }
  /* The work ID from the slot card (`slug`). Only the characters the /manga/{ID} route accepts. */
  function chosenId(slot) {
    var card = slot && Array.isArray(slot.items) ? slot.items[0] : null;
    var id = card && typeof card.slug === 'string' ? card.slug : '';
    return /^[a-z0-9-]{1,100}$/.test(id) ? id : '';
  }
  function prepare(videos, works, chosen) {
    var anime = viewerItems(videos, 'bizanime');
    var film = viewerItems(videos, 'bizvideo');
    var manga = readable(chosen) ? chosen : (Array.isArray(works) ? works : []).filter(readable)[0] || null;
    return {
      bizanime: anime.length ? anime : playlists(videos, 'bizanime').concat(cases(videos)),
      bizvideo: film.length ? film : playlists(videos, 'bizvideo'),
      manga: manga,
      videosFailed: !videos,
      worksFailed: !Array.isArray(works) && !readable(chosen)
    };
  }

  /* ---------- panel ---------- */
  function message(service, textContent) {
    var box = el('div', 'cxcx-message');
    box.setAttribute('role', 'status');
    box.appendChild(el('p', '', textContent));
    var a = el('a', '', LINKS[service].label);
    a.href = LINKS[service].href;
    box.appendChild(a);
    return box;
  }
  function build(service) {
    if (instance) instance.destroy();
    instance = null;
    panel.textContent = '';
    panel.setAttribute('data-service', service);
    if (!data) {
      var wait = el('div', 'cxcx-message', '読み込み中…');
      wait.setAttribute('role', 'status');
      panel.appendChild(wait);
      return;
    }
    if (service === 'manga') {
      if (!data.manga) {
        panel.appendChild(message(service, data.worksFailed ? '漫画を読み込めませんでした。' : '漫画は準備中です。'));
        return;
      }
      var box = el('div', 'cxcx-reader');
      panel.appendChild(box);
      instance = window.CxMangaReader(box, data.manga, { wide: function () { return window.innerWidth >= 769; } });
      return;
    }
    if (!window.CxVideoPlayer.playable(data[service]).length) {
      panel.appendChild(message(service, data.videosFailed ? '動画を読み込めませんでした。' : '動画は準備中です。'));
      return;
    }
    var player = el('div', 'cxcx-player');
    panel.appendChild(player);
    instance = window.CxVideoPlayer(player, data[service]);
  }
  function select(service, focus) {
    if (service === active) return;
    active = service;
    tabs.forEach(function (t) {
      var on = t.getAttribute('data-cxcx-service') === service;
      t.setAttribute('aria-selected', String(on));
      t.tabIndex = on ? 0 : -1;
      if (on) { panel.setAttribute('aria-labelledby', t.id); if (focus) t.focus(); }
    });
    if (instance) instance.stop();
    var my = ++token;
    if (reduced.matches || !panel.firstChild) { build(service); return; }
    panel.classList.add('is-fading');
    setTimeout(function () {
      if (my !== token) return;
      build(service);
      // Next frame so the new content fades in from transparent.
      requestAnimationFrame(function () { if (my === token) panel.classList.remove('is-fading'); });
    }, FADE);
  }

  /* ---------- tabs: the card links become tabs (click, Space, arrows, Home/End) ---------- */
  list.setAttribute('role', 'tablist');
  list.setAttribute('aria-label', '表示するサービス');
  panel.setAttribute('role', 'tabpanel');
  tabs.forEach(function (t, i) {
    t.setAttribute('role', 'tab');
    t.setAttribute('aria-controls', panel.id);
    t.addEventListener('click', function (e) {
      // Ctrl/⌘/Shift-click still opens the service page in a new tab or window.
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.button > 0) return;
      e.preventDefault();
      select(t.getAttribute('data-cxcx-service'), false);
    });
    t.addEventListener('keydown', function (e) {
      var to = null;
      if (e.key === ' ') { e.preventDefault(); select(t.getAttribute('data-cxcx-service'), false); return; }
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') to = (i + 1) % tabs.length;
      if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') to = (i - 1 + tabs.length) % tabs.length;
      if (e.key === 'Home') to = 0;
      if (e.key === 'End') to = tabs.length - 1;
      if (to === null) return;
      e.preventDefault();
      select(tabs[to].getAttribute('data-cxcx-service'), true);
    });
  });

  root.classList.add('cxcx-enhanced');
  panel.textContent = '';  // the no-JS link gives way to「読み込み中…」without a fade
  select('bizanime', false);
  Promise.all([getJSON('/bizanime-videos'), getJSON('/works?site=contentsx'), getJSON('/slots/cx-top-manga')]).then(function (res) {
    var id = chosenId(res[2]);
    return (id ? getJSON('/manga/' + id) : Promise.resolve(null)).then(function (chosen) { return [res[0], res[1], chosen]; });
  }).then(function (res) {
    data = prepare(res[0], res[1], res[2]);
    build(active);
    root.classList.add('cxcx-ready');
  });
})();
