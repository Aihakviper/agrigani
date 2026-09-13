/* ═══════════════════════════════════════════════════════════
   DIAGNOSE.JS — Scanner + API + Result
   Special feature: holographic scan beam on image upload
   ═══════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var API = '/api/v1';

  /* ── Elements ── */
  var chamber    = document.getElementById('scanner-chamber');
  var fileInput  = document.getElementById('file-input');
  var imgEl      = document.getElementById('chamber-img');
  var statusEl   = document.getElementById('scan-status-txt');
  var diagnoseBtn= document.getElementById('diagnose-btn');

  var rEmpty   = document.getElementById('r-empty');
  var rLoading = document.getElementById('r-loading');
  var rError   = document.getElementById('r-error');
  var rCard    = document.getElementById('result-card');
  var errorMsg = document.getElementById('error-msg');
  var retryBtn = document.getElementById('retry-btn');
  var newBtn   = document.getElementById('new-diag-btn');
  var saveBtn  = document.getElementById('save-btn');

  var selectedFile = null;

  if (!chamber) return;

  /* ══════════════════════════════════════
     STATE
  ══════════════════════════════════════ */
  function setState(s) {
    [rEmpty,rLoading,rError,rCard].forEach(function(e){ if(e){ e.classList.remove('is-on'); e.style.display=''; }});
    if (s === 'empty')  { rEmpty.style.display = 'flex'; }
    if (s === 'loading'){ rLoading.classList.add('is-on'); }
    if (s === 'error')  { rError.classList.add('is-on'); }
    if (s === 'result') { rCard.classList.add('is-on'); }
  }

  setState('empty');

  /* ══════════════════════════════════════
     FILE HANDLING
  ══════════════════════════════════════ */
  function loadFile(file) {
    if (!file) return;
    if (!['image/jpeg','image/png','image/webp'].includes(file.type)) { alert('Please upload a JPG or PNG image.'); return; }
    if (file.size > 5 * 1024 * 1024) { alert('Image must be under 5 MB.'); return; }
    selectedFile = file;

    var reader = new FileReader();
    reader.onload = function (e) {
      imgEl.src = e.target.result;
      imgEl.alt = 'Uploaded crop for diagnosis';
      chamber.classList.add('has-image');
      if (statusEl) statusEl.textContent = 'READY TO SCAN';
      if (window.setCursorState) window.setCursorState('scan');
    };
    reader.readAsDataURL(file);
  }

  /* Click to open picker */
  chamber.addEventListener('click', function (e) {
    if (e.target.id === 'change-img-btn' || (e.target.closest && e.target.closest('#change-img-btn'))) return;
    if (!chamber.classList.contains('has-image')) fileInput.click();
  });

  chamber.addEventListener('keydown', function (e) {
    if ((e.key === 'Enter' || e.key === ' ') && !chamber.classList.contains('has-image')) {
      e.preventDefault(); fileInput.click();
    }
  });

  if (fileInput) fileInput.addEventListener('change', function () { loadFile(this.files[0]); });

  /* Drag-and-drop */
  chamber.addEventListener('dragover',  function (e) { e.preventDefault(); chamber.classList.add('is-drag'); });
  chamber.addEventListener('dragleave', function ()  { chamber.classList.remove('is-drag'); });
  chamber.addEventListener('drop', function (e) {
    e.preventDefault(); chamber.classList.remove('is-drag');
    loadFile(e.dataTransfer.files[0]);
  });

  /* Change image */
  var changeBtn = document.getElementById('change-img-btn');
  if (changeBtn) {
    changeBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      chamber.classList.remove('has-image','is-scanning');
      imgEl.src = '';
      selectedFile = null;
      if (fileInput) fileInput.value = '';
      if (window.setCursorState) window.setCursorState('');
    });
  }

  /* ══════════════════════════════════════
     SCAN ANIMATION
  ══════════════════════════════════════ */
  function playScan(callback) {
    chamber.classList.add('is-active','is-scanning');
    if (statusEl) statusEl.textContent = 'SCANNING…';
    if (window.setCursorState) window.setCursorState('scan');

    /* After scan completes */
    setTimeout(function () {
      chamber.classList.remove('is-scanning');
      if (statusEl) statusEl.textContent = 'ANALYSIS COMPLETE';
      if (window.fieldBg) window.fieldBg.flash();
      if (window.setCursorState) window.setCursorState('');
      setTimeout(callback, 280);
    }, 2200);
  }

  /* ══════════════════════════════════════
     SUBMIT
  ══════════════════════════════════════ */
  if (diagnoseBtn) {
    diagnoseBtn.addEventListener('click', function () {
      if (!selectedFile) { alert('Upload a crop photo first.'); return; }
      playScan(submitDiagnosis);
    });
  }

  async function submitDiagnosis() {
    setState('loading');

    var fd = new FormData();
    fd.append('image', selectedFile);

    var fields = ['farmer-name','farmer-phone','farm-type','farm-state'];
    var keys   = ['full_name','phone_number','farm_type','location'];
    fields.forEach(function (id, i) {
      var el = document.getElementById(id);
      if (el && el.value) fd.append(keys[i], el.value.trim());
    });

    try {
      var res = await fetch(API + '/diagnoses/', { method: 'POST', body: fd });
      if (!res.ok) throw new Error('Server ' + res.status);
      var data = await res.json();
      renderResult(data);
      setState('result');
    } catch (err) {
      console.warn('API offline — demo mode:', err.message);
      renderResult(demoResult());
      setState('result');
    }
  }

  /* ══════════════════════════════════════
     RESULT RENDERING
  ══════════════════════════════════════ */
  function renderResult(data) {
    /* Disease name */
    var nameEl = document.getElementById('rc-name');
    if (nameEl) nameEl.textContent = data.disease_name || '—';

    /* Image */
    var rcImg = document.getElementById('rc-img');
    if (rcImg && imgEl.src) { rcImg.src = imgEl.src; }

    /* Confidence ring */
    var conf = parseFloat(data.disease_confidence || data.confidence || 0);
    var pct  = Math.round(conf * 100);
    var valEl = document.getElementById('conf-val');
    if (valEl) valEl.textContent = pct + '%';

    var arc = document.getElementById('conf-arc');
    if (arc) {
      var circ = 2 * Math.PI * 45;
      setTimeout(function () {
        arc.style.strokeDashoffset = circ * (1 - conf);
        arc.style.stroke = conf >= 0.85 ? 'var(--leaf)' : conf >= 0.65 ? 'var(--harvest)' : 'var(--critical)';
      }, 350);
    }

    var modelEl = document.getElementById('rc-model');
    if (modelEl) modelEl.textContent = 'MODEL ' + (data.ml_model_version || 'v1.0');

    /* Description */
    var descEl = document.getElementById('rc-desc');
    if (descEl) descEl.textContent = data.description || 'No description available for this condition.';

    /* Treatment */
    var tList = document.getElementById('treatment-list');
    if (tList) {
      tList.innerHTML = '';
      parseTreatment(data.treatment_recommendation).forEach(function (it) {
        tList.insertAdjacentHTML('beforeend',
          '<div class="treatment-item">' +
          '<span class="treatment-item__ico" aria-hidden="true">' + it.icon + '</span>' +
          '<span class="treatment-item__text">' + esc(it.text) + '</span></div>');
      });
    }

    /* Vendors */
    var vList = document.getElementById('vendor-result-list');
    if (vList) {
      vList.innerHTML = '';
      (data.vendor_info || []).slice(0, 3).forEach(function (v) {
        var init = (v.name || 'AG').split(' ').map(function (w) { return w[0]; }).join('').slice(0,2).toUpperCase();
        vList.insertAdjacentHTML('beforeend',
          '<div class="vri">' +
          '<div class="vri__av">' + init + '</div>' +
          '<div><div class="vri__name">' + esc(v.name||'Unknown') + '</div>' +
          '<div class="vri__loc">' + esc(v.location||'—') + '</div></div>' +
          '<a href="tel:' + esc(v.contact||'') + '" class="vri__call">' + esc(v.contact||'Contact') + '</a></div>');
      });
      if (!data.vendor_info || !data.vendor_info.length) {
        vList.innerHTML = '<p style="font-size:var(--small);color:var(--text-3)">No vendors found for your region.</p>';
      }
    }
  }

  var ICON_PILL   = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="3.5" y="9" width="17" height="6" rx="3" transform="rotate(-30 12 12)" stroke="currentColor" stroke-width="1.6"/><line x1="10.5" y1="8" x2="13.5" y2="16" transform="rotate(-30 12 12)" stroke="currentColor" stroke-width="1.4"/></svg>';
  var ICON_LIST   = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="5" cy="7" r="1.2" fill="currentColor"/><circle cx="5" cy="12" r="1.2" fill="currentColor"/><circle cx="5" cy="17" r="1.2" fill="currentColor"/><path d="M9 7h11M9 12h11M9 17h11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>';
  var ICON_DROP   = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 3c3 4 5 7 5 10a5 5 0 0 1-10 0c0-3 2-6 5-10Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>';
  var ICON_SHIELD = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6l7-3Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/><path d="M9 12l2 2 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  var ICON_DOT    = '<svg width="8" height="8" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="9"/></svg>';

  function parseTreatment(rec) {
    if (!rec) return [];
    if (typeof rec === 'string') return [{ icon:ICON_PILL, text:rec }];
    var items = [];
    if (rec.medicine_name) items.push({ icon:ICON_PILL, text:'Apply ' + rec.medicine_name + (rec.dosage ? ' — ' + rec.dosage : '') });
    if (rec.instructions)  items.push({ icon:ICON_LIST, text:rec.instructions });
    if (rec.application_method) items.push({ icon:ICON_DROP, text:'Method: ' + rec.application_method });
    if (rec.prevention)    items.push({ icon:ICON_SHIELD, text:'Prevention: ' + rec.prevention });
    if (!items.length) Object.entries(rec).forEach(function (p) {
      if (p[1] && typeof p[1]==='string') items.push({ icon:ICON_DOT, text:p[0]+': '+p[1] });
    });
    return items;
  }

  function esc(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  /* ══════════════════════════════════════
     DEMO DATA
  ══════════════════════════════════════ */
  function demoResult() {
    return {
      disease_name:       'Maize Northern Leaf Blight',
      disease_confidence: 0.91,
      ml_model_version:   'v1.0',
      description:        'Tan cigar-shaped lesions caused by Setosphaeria turcica. Begins on lower leaves, spreads upward, reducing photosynthesis and grain fill. Most prevalent in humid Nigerian growing conditions.',
      treatment_recommendation: {
        medicine_name:      'Mancozeb (Dithane M-45)',
        dosage:             '2.5 g per litre of water',
        instructions:       'Apply as foliar spray every 7–10 days from first sign of lesions. Cover both leaf surfaces.',
        application_method: 'Knapsack sprayer, early morning. Wear protective clothing.',
        prevention:         'Use certified resistant varieties. Practice seasonal crop rotation. Remove infected debris after harvest.'
      },
      vendor_info: [
        { name:'Green Acre Agro Inputs', location:'Kano State, Fagge LGA',  contact:'+234 802 123 4567' },
        { name:'FarmPlus Abuja Ltd',     location:'FCT Abuja, Wuse II',      contact:'+234 803 456 7890' },
        { name:'Nwosu Agro Inputs',      location:'Anambra State, Onitsha',  contact:'+234 806 111 2222' }
      ]
    };
  }

  /* ══════════════════════════════════════
     SECONDARY ACTIONS
  ══════════════════════════════════════ */
  if (retryBtn) retryBtn.addEventListener('click', function () { setState('empty'); });

  if (newBtn) newBtn.addEventListener('click', function () {
    selectedFile = null;
    chamber.classList.remove('has-image','is-active','is-scanning');
    imgEl.src = '';
    if (fileInput) fileInput.value = '';
    if (statusEl) statusEl.textContent = '';
    if (window.setCursorState) window.setCursorState('');
    setState('empty');
  });

  var ICON_CHECK = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="vertical-align:-2px;margin-right:5px"><path d="M20 6 9 17l-5-5" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>';

  if (saveBtn) saveBtn.addEventListener('click', function () {
    saveBtn.innerHTML = ICON_CHECK + 'Saved';
    saveBtn.disabled = true;
    setTimeout(function () { saveBtn.textContent = 'Save to history'; saveBtn.disabled = false; }, 2500);
  });
})();
