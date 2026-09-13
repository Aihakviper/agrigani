/* ═══════════════════════════════════════════════════════════
   FIELD.JS — Living crop field canvas background
   800 organic nodes in staggered rows, react to mouse proximity.
   Mouse = the diagnostic scanner sweeping across the field.
   ═══════════════════════════════════════════════════════════ */
(function () {
  'use strict';
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  var canvas = document.getElementById('field-canvas');
  if (!canvas) return;

  var ctx    = canvas.getContext('2d');
  var W = 0, H = 0;
  var mouseX = -9999, mouseY = -9999;
  var nodes  = [];
  var raf;

  var CONFIG = {
    spacing:    48,       /* px between nodes */
    mouseRadius: 180,     /* glow radius */
    baseAlpha:  0.10,     /* dim resting state */
    maxAlpha:   0.85,     /* max lit state */
    connRadius: 110,      /* connection draw radius */
    waveSpeed:  0.0006,   /* ambient wave speed */
    returnSpeed: 0.055,   /* return-to-base speed */
    scatterForce: 4       /* push strength near cursor */
  };

  /* ── Build node grid ── */
  function buildNodes() {
    nodes = [];
    var cols = Math.ceil(W / CONFIG.spacing) + 2;
    var rows = Math.ceil(H / CONFIG.spacing) + 2;
    for (var r = 0; r < rows; r++) {
      for (var c = 0; c < cols; c++) {
        var offset = (r % 2) * (CONFIG.spacing * 0.5); /* hex stagger */
        nodes.push({
          baseX: c * CONFIG.spacing + offset - CONFIG.spacing,
          baseY: r * CONFIG.spacing - CONFIG.spacing,
          x: 0, y: 0,
          phase: Math.random() * Math.PI * 2,
          size:  1.2 + Math.random() * 0.8,
          glow:  0
        });
      }
    }
    /* init positions */
    nodes.forEach(function (n) { n.x = n.baseX; n.y = n.baseY; });
  }

  /* ── Resize ── */
  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
    buildNodes();
  }

  window.addEventListener('resize', resize, { passive: true });
  resize();

  /* ── Mouse ── */
  document.addEventListener('mousemove', function (e) {
    mouseX = e.clientX; mouseY = e.clientY;
  }, { passive: true });

  document.addEventListener('mouseleave', function () {
    mouseX = -9999; mouseY = -9999;
  });

  /* ── Per-frame update ── */
  function update(t) {
    nodes.forEach(function (n) {
      /* Organic wave drift */
      var wave = Math.sin(t * CONFIG.waveSpeed + n.baseX * 0.018 + n.phase) * 2.5;
      var waveY = Math.cos(t * CONFIG.waveSpeed * 0.7 + n.baseY * 0.016 + n.phase) * 1.8;

      /* Cursor proximity */
      var dx = n.x - mouseX;
      var dy = n.y - mouseY;
      var dist = Math.hypot(dx, dy);
      var prox = Math.max(0, 1 - dist / CONFIG.mouseRadius);

      /* Glow easing */
      n.glow += (prox * CONFIG.maxAlpha - n.glow) * 0.09;

      /* Scatter push */
      if (dist < CONFIG.mouseRadius * 0.55 && dist > 0.1) {
        var force = (1 - dist / (CONFIG.mouseRadius * 0.55)) * CONFIG.scatterForce;
        n.x += (dx / dist) * force;
        n.y += (dy / dist) * force;
      }

      /* Return to base */
      var targetX = n.baseX + wave;
      var targetY = n.baseY + waveY;
      n.x += (targetX - n.x) * CONFIG.returnSpeed;
      n.y += (targetY - n.y) * CONFIG.returnSpeed;
    });
  }

  /* ── Per-frame draw ── */
  function draw() {
    ctx.clearRect(0, 0, W, H);

    /* Draw connections first (under nodes) */
    ctx.lineWidth = 0.6;
    for (var i = 0; i < nodes.length; i++) {
      var a = nodes[i];
      if (a.glow < 0.04) continue;
      for (var j = i + 1; j < nodes.length; j++) {
        var b = nodes[j];
        if (b.glow < 0.04) continue;
        var d = Math.hypot(a.x - b.x, a.y - b.y);
        if (d > CONFIG.connRadius) continue;
        var alpha = Math.min(a.glow, b.glow) * (1 - d / CONFIG.connRadius) * 0.6;
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.strokeStyle = 'rgba(59,196,106,' + alpha + ')';
        ctx.stroke();
      }
    }

    /* Draw nodes */
    nodes.forEach(function (n) {
      var g = n.glow;
      var alpha = CONFIG.baseAlpha + g * (CONFIG.maxAlpha - CONFIG.baseAlpha);
      var size  = n.size + g * 3.5;

      /* Outer glow halo */
      if (g > 0.05) {
        var grad = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, size * 5);
        grad.addColorStop(0, 'rgba(59,196,106,' + (g * 0.22) + ')');
        grad.addColorStop(1, 'rgba(59,196,106,0)');
        ctx.beginPath();
        ctx.arc(n.x, n.y, size * 5, 0, Math.PI * 2);
        ctx.fillStyle = grad;
        ctx.fill();
      }

      /* Core dot */
      ctx.beginPath();
      ctx.arc(n.x, n.y, size, 0, Math.PI * 2);
      var r = Math.round(40  + g * 19);
      var gv= Math.round(130 + g * 66);
      var bv= Math.round(80  + g * 26);
      ctx.fillStyle = 'rgba(' + r + ',' + gv + ',' + bv + ',' + alpha + ')';
      ctx.fill();
    });
  }

  /* ── Loop ── */
  function loop(t) {
    update(t);
    draw();
    raf = requestAnimationFrame(loop);
  }

  raf = requestAnimationFrame(loop);

  /* Expose for page-specific use */
  window.fieldBg = {
    flash: function (intensity) {
      /* Brief full-field light-up — used after scan completes */
      var orig = CONFIG.mouseRadius;
      CONFIG.mouseRadius = 2000;
      mouseX = W / 2; mouseY = H / 2;
      setTimeout(function () {
        CONFIG.mouseRadius = orig;
        mouseX = -9999; mouseY = -9999;
      }, 400);
    }
  };
})();
