/* Creative X landing — 01 CREATIVE SOLUTION (css/service-creative-solution.css, SPEC.md §3.0).
   Each card shows the representative work chosen in WordPress for its service: the slot
   cx-creative-solution-<data-kind> (cxWorks.slot, js/cx-works.js; the same cards as WORKS). The script puts
   the real cover / thumbnail and title into the card and swaps its link for a button that opens the work on
   the page (cxWorks.open: manga reader / video player). The button's ::after covers the whole card, so a
   card has one control and nothing nested.
   - Empty slot (200, no items): nothing is chosen. The card keeps its link to the service and says
     「作品は準備中です」. Another work is never put in its place.
   - Failure (network, time-out, 5xx): the card keeps its link and says 「作品を読み込めませんでした」.
   - 404 (a WordPress without the Creative X slots yet): the work named by data-work-id (written by
     tools/build-services.py from data/creative-solution.json) in the older lists (cxWorks.load); if it is
     not there, the card says so — again no stand-in work. No placeholder work is ever shown.
   Backdrop: alone, the section sits on a CSS-only dark backdrop. When the page has the HERO showreel
   (css/service-creative-hero.css, other branch), its poster image is reused here, blurred and darker, so the
   HERO picture carries on without a second video. Inside the HERO stage (.cxg-stage) the section turns
   transparent and the live HERO picture shows through instead. */
(function () {
  'use strict';
  var root = document.querySelector('[data-cxcs]');
  if (!root || !window.cxDom || !window.cxWorks) return;
  var el = window.cxDom.el;
  var cards = Array.prototype.slice.call(root.querySelectorAll('[data-cxcs-card]'));
  var SVG = 'http://www.w3.org/2000/svg';
  var MESSAGES = {
    failed: ['作品を読み込めませんでした。', 'We could not load this work.'],
    empty: ['作品は準備中です。', 'Works are coming soon.']
  };

  function bilingual(node, pair) {
    node.textContent = pair[0];
    node.setAttribute('data-ja', pair[0]);
    node.setAttribute('data-en', pair[1]);
    // translateElement always writes the English text, so call it only while the page is in English.
    var i18n = window.i18n;
    if (i18n && i18n.getLang && i18n.getLang() === 'en' && i18n.translateElement) i18n.translateElement(node);
  }
  function arrow() {
    var svg = document.createElementNS(SVG, 'svg');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('aria-hidden', 'true');
    svg.setAttribute('focusable', 'false');
    var path = document.createElementNS(SVG, 'path');
    path.setAttribute('d', 'M4 12h15M13 6l6 6-6 6');
    svg.appendChild(path);
    return svg;
  }
  function picture(item, media) {
    var box = el('span', 'cxcs-card__picture');
    var broken = function () { box.remove(); media.classList.remove('has-picture'); };
    if (item.kind === 'manga') {
      // The cover is shown whole (portrait pages are never cropped); a blurred copy fills the frame.
      var fill = el('img', 'cxcs-card__cover-fill');
      var cover = el('img', 'cxcs-card__cover');
      [fill, cover].forEach(function (img) { img.alt = ''; img.decoding = 'async'; img.loading = 'lazy'; img.src = item.cover; box.appendChild(img); });
      cover.addEventListener('error', broken);
    } else {
      var thumb = el('img', 'cxcs-card__thumb');
      thumb.alt = ''; thumb.decoding = 'async'; thumb.loading = 'lazy';
      thumb.addEventListener('error', broken);
      if (item.poster) window.cxWorks.poster(thumb, item.poster);
      box.appendChild(thumb);
      var play = el('span', 'cxcs-card__play');
      play.setAttribute('aria-hidden', 'true');
      box.appendChild(play);
    }
    return box;
  }
  function fill(card, item) {
    var media = card.querySelector('[data-cxcs-media]');
    var title = card.querySelector('[data-cxcs-title]');
    var link = card.querySelector('[data-cxcs-action]');
    if (!media || !title || !link) return;
    media.appendChild(picture(item, media));
    media.classList.add('has-picture');
    title.textContent = item.title;
    title.id = card.id + '-title';
    title.hidden = false;
    var button = el('button', 'cxcs-card__action');
    button.type = 'button';
    button.setAttribute('aria-haspopup', 'dialog');
    var label = el('span');
    label.id = card.id + '-open';
    bilingual(label, [card.getAttribute('data-open-ja'), card.getAttribute('data-open-en')]);
    button.appendChild(label);
    button.appendChild(arrow());
    // Read as「マンガを読む マンガでわかる…」: the action, then the work.
    button.setAttribute('aria-labelledby', label.id + ' ' + title.id);
    button.addEventListener('click', function () { window.cxWorks.open(item, button); });
    if (item.kind !== 'manga' && window.cxWorks.warm) {
      // About to open a video: fetch the 3D phone module ahead (it builds nothing yet).
      ['pointerenter', 'focus'].forEach(function (type) { button.addEventListener(type, window.cxWorks.warm); });
    }
    link.replaceWith(button);
    card.classList.add('is-ready');
  }
  function unavailable(card, failed) {
    var status = card.querySelector('[data-cxcs-status]');
    if (status) {
      bilingual(status, failed ? MESSAGES.failed : MESSAGES.empty);
      status.setAttribute('role', 'status');
      status.hidden = false;
    }
    card.classList.add('is-unavailable');
  }
  function backdrop() {
    if (root.closest('.cxg-stage')) { root.classList.add('cxcs--on-stage'); return; }
    var poster = document.querySelector('.cxg-reel__poster');
    var src = poster && window.cxDom.safeImage(poster.currentSrc || poster.getAttribute('src'));
    var box = root.querySelector('[data-cxcs-backdrop]');
    if (!src || !box) return;
    var img = el('img', 'cxcs-backdrop__img');
    img.alt = ''; img.decoding = 'async'; img.loading = 'lazy';
    img.addEventListener('load', function () { root.classList.add('has-hero-backdrop'); });
    img.src = src;
    box.appendChild(img);
  }

  backdrop();
  root.classList.add('is-loading');
  root.setAttribute('aria-busy', 'true');
  /** A WordPress without the Creative X slots (404): the work named in the HTML, from the older lists. */
  function older(card, kind) {
    return window.cxWorks.load().then(function (data) {
      var id = card.getAttribute('data-work-id');
      var item = window.cxWorks.find(data, kind, id);
      if (item) { fill(card, item); return; }
      if (data[kind] && data[kind].length) console.warn('[Creative X solution] ' + kind + ' "' + id + '" is not in WordPress; the card shows no work.');
      unavailable(card, kind === 'manga' ? data.failed.works : data.failed.videos);
    });
  }
  Promise.all(cards.map(function (card) {
    var kind = card.getAttribute('data-kind');
    return window.cxWorks.slot('cx-creative-solution-' + kind).then(function (res) {
      if (res.state === 'ok') { fill(card, res.items[0]); return null; }
      if (res.state === 'missing') return older(card, kind);
      unavailable(card, res.state === 'error');
      return null;
    });
  })).then(function () {
    root.classList.remove('is-loading');
    root.removeAttribute('aria-busy');
    root.classList.add('is-ready');
  });
})();
