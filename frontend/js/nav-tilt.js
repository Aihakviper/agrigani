/* ═══════════════════════════════════════════════
   TILT.JS — 3D perspective tilt on .tilt-card
   ═══════════════════════════════════════════════ */
(function () {
  'use strict';
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  var MAX_TILT = 10; /* degrees */
  var LIFT_Z   = 24; /* px translateZ */

  function initTilt(card) {
    card.style.transition = 'transform 0.08s linear, box-shadow 0.2s ease';
    card.style.transformStyle = 'preserve-3d';
    card.style.willChange = 'transform';

    card.addEventListener('mousemove', function (e) {
      var rect = card.getBoundingClientRect();
      var x = (e.clientX - rect.left) / rect.width  - 0.5;
      var y = (e.clientY - rect.top)  / rect.height - 0.5;
      var rx = y * -MAX_TILT;
      var ry = x *  MAX_TILT;
      card.style.transform = [
        'perspective(900px)',
        'rotateX(' + rx + 'deg)',
        'rotateY(' + ry + 'deg)',
        'translateZ(' + LIFT_Z + 'px)'
      ].join(' ');
      card.style.boxShadow = [
        '0 ' + (24 + Math.abs(y) * 20) + 'px ' + (60 + Math.abs(y) * 30) + 'px rgba(0,0,0,0.55)',
        '0 0 0 1px rgba(59,196,106,' + (0.12 + Math.abs(x) * 0.2) + ')'
      ].join(', ');
    });

    card.addEventListener('mouseleave', function () {
      card.style.transition = 'transform 0.45s cubic-bezier(0.22,1,0.36,1), box-shadow 0.4s ease';
      card.style.transform  = 'perspective(900px) rotateX(0deg) rotateY(0deg) translateZ(0)';
      card.style.boxShadow  = '';
    });
  }

  /* Init on existing cards and observe for new ones */
  function attachAll() {
    document.querySelectorAll('.tilt-card:not([data-tilt-ready])').forEach(function (c) {
      c.setAttribute('data-tilt-ready', '1');
      initTilt(c);
    });
  }

  attachAll();

  /* MutationObserver for dynamically inserted cards */
  if (window.MutationObserver) {
    new MutationObserver(attachAll).observe(document.body, { childList: true, subtree: true });
  }
})();


/* ═══════════════════════════════════════════════
   NAV.JS — Scroll + mobile toggle
   ═══════════════════════════════════════════════ */
(function () {
  'use strict';
  var nav    = document.getElementById('main-nav');
  var toggle = document.getElementById('nav-burger');
  var links  = document.getElementById('nav-links');

  function onScroll() {
    if (!nav) return;
    nav.classList.toggle('is-scrolled', window.scrollY > 40);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  if (toggle && links) {
    toggle.addEventListener('click', function () {
      var open = links.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', String(open));
    });
    links.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () {
        links.classList.remove('is-open');
        toggle.setAttribute('aria-expanded', 'false');
      });
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && links.classList.contains('is-open')) {
        links.classList.remove('is-open');
        toggle.setAttribute('aria-expanded', 'false');
        toggle.focus();
      }
    });
  }
})();
