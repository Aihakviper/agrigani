/* ═══════════════════════════════════════════════════════════
   DISEASES.JS — Hex grid filter with spotlight dimming
   Non-matching cells shrink and fade; matching ones stay bright.
   ═══════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var searchInput = document.getElementById('disease-search');
  var typeTabs    = document.querySelectorAll('.type-tab');
  var cells       = document.querySelectorAll('.hex-cell');
  var emptyEl     = document.getElementById('disease-empty');

  var activeType = 'all';
  var query      = '';

  /* ── CASCADE ENTRY ── */
  if (!window.matchMedia('(prefers-reduced-motion:reduce)').matches) {
    cells.forEach(function (c, i) {
      c.style.opacity   = '0';
      c.style.transform = 'translateY(24px) scale(0.95)';
      setTimeout(function () {
        c.style.transition = 'opacity 0.5s var(--ease-smooth), transform 0.5s var(--ease-spring)';
        c.style.opacity    = '1';
        c.style.transform  = 'translateY(0) scale(1)';
      }, 80 + i * 60);
    });
  }

  /* ── FILTER ── */
  function applyFilters() {
    var visible = 0;

    cells.forEach(function (cell) {
      var type  = (cell.dataset.type || '').toLowerCase();
      var name  = (cell.querySelector('.hex-name')  || {}).textContent || '';
      var crop  = (cell.querySelector('.hex-crop')  || {}).textContent || '';
      var searchText = (name + ' ' + crop).toLowerCase();

      var typeOk = activeType === 'all' || type === activeType;
      var nameOk = !query || searchText.includes(query.toLowerCase());
      var match  = typeOk && nameOk;

      /* Spotlight: dim non-matching, scale down */
      if (match) {
        cell.style.opacity   = '1';
        cell.style.transform = '';
        cell.style.filter    = '';
        cell.style.pointerEvents = '';
        visible++;
      } else {
        cell.style.opacity   = '0.15';
        cell.style.transform = 'scale(0.92)';
        cell.style.filter    = 'grayscale(0.6)';
        cell.style.pointerEvents = 'none';
      }
      cell.style.transition = 'opacity 0.35s ease, transform 0.35s var(--ease-smooth), filter 0.35s ease';
    });

    if (emptyEl) emptyEl.classList.toggle('is-on', visible === 0);
  }

  /* ── TYPE TABS ── */
  typeTabs.forEach(function (tab) {
    tab.addEventListener('click', function () {
      typeTabs.forEach(function (t) { t.classList.remove('is-on'); });
      tab.classList.add('is-on');
      activeType = tab.dataset.type || 'all';
      applyFilters();
    });
  });

  /* ── SEARCH ── */
  if (searchInput) {
    searchInput.addEventListener('input', function () {
      query = this.value.trim();
      applyFilters();
    });
  }

  /* ── HEX HOVER CURSOR STATE ── */
  cells.forEach(function (cell) {
    cell.addEventListener('mouseenter', function () {
      if (window.setCursorState) window.setCursorState('hover');
    });
    cell.addEventListener('mouseleave', function () {
      if (window.setCursorState) window.setCursorState('');
    });
  });
})();
