/* One-time reveals for Contents X pages outside Home.
   The page stays fully readable if this script or IntersectionObserver is absent. */
(function () {
  'use strict';

  var motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
  var revealSelector = [
    '.ab-section-head', '.ab-statement', '.ab-biz-grid', '.ab-global-grid',
    '.ab-related-grid', '.ab-cta-message-inner',
    '.ax-panel-copy', '.ax-purpose-card', '.ax-value-card',
    '.ax-message-copy', '.ax-portrait', '.ax-contact-inner',
    '.ot-section > h2', '.ot-section-alt h2', '.ot-lead', '.ot-values-grid',
    '.ot-paths', '.ot-closing',
    '.company-info', '.leader-card', '.partners-cards', '.partners-recruit',
    '.rc-op__intro', '.rc-op-item', '.rc-sel__head', '.rc-sel__step', '.rc-entry__inner',
    '.cxtp-head', '.cxtp-list',
    '.cxcs-head', '.cxcs-flow', '.cxcs-uses', '.cxcs-note',
    '.cxpf-head', '.cxpf-timeline', '.cxfq-head', '.cxfq-list', '.cxfq-contact',
    '.cx-col-featured-card', '.cx-col-grid', '.cx-col-toc', '.cx-col-cta',
    '.news-list', '.faq-list', '.faq-cta', '.legal-page h2',
    '.cxs-section-header', '.cxs-service-grid', '.cxs-tab-panel:not([hidden])',
    '.cxs-detail-extra',
    '.cxg-heading', '.cxg-overview-grid', '.cxg-detail-row', '.cxg-collaboration__inner',
    '.cxg-contact__inner',
    '.cxw-head', '.cxw-gallery'
  ].join(',');
  var wipeSelector = [
    '.ax-photo > img:first-child', '.ax-value-card > img',
    '.cx-col-featured-img img', '.cx-col-card img',
    '.cxs-detail-hero__visual > img',
    '.cxg-service-card__image > img', '.cxg-detail-row__visual > img',
    '.cxg-contact__inner > img'
  ].join(',');

  function start() {
    var body = document.body;
    if (!body || !body.matches('.cx-sitewide, .cxs-services') ||
        motionQuery.matches || !('IntersectionObserver' in window)) return;

    var seen = new WeakSet();
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('cx-motion-visible');
        entry.target.querySelectorAll('.cx-wipe-pending').forEach(function (image) {
          image.classList.add('cx-wipe-visible');
        });
        observer.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0 });

    function add(element, wipe) {
      if (seen.has(element) || element.closest('[hidden], .dl-modal')) return;
      var target = wipe ? element.parentElement : element;
      if (!target || !target.getClientRects().length) return;
      seen.add(element);
      /* First-screen content must never wait for scroll or a delayed observer. */
      if (target.getBoundingClientRect().top < window.innerHeight * 0.96) return;
      element.classList.add(wipe ? 'cx-wipe-pending' : 'cx-motion-pending');
      observer.observe(target);
    }

    function scan(root) {
      if (root.nodeType !== 1) return;
      if (root.matches(revealSelector)) add(root, false);
      root.querySelectorAll(revealSelector).forEach(function (element) { add(element, false); });
      if (root.matches(wipeSelector)) add(root, true);
      root.querySelectorAll(wipeSelector).forEach(function (element) { add(element, true); });
    }

    scan(body);
    /* News and column cards can arrive after WordPress data loads. */
    var mutations = new MutationObserver(function (records) {
      records.forEach(function (record) {
        if (record.type === 'attributes') scan(record.target);
        else record.addedNodes.forEach(scan);
      });
    });
    mutations.observe(body, { childList: true, attributes: true,
      attributeFilter: ['style', 'hidden'], subtree: true });

    function showAllForReducedMotion() {
      if (!motionQuery.matches) return;
      observer.disconnect();
      mutations.disconnect();
      body.querySelectorAll('.cx-motion-pending').forEach(function (node) {
        node.classList.add('cx-motion-visible');
      });
      body.querySelectorAll('.cx-wipe-pending').forEach(function (node) {
        node.classList.add('cx-wipe-visible');
      });
    }
    if (motionQuery.addEventListener) {
      motionQuery.addEventListener('change', showAllForReducedMotion, { once: true });
    } else if (motionQuery.addListener) {
      motionQuery.addListener(showAllForReducedMotion);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start, { once: true });
  } else {
    start();
  }
})();
