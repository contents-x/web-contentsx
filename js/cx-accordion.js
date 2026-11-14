/* cxAccordion — questions that open and close their answers (first used by the Creative X FAQ, 2026-11).
   Reusable on any page: load css/cx-accordion.css and this file (defer), and write

     <div data-cx-accordion>                                   ("single" as the value: one answer open at a time)
       <div data-cx-accordion-item>
         <h3><button type="button" id="q1" aria-controls="a1" aria-expanded="true" data-cx-accordion-trigger>…</button></h3>
         <div id="a1" role="region" aria-labelledby="q1" data-cx-accordion-panel><div>…answer…</div></div>
       </div>
     </div>

   The questions and answers are in the HTML: without JS every answer is shown (aria-expanded="true" in the
   markup says so). This script then closes them all (a trigger with data-cx-accordion-open stays open),
   adds .is-ready to the list and keeps aria-expanded and .is-open (on the item and the panel) in step.
   Keys: Enter / Space on a question (it is a button), ↑ ↓ Home End move between the questions.
   The panel's open / close motion and its hiding from screen readers and Tab are in css/cx-accordion.css. */
(function () {
  'use strict';
  function setup(root) {
    if (!root || root.cxAccordion) return root && root.cxAccordion;
    var single = root.getAttribute('data-cx-accordion') === 'single';
    var triggers = Array.prototype.slice.call(root.querySelectorAll('[data-cx-accordion-trigger]'));
    function panelOf(t) { return document.getElementById(t.getAttribute('aria-controls') || ''); }
    function set(t, open) {
      t.setAttribute('aria-expanded', String(open));
      var panel = panelOf(t);
      if (panel) panel.classList.toggle('is-open', open);
      var item = t.closest('[data-cx-accordion-item]');
      if (item) item.classList.toggle('is-open', open);
    }
    function toggle(t, open) {
      if (open && single) triggers.forEach(function (o) { if (o !== t) set(o, false); });
      set(t, open);
    }
    triggers.forEach(function (t, i) {
      set(t, t.hasAttribute('data-cx-accordion-open'));
      t.addEventListener('click', function () { toggle(t, t.getAttribute('aria-expanded') !== 'true'); });
      t.addEventListener('keydown', function (e) {
        var to = e.key === 'ArrowDown' ? i + 1 : e.key === 'ArrowUp' ? i - 1 : e.key === 'Home' ? 0 : e.key === 'End' ? triggers.length - 1 : null;
        if (to === null) return;
        e.preventDefault();
        triggers[(to + triggers.length) % triggers.length].focus();
      });
    });
    root.classList.add('is-ready');
    root.cxAccordion = { open: function (t) { toggle(t, true); }, close: function (t) { set(t, false); } };
    return root.cxAccordion;
  }
  Array.prototype.forEach.call(document.querySelectorAll('[data-cx-accordion]'), setup);
  window.cxAccordion = { setup: setup };
})();
