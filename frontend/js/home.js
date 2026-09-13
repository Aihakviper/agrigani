/* ═══════════════════════════════════════════════
   HOME.JS — Landing page interactions
   ═══════════════════════════════════════════════ */
(function () {
  'use strict';

  /* ── Word-by-word title reveal ── */
  function revealTitle() {
    var words = document.querySelectorAll('.hero__title .word');
    words.forEach(function (w, i) {
      setTimeout(function () {
        w.classList.add('is-visible');
      }, 120 + i * 140);
    });
  }
  revealTitle();

  /* ── Animated counter ── */
  function countUp(el, target, dur) {
    var start = null;
    function step(ts) {
      if (!start) start = ts;
      var p = Math.min((ts - start) / dur, 1);
      var ease = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.floor(ease * target).toLocaleString() + '+';
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  var statEl = document.getElementById('stat-count');
  if (statEl && 'IntersectionObserver' in window) {
    var obs = new IntersectionObserver(function (entries) {
      if (entries[0].isIntersecting) { countUp(statEl, 12500, 1600); obs.disconnect(); }
    }, { threshold: 0.4 });
    obs.observe(statEl);
  }

  /* ── Scroll reveal for process cards and tiles ── */
  if ('IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion:reduce)').matches) {
    var targets = document.querySelectorAll('.process-card, .dp-tile');
    targets.forEach(function (el) {
      el.style.opacity = '0';
      el.style.transform = 'translateY(32px)';
    });

    var revObs = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        var idx = Array.from(targets).indexOf(e.target);
        setTimeout(function () {
          e.target.style.transition = 'opacity 0.55s var(--ease-smooth), transform 0.55s var(--ease-smooth)';
          e.target.style.opacity = '1';
          e.target.style.transform = 'translateY(0)';
        }, (idx % 4) * 90);
        revObs.unobserve(e.target);
      });
    }, { threshold: 0.1 });

    targets.forEach(function (el) { revObs.observe(el); });
  }

  /* ── Hero portal → diagnose ── */
  var portal = document.getElementById('hero-drop-zone');
  if (!portal) return;

  portal.addEventListener('click', function () { window.location.href = 'diagnose.html'; });
  portal.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); window.location.href = 'diagnose.html'; }
  });
  portal.addEventListener('dragover', function (e) { e.preventDefault(); portal.classList.add('is-dragover'); if (window.setCursorState) window.setCursorState('grab'); });
  portal.addEventListener('dragleave', function () { portal.classList.remove('is-dragover'); if (window.setCursorState) window.setCursorState(''); });
  portal.addEventListener('drop', function (e) {
    e.preventDefault();
    portal.classList.remove('is-dragover');
    if (e.dataTransfer.files.length) window.location.href = 'diagnose.html';
  });
})();
