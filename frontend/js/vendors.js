/* ═══════════════════════════════════════════════════════════
   VENDORS.JS — Map interactions + filter + card animation
   ═══════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  /* ── CARD CASCADE ENTRY ── */
  var vendorCards = document.querySelectorAll('.vendor-card');
  if (!window.matchMedia('(prefers-reduced-motion:reduce)').matches) {
    vendorCards.forEach(function (card, i) {
      card.style.opacity   = '0';
      card.style.transform = 'translateY(28px)';
      setTimeout(function () {
        card.style.transition = 'opacity 0.5s var(--ease-smooth), transform 0.5s var(--ease-spring)';
        card.style.opacity    = '1';
        card.style.transform  = 'translateY(0)';
      }, 200 + i * 90);
    });
  }

  /* ── CLEAR FILTERS ── */
  var clearBtn = document.getElementById('clear-filters');
  if (clearBtn) {
    clearBtn.addEventListener('click', function () {
      document.querySelectorAll('.vendor-sidebar input[type="checkbox"]')
        .forEach(function (cb) { cb.checked = false; });
    });
  }

  /* ── DIRECTIONS STUB ── */
  document.querySelectorAll('.vc__foot .btn--ghost').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var name = btn.closest('.vendor-card').querySelector('.vc__name');
      alert((name ? name.textContent : 'Vendor') + ' — Directions will open in Google Maps in the full app.');
    });
  });

  /* ── MAP PIN INTERACTIONS ── */
  /* Make SVG pins interactive — highlight on hover and show tooltip */
  var pins = document.querySelectorAll('[data-vendor]');
  pins.forEach(function (pin) {
    var dot = pin.querySelector('.map-pin-dot');
    var state = pin.dataset.vendor;

    pin.style.cursor = 'none';

    pin.addEventListener('mouseenter', function () {
      if (dot) {
        dot.style.transition = 'r 0.2s, filter 0.2s';
        dot.setAttribute('r', '8');
        dot.style.filter = 'drop-shadow(0 0 12px rgba(200,120,32,1))';
      }
      if (window.setCursorState) window.setCursorState('hover');

      /* Highlight matching vendor cards */
      highlightState(state);
    });

    pin.addEventListener('mouseleave', function () {
      if (dot) {
        dot.setAttribute('r', '5');
        dot.style.filter = '';
      }
      if (window.setCursorState) window.setCursorState('');
      clearHighlight();
    });
  });

  /* Map vendor state strings to city keywords in cards */
  var STATE_MAP = {
    'kano':      'Kano',
    'abuja':     'Abuja',
    'lagos':     'Lagos',
    'ibadan':    'Ibadan',
    'onitsha':   'Onitsha',
    'jos':       'Jos',
    'maiduguri': 'Maiduguri'
  };

  function highlightState(state) {
    var keyword = STATE_MAP[state] || '';
    if (!keyword) return;
    vendorCards.forEach(function (card) {
      var loc = (card.querySelector('.vc__detail') || {}).textContent || '';
      if (loc.includes(keyword)) {
        card.style.transition = 'border-color 0.25s, box-shadow 0.25s, transform 0.25s var(--ease-spring)';
        card.style.borderColor = 'rgba(200,120,32,0.6)';
        card.style.boxShadow   = '0 0 28px rgba(200,120,32,0.18)';
        card.style.transform   = 'translateY(-4px)';
      } else {
        card.style.transition = 'opacity 0.25s';
        card.style.opacity    = '0.4';
      }
    });
  }

  function clearHighlight() {
    vendorCards.forEach(function (card) {
      card.style.borderColor = '';
      card.style.boxShadow   = '';
      card.style.transform   = '';
      card.style.opacity     = '';
    });
  }

  /* ── STAGGERED MAP PIN ENTRY ── */
  if (!window.matchMedia('(prefers-reduced-motion:reduce)').matches) {
    var pinGroups = document.querySelectorAll('[data-vendor]');
    pinGroups.forEach(function (g, i) {
      g.style.opacity = '0';
      setTimeout(function () {
        g.style.transition = 'opacity 0.6s ease';
        g.style.opacity    = '1';
      }, 400 + i * 120);
    });
  }
})();
