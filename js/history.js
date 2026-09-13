/* ═══════════════════════════════════════════════════════════
   HISTORY.JS — Filter + 3D stage mouse tilt
   Special feature: entire archive grid tilts with mouse position
   ═══════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  /* ── 3D STAGE GLOBAL TILT ── */
  var stage = document.getElementById('archive-stage');
  if (stage && !window.matchMedia('(prefers-reduced-motion:reduce)').matches) {
    var currentTiltX = 0, currentTiltY = 0;

    document.addEventListener('mousemove', function (e) {
      var x = (e.clientX / window.innerWidth  - 0.5) * 5;   /* ±2.5deg */
      var y = (e.clientY / window.innerHeight - 0.5) * -3;  /* ±1.5deg */
      currentTiltX += (x - currentTiltX) * 0.06;
      currentTiltY += (y - currentTiltY) * 0.06;
    }, { passive: true });

    function applyTilt() {
      if (stage) {
        stage.style.transform =
          'perspective(1400px) rotateX(' + currentTiltY.toFixed(2) + 'deg) rotateY(' + currentTiltX.toFixed(2) + 'deg)';
      }
      requestAnimationFrame(applyTilt);
    }
    requestAnimationFrame(applyTilt);

    /* Reset on mouse leave */
    document.addEventListener('mouseleave', function () {
      currentTiltX = 0; currentTiltY = 0;
    });
  }

  /* ── CASCADE ENTRY ANIMATION ── */
  var cards = document.querySelectorAll('.archive-card');
  if (!window.matchMedia('(prefers-reduced-motion:reduce)').matches) {
    cards.forEach(function (c, i) {
      c.style.opacity = '0';
      c.style.transform = 'translateX(-20px)';
      setTimeout(function () {
        c.style.transition = 'opacity 0.45s var(--ease-smooth), transform 0.45s var(--ease-smooth)';
        c.style.opacity = '1';
        c.style.transform = 'translateX(0)';
      }, 120 + i * 80);
    });
  }

  /* ── FILTER CHIPS ── */
  var chips      = document.querySelectorAll('.chip');
  var searchInput= document.getElementById('history-search');
  var emptyState = document.getElementById('history-empty');
  var activeFilter = 'all';
  var query = '';

  function applyFilters() {
    var visible = 0;
    cards.forEach(function (card) {
      var type = (card.dataset.type || '').toLowerCase();
      var conf = parseInt(card.dataset.conf || '0', 10);
      var name = (card.querySelector('.archive-card__disease') || {}).textContent || '';

      var typeOk = activeFilter === 'all'
        || (activeFilter === 'crop'      && type === 'crop')
        || (activeFilter === 'livestock' && type === 'livestock')
        || (activeFilter === 'high'      && conf >= 90);

      var nameOk = !query || name.toLowerCase().includes(query.toLowerCase());

      if (typeOk && nameOk) {
        card.style.display = '';
        visible++;
      } else {
        card.style.display = 'none';
      }
    });

    if (emptyState) emptyState.classList.toggle('is-on', visible === 0);
  }

  chips.forEach(function (chip) {
    chip.addEventListener('click', function () {
      chips.forEach(function (c) { c.classList.remove('is-on'); });
      chip.classList.add('is-on');
      activeFilter = chip.dataset.filter || 'all';
      applyFilters();
    });
  });

  if (searchInput) {
    searchInput.addEventListener('input', function () {
      query = this.value;
      applyFilters();
    });
  }

  /* ── DELETE WITH FADE-SLIDE ── */
  document.querySelectorAll('.btn--danger').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var card = btn.closest('.archive-card');
      if (!card) return;
      if (!confirm('Delete this diagnosis record?')) return;

      card.style.transition = 'opacity 0.3s ease, transform 0.35s ease, max-height 0.4s ease, padding 0.4s ease, margin 0.4s ease';
      card.style.opacity    = '0';
      card.style.transform  = 'translateX(24px)';
      card.style.maxHeight  = card.offsetHeight + 'px';
      card.style.overflow   = 'hidden';

      setTimeout(function () {
        card.style.maxHeight = '0';
        card.style.padding   = '0';
        card.style.margin    = '0';
      }, 300);

      setTimeout(function () {
        card.remove();
        applyFilters();
      }, 700);
    });
  });
})();
