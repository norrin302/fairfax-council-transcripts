/* ============================================================
   Review-mode speaker labeling — v2.2
   reviewer cockpit for staged decisions + export

   Enable: add ?review=1 to the transcript page URL.
   Passphrase gate: reviewer confirms once per session (stored in sessionStorage).
   Staging: localStorage key per meeting_id (merged on export).
   Safe architecture: decisions never written directly to public output.

   v2.1 hardening:
   - Audit metadata in all exported decisions
   - Full evidence preserved (not truncated)
   - Guardrails on suppress/keep_unknown actions
   - Unexported-state dirty indicator
   - beforeunload warning for open tabs

   v2.2 provenance polish:
   - decision_id: stable unique ID per staged decision
   - export_batch_id: per-export-session grouping ID
   - exported_at: ISO timestamp set at export time
   - Apply-time provenance written to structured JSON metadata
   ============================================================ */

(function () {
  'use strict';

  // ---- Config ----
  var REVIEW_SESSION_KEY = 'review_session';
  var REVIEW_SESSION_VALUE = 'confirmed';
  var PENDING_KEY = function (meetingId) {
    return 'reviewdecisions:pending:' + String(meetingId || '').trim();
  };
  var EXPORT_FLAG_KEY = function (meetingId) {
    return 'reviewdecisions:exported:' + String(meetingId || '').trim();
  };
  var UI_VERSION = '2.2';
  var REVIEWER_DEFAULT = 'manual-review';

  var COUNCIL_QUICK_PICK = [
    'Mayor Catherine Read',
    'Councilmember Anthony Amos',
    'Councilmember Billy Bates',
    'Councilmember Stacy Hall',
    'Councilmember Stacy Hardy-Chandler',
    'Councilmember Rachel McQuillen',
    'Councilmember Tom Peterson',
  ];

  var STAFF_QUICK_PICK = [
    'JC Martinez',
    'Mr. Alexander',
    'William Pitchford',
  ];

  // ---- State ----
  var REVIEW_MODE = false;
  var SESSION_CONFIRMED = false;
  var PENDING_DECISIONS = [];
  var EXPORTED_SET = {};         // turn_ids that have been exported this session
  var MEETING_ID = '';
  var ACTIVE_TURN_ID = null;
  var DIRTY_STATE = false;       // true when staged decisions exist and haven't been exported
  var CURRENT_EXPORT_BATCH_ID = null;  // set once per export event; used to tag all decisions in that export

  // ---- Helpers ----
  function getTurns() {
    return (typeof TRANSCRIPT_TURNS !== 'undefined') ? TRANSCRIPT_TURNS : [];
  }

  function speakerKey(s) {
    return String(s || '').toLowerCase().replace(/\s+/g, ' ').trim();
  }

  function formatTime(seconds) {
    var s = Math.max(0, Math.floor(Number(seconds) || 0));
    var m = Math.floor((s % 3600) / 60);
    var sec = s % 60;
    return String(m).padStart(2, '0') + ':' + String(sec).padStart(2, '0');
  }

  // ---- ID generation (stable, no crypto required) ----
  function generateId() {
    // Date.now().toString(36) gives a compact time-sortable prefix.
    // + random suffix makes it unique enough for audit use.
    return Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 8);
  }

  function formatISOTime(timestamp) {
    try { return new Date(Number(timestamp) || Date.now()).toISOString(); }
    catch (e) { return new Date().toISOString(); }
  }

  function showToast(msg) {
    var existing = document.querySelector('.toast');
    if (existing) existing.remove();
    var t = document.createElement('div');
    t.className = 'toast';
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(function () { t.classList.add('show'); }, 10);
    setTimeout(function () {
      t.classList.remove('show');
      setTimeout(function () { t.remove(); }, 300);
    }, 2200);
  }

  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text);
    }
    var ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    ta.remove();
    return Promise.resolve();
  }

  function getMeetingMeta() {
    var m = (typeof MEETING !== 'undefined' && MEETING) ? MEETING : {};
    return {
      id: String(m.meeting_id || '').trim(),
      date: String(m.display_date || m.meeting_date || '').trim(),
      title: String(m.title || '').trim(),
    };
  }

  // ---- Dirty state management ----
  function markDirty() {
    DIRTY_STATE = true;
    updateDirtyIndicator();
  }

  function clearDirty() {
    DIRTY_STATE = false;
    EXPORTED_SET = {};
    try { localStorage.removeItem(EXPORT_FLAG_KEY(MEETING_ID)); } catch (e) {}
    updateDirtyIndicator();
  }

  function markExported(turnIds) {
    for (var i = 0; i < turnIds.length; i++) EXPORTED_SET[String(turnIds[i])] = true;
    try {
      localStorage.setItem(EXPORT_FLAG_KEY(MEETING_ID), JSON.stringify(EXPORTED_SET));
    } catch (e) {}
    DIRTY_STATE = false;
    updateDirtyIndicator();
  }

  function loadExportedSet() {
    try {
      var raw = localStorage.getItem(EXPORT_FLAG_KEY(MEETING_ID));
      if (raw) EXPORTED_SET = JSON.parse(raw) || {};
    } catch (e) { EXPORTED_SET = {}; }
  }

  function updateDirtyIndicator() {
    var dirtyEl = document.getElementById('review-dirty-indicator');
    if (!dirtyEl) return;
    if (DIRTY_STATE) {
      dirtyEl.style.display = 'inline-flex';
    } else {
      dirtyEl.style.display = 'none';
    }
  }

  // ---- beforeunload ----
  function handleBeforeUnload(e) {
    if (!DIRTY_STATE) return;
    var msg = 'You have unexported staged decisions. Leaving this page will lose them.';
    e.preventDefault();
    e.returnValue = msg;
    return msg;
  }

  // ---- Passphrase gate ----
  function isReviewMode() {
    var params = new URLSearchParams(window.location.search);
    return params.get('review') === '1';
  }

  function isSessionConfirmed() {
    try {
      return sessionStorage.getItem(REVIEW_SESSION_KEY) === REVIEW_SESSION_VALUE;
    } catch (e) { return false; }
  }

  function confirmSession() {
    try { sessionStorage.setItem(REVIEW_SESSION_KEY, REVIEW_SESSION_VALUE); } catch (e) {}
    SESSION_CONFIRMED = true;
  }

  function showPassphraseGate(callback) {
    var overlay = document.createElement('div');
    overlay.id = 'review-passphrase-overlay';
    overlay.innerHTML =
      '<div class="review-passphrase-box">' +
        '<h3><i class="fas fa-lock"></i> Review Mode</h3>' +
        '<p>Enter the reviewer passphrase to continue.</p>' +
        '<p class="rm-hint-text">Passphrase: <code>review</code></p>' +
        '<input type="password" id="rm-passphrase-input" class="rm-input" placeholder="Enter passphrase" autocomplete="off">' +
        '<div class="rm-actions" style="margin-top:14px;">' +
          '<button type="button" id="rm-passphrase-submit" class="mini-btn primary-btn">Confirm</button>' +
        '</div>' +
        '<p id="rm-passphrase-error" style="color:#e53e3e;font-size:13px;display:none;margin-top:8px;">Incorrect passphrase. Please try again.</p>' +
      '</div>';
    overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.55);z-index:3000;display:flex;align-items:center;justify-content:center;padding:20px;';
    document.body.appendChild(overlay);

    var input = document.getElementById('rm-passphrase-input');
    var submitBtn = document.getElementById('rm-passphrase-submit');
    var errorEl = document.getElementById('rm-passphrase-error');

    function attempt() {
      var val = input.value.trim();
      if (val === 'review') {
        overlay.remove();
        confirmSession();
        callback();
      } else {
        errorEl.style.display = 'block';
        input.value = '';
        input.focus();
      }
    }

    submitBtn.addEventListener('click', attempt);
    input.addEventListener('keydown', function (e) { if (e.key === 'Enter') attempt(); });
    input.focus();
  }

  // ---- Pending decisions storage ----
  function loadPending() {
    try {
      return JSON.parse(localStorage.getItem(PENDING_KEY(MEETING_ID)) || '[]');
    } catch (e) { return []; }
  }

  function savePending(decisions) {
    try {
      localStorage.setItem(PENDING_KEY(MEETING_ID), JSON.stringify(decisions || []));
    } catch (e) {}
    PENDING_DECISIONS = decisions || [];
  }

  function addPending(decision) {
    var all = loadPending();
    var idx = -1;
    for (var i = 0; i < all.length; i++) {
      if (all[i].turn_id === decision.turn_id) { idx = i; break; }
    }
    if (idx >= 0) all[idx] = decision;
    else all.push(decision);
    savePending(all);
    PENDING_DECISIONS = all;
    markDirty();
  }

  function removePending(turnId) {
    var all = loadPending();
    all = all.filter(function (d) { return d.turn_id !== turnId; });
    savePending(all);
    markDirty();
  }

  function clearAllPending() {
    savePending([]);
    clearDirty();
  }

  // ---- Build audit-enriched decision for export ----
  function buildExportDecision(decision) {
    return {
      meeting_id: MEETING_ID,
      decision_id: decision.decision_id || generateId(),
      turn_id: decision.turn_id,
      timestamp: decision.timestamp || Date.now(),
      reviewed_at: formatISOTime(decision.timestamp || Date.now()),
      reviewer: decision.reviewer || REVIEWER_DEFAULT,
      reviewer_action: decision.reviewer_action || 'keep_unknown',
      speaker_name: decision.speaker_name || '',
      speaker_type: decision.speaker_type || 'unknown',
      evidence_note: decision.evidence_note || decision.notes || '',
      speaker_public_override: decision.speaker_public_override || '',
      speaker_status_override: decision.speaker_status_override || '',
      text_override: '',
      suppress: decision.suppress || false,
      ui_version: UI_VERSION,
      exported_at: formatISOTime(Date.now()),
      export_batch_id: CURRENT_EXPORT_BATCH_ID || '',
    };
  }

  // ---- Build block index ----
  function buildBlockIndex() {
    var turns = getTurns();
    var blocks = [];
    for (var i = 0; i < turns.length; i++) {
      var turn = turns[i];
      var speaker = String(turn.speaker || 'Unknown').trim();
      if (!speaker || speaker.toLowerCase() === 'speaker' || speaker.toLowerCase() === 'unknown') {
        speaker = 'Unknown Speaker';
      }
      var speakerSource = String(turn.speaker_source || '').trim() || (speaker === 'Unknown Speaker' ? 'unknown' : '');
      var start = Number(turn.start) || 0;
      var end = Number(turn.end) || start;
      var text = String(turn.text || '').replace(/\s+/g, ' ').trim();
      if (!text) continue;

      var last = blocks.length ? blocks[blocks.length - 1] : null;
      var canMerge = speaker !== 'Unknown Speaker';
      if (canMerge && last && String(last.speaker) === speaker && String(last.speakerSource || '') === String(speakerSource || '')) {
        last.end = Math.max(Number(last.end) || 0, end);
        last.turnIds.push(turn.turn_id);
        last.texts.push(text);
        last.endTime = Math.max(last.endTime || 0, end);
      } else {
        blocks.push({
          speaker: speaker,
          speakerKey: speakerKey(speaker),
          speakerSource: speakerSource,
          start: start,
          end: end,
          endTime: end,
          turnIds: [turn.turn_id],
          texts: [text],
          turn_id: turn.turn_id,
        });
      }
    }
    return blocks;
  }

  // ---- Wire Label buttons into unlabeled blocks ----
  function wireLabelButtons() {
    var blocks = buildBlockIndex();
    document.querySelectorAll('.speaker-block').forEach(function (block) {
      var speakerKey2 = String(block.dataset.speaker || '').toLowerCase();
      if (speakerKey2 !== speakerKey('Unknown Speaker')) return;
      var blockIndex = parseInt(block.dataset.index || '0', 10);
      var blockInfo = blocks[blockIndex];
      if (!blockInfo) return;
      if (block.querySelector('.label-btn')) return;

      var staged = PENDING_DECISIONS.find(function (d) {
        return blockInfo.turnIds.indexOf(d.turn_id) >= 0;
      });

      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = staged ? 'label-btn label-btn-staged' : 'label-btn';
      btn.title = staged ? 'Edit staged label (review mode)' : 'Label this speaker (review mode)';
      btn.innerHTML = staged
        ? '<i class="fas fa-edit"></i> Edit label'
        : '<i class="fas fa-tag"></i> Label speaker';
      btn.addEventListener('click', function (e) {
        e.stopPropagation();
        openModalForTurn(blockInfo.turnIds[0]);
      });
      block.querySelector('.turn-header').appendChild(btn);
    });
  }

  // ---- Review banner ----
  function showReviewBanner() {
    var existing = document.getElementById('review-banner');
    if (existing) existing.remove();
    var meta = getMeetingMeta();
    var pending = PENDING_DECISIONS;
    var banner = document.createElement('div');
    banner.id = 'review-banner';
    banner.className = 'review-banner';
    banner.innerHTML =
      '<span class="review-banner-icon"><i class="fas fa-edit"></i></span>' +
      '<span class="review-banner-text">' +
        '<strong>Review mode</strong> — ' + meta.id +
      '</span>' +
      '<span class="review-staged-count" id="review-staged-count">' +
        (pending.length > 0 ? pending.length + ' staged decision' + (pending.length !== 1 ? 's' : '') : 'no staged decisions') +
      '</span>' +
      '<span class="review-dirty-indicator" id="review-dirty-indicator" style="display:none;">' +
        '<i class="fas fa-exclamation-circle"></i> unexported' +
      '</span>' +
      '<button type="button" id="review-export-btn" class="review-action-btn"' + (pending.length === 0 ? ' disabled' : '') + '>' +
        '<i class="fas fa-download"></i> Export JSON' +
      '</button>' +
      '<button type="button" id="review-copy-btn" class="review-action-btn"' + (pending.length === 0 ? ' disabled' : '') + '>' +
        '<i class="fas fa-copy"></i> Copy JSON' +
      '</button>' +
      '<button type="button" id="review-clear-btn" class="review-action-btn review-action-btn-danger"' + (pending.length === 0 ? ' disabled' : '') + '>' +
        '<i class="fas fa-trash-alt"></i> Clear all' +
      '</button>' +
      '<a href="?" class="review-exit-link">Exit review mode</a>';
    document.querySelector('.container').prepend(banner);

    document.getElementById('review-export-btn').addEventListener('click', function () {
      exportDownload();
    });

    document.getElementById('review-copy-btn').addEventListener('click', function () {
      copyExportJSON();
    });

    document.getElementById('review-clear-btn').addEventListener('click', function () {
      if (pending.length === 0) return;
      if (window.confirm('Clear all ' + pending.length + ' staged decision' + (pending.length !== 1 ? 's' : '') + '? This cannot be undone.')) {
        clearAllPending();
        renderSidebar();
        updateBannerCounts();
        wireLabelButtons();
        showToast('All staged decisions cleared');
      }
    });

    updateDirtyIndicator();
  }

  function updateBannerCounts() {
    var countEl = document.getElementById('review-staged-count');
    var exportBtn = document.getElementById('review-export-btn');
    var copyBtn = document.getElementById('review-copy-btn');
    var clearBtn = document.getElementById('review-clear-btn');
    var pending = PENDING_DECISIONS;
    if (countEl) {
      countEl.textContent = pending.length > 0
        ? pending.length + ' staged decision' + (pending.length !== 1 ? 's' : '')
        : 'no staged decisions';
    }
    if (exportBtn) exportBtn.disabled = pending.length === 0;
    if (copyBtn) copyBtn.disabled = pending.length === 0;
    if (clearBtn) clearBtn.disabled = pending.length === 0;
    updateDirtyIndicator();
  }

  // ---- Export ----
  function getExportPayload() {
    // Build full audit-enriched decisions for export.
    // A new export_batch_id is generated once per export event so all
    // decisions in this export share the same batch ID — making it easy to
    // distinguish separate export sessions from repeated exports of the same decisions.
    CURRENT_EXPORT_BATCH_ID = generateId();
    var decisions = loadPending();
    var exportDecisions = [];
    for (var i = 0; i < decisions.length; i++) {
      exportDecisions.push(buildExportDecision(decisions[i]));
    }
    return exportDecisions;
  }

  function exportDownload() {
    var payload = getExportPayload();
    if (payload.length === 0) return;
    var blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = MEETING_ID + '-staged-decisions.json';
    document.body.appendChild(a);
    a.click();
    setTimeout(function () { document.body.removeChild(a); URL.revokeObjectURL(url); }, 100);

    var turnIds = payload.map(function (d) { return d.turn_id; });
    markExported(turnIds);
    showToast('Downloaded ' + payload.length + ' decision' + (payload.length !== 1 ? 's' : '') + ' as JSON');
  }

  function copyExportJSON() {
    var payload = getExportPayload();
    if (payload.length === 0) return;
    copyText(JSON.stringify(payload, null, 2)).then(function () {
      var turnIds = payload.map(function (d) { return d.turn_id; });
      markExported(turnIds);
      showToast('JSON copied to clipboard');
    }).catch(function () { showToast('Copy failed'); });
  }

  // ---- Sidebar ----
  function getSidebar() {
    var existing = document.getElementById('review-sidebar');
    if (existing) return existing;
    var sidebar = document.createElement('div');
    sidebar.id = 'review-sidebar';
    sidebar.className = 'review-sidebar';
    document.querySelector('.container').appendChild(sidebar);
    return sidebar;
  }

  function renderSidebar() {
    var sidebar = getSidebar();
    var pending = PENDING_DECISIONS;

    if (pending.length === 0) {
      sidebar.innerHTML =
        '<div class="review-sidebar-header">' +
          '<h3><i class="fas fa-list"></i> Staged Decisions</h3>' +
        '</div>' +
        '<div class="review-sidebar-empty">No staged decisions yet.<br>Click "Label speaker" on an unlabeled block to begin.</div>';
      return;
    }

    var html = '<div class="review-sidebar-header">' +
      '<h3><i class="fas fa-list"></i> Staged Decisions <span class="review-sidebar-count">' + pending.length + '</span></h3>' +
    '</div>';

    for (var i = 0; i < pending.length; i++) {
      var d = pending[i];
      var actionLabel = actionToLabel(d.reviewer_action || 'keep_unknown');
      var typeBadge = typeToBadge(d.speaker_type || 'unknown');
      var wasExported = EXPORTED_SET[String(d.turn_id)] ? true : false;
      var exportIcon = wasExported
        ? '<span class="review-exported-icon" title="Exported"><i class="fas fa-check-circle"></i></span>'
        : '<span class="review-pending-icon" title="Not yet exported"><i class="fas fa-clock"></i></span>';

      // Truncate display in sidebar; full text preserved in stored/exported decision
      var noteTrunc = String(d.evidence_note || d.notes || '').slice(0, 60) +
        (String(d.evidence_note || d.notes || '').length > 60 ? '…' : '');

      html +=
        '<div class="review-staged-item" data-turn-id="' + d.turn_id + '">' +
          '<div class="review-staged-header">' +
            '<span class="review-staged-turn">' + escHtml(String(d.turn_id || '')) + '</span>' +
            '<span class="review-staged-time">' + (d.timestamp ? formatTime(d.timestamp / 1000) : '') + '</span>' +
          '</div>' +
          '<div class="review-staged-speaker">' + escHtml(String(d.speaker_name || '(unnamed)')) + ' ' + exportIcon + '</div>' +
          '<div class="review-staged-meta">' +
            '<span class="review-staged-action">' + actionLabel + '</span>' +
            typeBadge +
          '</div>' +
          '<div class="review-staged-decision-id">ID: ' + escHtml(String(d.decision_id || '—')) + '</div>' +
          (noteTrunc ? '<div class="review-staged-notes" title="' + escHtml(String(d.evidence_note || d.notes || '')) + '">' + escHtml(noteTrunc) + '</div>' : '') +
          '<div class="review-staged-actions">' +
            '<button type="button" class="review-item-edit-btn" data-turn-id="' + escHtml(String(d.turn_id || '')) + '"><i class="fas fa-edit"></i> Edit</button>' +
            '<button type="button" class="review-item-remove-btn" data-turn-id="' + escHtml(String(d.turn_id || '')) + '"><i class="fas fa-trash-alt"></i> Remove</button>' +
          '</div>' +
        '</div>';
    }

    sidebar.innerHTML = html;

    sidebar.querySelectorAll('.review-item-edit-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var turnId = btn.getAttribute('data-turn-id');
        openModalForTurn(turnId);
      });
    });
    sidebar.querySelectorAll('.review-item-remove-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var turnId = btn.getAttribute('data-turn-id');
        removePending(turnId);
        renderSidebar();
        updateBannerCounts();
        wireLabelButtons();
        showToast('Staged decision removed');
      });
    });
  }

  function escHtml(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function actionToLabel(action) {
    var map = {
      'keep_unknown': 'Keep unknown',
      'mark_public_comment': 'Public comment',
      'approve_named_official': 'Named official',
      'suppress_turn': 'Suppress',
    };
    return map[action] || action || 'unknown';
  }

  function typeToBadge(type) {
    var map = {
      'council': '<span class="review-badge review-badge-council">Council</span>',
      'staff': '<span class="review-badge review-badge-staff">Staff</span>',
      'public_comment': '<span class="review-badge review-badge-public">Public</span>',
      'unknown': '<span class="review-badge review-badge-unknown">Unknown</span>',
    };
    return map[type] || '<span class="review-badge review-badge-unknown">Unknown</span>';
  }

  // ---- Modal ----
  var modalEl = null;

  function getModal() {
    if (modalEl) return modalEl;
    modalEl = document.createElement('div');
    modalEl.id = 'review-modal';
    modalEl.className = 'review-modal';
    modalEl.style.display = 'none';
    document.body.appendChild(modalEl);
    return modalEl;
  }

  function openModalForTurn(turnId) {
    var blocks = buildBlockIndex();
    var blockInfo = null;
    for (var i = 0; i < blocks.length; i++) {
      if (blocks[i].turnIds.indexOf(String(turnId)) >= 0) {
        blockInfo = blocks[i];
        break;
      }
    }
    if (!blockInfo) return;

    ACTIVE_TURN_ID = String(turnId);
    var modal = getModal();
    var existing = PENDING_DECISIONS.find(function (d) { return d.turn_id === ACTIVE_TURN_ID; });

    modal.innerHTML = getModalHtml(blockInfo, existing);

    // Wire reviewer field
    var reviewerInput = modal.querySelector('#rm-reviewer');
    if (reviewerInput) {
      reviewerInput.value = existing && existing.reviewer ? existing.reviewer : REVIEWER_DEFAULT;
    }

    // Wire quick-picks
    modal.querySelectorAll('.quick-pick-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var name = btn.textContent.trim();
        var input = modal.querySelector('#rm-speaker-name');
        if (input) input.value = name;
        var typeCouncil = modal.querySelector('#rm-type-council');
        var typeStaff = modal.querySelector('#rm-type-staff');
        if (typeCouncil) typeCouncil.checked = true;
        if (typeStaff) typeStaff.checked = true;
        updateSubmitState(modal);
      });
    });

    var quickKeepUnknown = modal.querySelector('#rm-quick-keep-unknown');
    var quickPublic = modal.querySelector('#rm-quick-public');
    var quickSuppress = modal.querySelector('#rm-quick-suppress');
    var submitBtn = modal.querySelector('#rm-submit');
    var evidenceNote = modal.querySelector('#rm-evidence');

    // Quick Keep unknown — set note if empty, then save
    if (quickKeepUnknown) {
      quickKeepUnknown.addEventListener('click', function () {
        var typeUnknown = modal.querySelector('#rm-type-unknown');
        if (typeUnknown) typeUnknown.checked = true;
        var note = evidenceNote.value.trim();
        if (!note) {
          note = 'Reviewer action: keep unknown';
          evidenceNote.value = note;
        }
        var decision = buildDecisionFromModal(modal);
        decision.reviewer_action = 'keep_unknown';
        decision.speaker_type = 'unknown';
        saveDecision(decision);
      });
    }

    // Quick Public comment
    if (quickPublic) {
      quickPublic.addEventListener('click', function () {
        var typePublic = modal.querySelector('#rm-type-public');
        if (typePublic) typePublic.checked = true;
        updateSubmitState(modal);
      });
    }

    // Quick Suppress — requires note or confirm
    if (quickSuppress) {
      quickSuppress.addEventListener('click', function () {
        var note = (evidenceNote.value || '').trim();
        if (!note) {
          var confirmed = window.confirm(
            'Suppress this turn? No evidence note was provided.\n\nClick OK to suppress with a default note, or Cancel to go back and add a note.'
          );
          if (!confirmed) return;
          note = 'Suppress turn — reviewer action (no explicit evidence provided)';
          evidenceNote.value = note;
        }
        var decision = buildDecisionFromModal(modal);
        decision.reviewer_action = 'suppress_turn';
        decision.suppress = true;
        decision.evidence_note = note;
        saveDecision(decision);
      });
    }

    submitBtn.addEventListener('click', function () {
      var decision = buildDecisionFromModal(modal);
      if (!decision) return;
      // Guardrail: suppress and keep_unknown require note or confirm
      if ((decision.reviewer_action === 'suppress_turn' || decision.reviewer_action === 'keep_unknown') && !decision.evidence_note) {
        var confirmed = window.confirm(
          'No evidence note was provided for "' + decision.reviewer_action + '".\n\n' +
          'This makes audit difficult. Click OK to save without a note, or Cancel to add one.'
        );
        if (!confirmed) return;
      }
      saveDecision(decision);
    });

    modal.querySelector('#rm-cancel').addEventListener('click', closeModal);
    modal.addEventListener('click', function (e) {
      if (e.target === modal) closeModal();
    });

    updateSubmitState(modal);
    modal.classList.add('open');
    modal.style.display = 'flex';
  }

  function closeModal() {
    var modal = getModal();
    modal.classList.remove('open');
    setTimeout(function () { modal.style.display = 'none'; modal.innerHTML = ''; }, 200);
    ACTIVE_TURN_ID = null;
  }

  function updateSubmitState(modal) {
    var submitBtn = modal.querySelector('#rm-submit');
    if (!submitBtn) return;
    var speakerNameInput = modal.querySelector('#rm-speaker-name');
    var evidenceNote = modal.querySelector('#rm-evidence');
    var hasType = modal.querySelector('#rm-type-council').checked ||
      modal.querySelector('#rm-type-staff').checked ||
      modal.querySelector('#rm-type-public').checked ||
      modal.querySelector('#rm-type-unknown').checked;
    var hasName = speakerNameInput && speakerNameInput.value.trim().length > 0;
    var hasNote = evidenceNote && evidenceNote.value.trim().length > 0;
    var needsNote = hasName;
    submitBtn.disabled = !hasType || (needsNote && !hasNote);
  }

  function saveDecision(decision) {
    addPending(decision);
    renderSidebar();
    updateBannerCounts();
    wireLabelButtons();
    closeModal();
    showToast('Decision saved — ' + PENDING_DECISIONS.length + ' staged');
  }

  function buildDecisionFromModal(modal) {
    var speakerName = modal.querySelector('#rm-speaker-name').value.trim();
    var reviewer = modal.querySelector('#rm-reviewer').value.trim() || REVIEWER_DEFAULT;
    var typeCouncil = modal.querySelector('#rm-type-council').checked;
    var typeStaff = modal.querySelector('#rm-type-staff').checked;
    var typePublic = modal.querySelector('#rm-type-public').checked;
    var typeUnknown = modal.querySelector('#rm-type-unknown').checked;
    var evidenceNote = (modal.querySelector('#rm-evidence').value || '').trim();

    var speakerType = '';
    var action = 'keep_unknown';
    var speakerPublic = '';
    var speakerStatus = '';

    if (typeUnknown) {
      action = 'keep_unknown';
      speakerType = 'unknown';
    } else if (typePublic) {
      action = 'mark_public_comment';
      speakerType = 'public_comment';
      speakerPublic = speakerName || 'Public Comment Speaker';
      speakerStatus = 'approved';
    } else if (typeCouncil) {
      action = 'approve_named_official';
      speakerType = 'council';
      speakerPublic = speakerName;
      speakerStatus = 'approved';
    } else if (typeStaff) {
      action = 'approve_named_official';
      speakerType = 'staff';
      speakerPublic = speakerName;
      speakerStatus = 'approved';
    }

    return {
      turn_id: ACTIVE_TURN_ID,
      decision_id: existing && existing.decision_id ? existing.decision_id : generateId(),
      reviewer_action: action,
      speaker_name: speakerName,
      speaker_type: speakerType,
      evidence_note: evidenceNote,
      speaker_public_override: speakerPublic,
      speaker_status_override: speakerStatus,
      text_override: '',
      suppress: false,
      notes: evidenceNote,
      timestamp: Date.now(),
      reviewer: reviewer,
    };
  }

  function getModalHtml(blockInfo, existing) {
    var timeLabel = formatTime(blockInfo.start);
    var previewText = (blockInfo.texts[0] || '').slice(0, 120) + (blockInfo.texts[0] || '').length > 120 ? '…' : '';
    var exSpeaker = existing ? existing.speaker_name || '' : '';
    var exNotes = existing ? (existing.evidence_note || existing.notes || '') : '';
    var exType = existing ? existing.speaker_type || '' : '';
    var exReviewer = existing && existing.reviewer ? existing.reviewer : REVIEWER_DEFAULT;

    return [
      '<div class="review-modal-content">',
        '<h3><i class="fas fa-tag"></i> ' + (existing ? 'Edit Staged Label' : 'Label Speaker') + '</h3>',

        // Turn info
        '<div class="rm-section">',
          '<label class="rm-label">Turn</label>',
          '<div class="rm-info-text">',
            '<span class="rm-turn-id">' + escHtml(blockInfo.turnIds[0]) + '</span> &bull; ',
            '<span class="rm-turn-time">' + timeLabel + '</span>',
          '</div>',
        '</div>',

        // Text preview
        '<div class="rm-section">',
          '<label class="rm-label">Speaker text</label>',
          '<div class="rm-turn-preview">' + escHtml(previewText) + '</div>',
        '</div>',

        // Quick actions
        '<div class="rm-section rm-quick-actions">',
          '<button type="button" id="rm-quick-keep-unknown" class="mini-btn rm-quick-btn">Keep unknown</button>',
          '<button type="button" id="rm-quick-public" class="mini-btn rm-quick-btn">Public comment</button>',
          '<button type="button" id="rm-quick-suppress" class="mini-btn rm-quick-btn rm-quick-btn-warn"><i class="fas fa-ban"></i> Suppress turn</button>',
        '</div>',

        // Speaker name
        '<div class="rm-section">',
          '<label class="rm-label" for="rm-speaker-name">Speaker name</label>',
          '<input type="text" id="rm-speaker-name" class="rm-input" value="' + escHtml(exSpeaker) + '" placeholder="Type or pick from list below" autocomplete="off">',
          '<div class="rm-quick-pick-label">Council members:</div>',
          '<div class="rm-quick-pick">',
            COUNCIL_QUICK_PICK.map(function (n) { return '<button type="button" class="quick-pick-btn">' + escHtml(n) + '</button>'; }).join(''),
          '</div>',
          '<div class="rm-quick-pick-label" style="margin-top:8px;">Staff:</div>',
          '<div class="rm-quick-pick">',
            STAFF_QUICK_PICK.map(function (n) { return '<button type="button" class="quick-pick-btn">' + escHtml(n) + '</button>'; }).join(''),
          '</div>',
        '</div>',

        // Speaker type
        '<div class="rm-section">',
          '<label class="rm-label">Speaker type</label>',
          '<div class="rm-radio-group">',
            '<label class="rm-radio"><input type="radio" name="rm-type" id="rm-type-council" value="council"' + (exType === 'council' ? ' checked' : '') + '> Council / Mayor</label>',
            '<label class="rm-radio"><input type="radio" name="rm-type" id="rm-type-staff" value="staff"' + (exType === 'staff' ? ' checked' : '') + '> Staff</label>',
            '<label class="rm-radio"><input type="radio" name="rm-type" id="rm-type-public" value="public_comment"' + (exType === 'public_comment' ? ' checked' : '') + '> Public comment</label>',
            '<label class="rm-radio"><input type="radio" name="rm-type" id="rm-type-unknown" value="unknown"' + (exType === 'unknown' || !exType ? ' checked' : '') + '> Keep unknown</label>',
          '</div>',
        '</div>',

        // Evidence notes (full text stored — not truncated in export)
        '<div class="rm-section">',
          '<label class="rm-label" for="rm-evidence">Evidence / notes <span class="rm-required">*</span></label>',
          '<textarea id="rm-evidence" class="rm-textarea" rows="3" placeholder="e.g. Video frame at 6899s shows CM PETERSON nameplate">' + escHtml(exNotes) + '</textarea>',
          '<p class="rm-hint-text">Required for any named label. Stored in full in export; truncated in sidebar display.</p>',
        '</div>',

        // Reviewer identity
        '<div class="rm-section">',
          '<label class="rm-label" for="rm-reviewer">Reviewer name</label>',
          '<input type="text" id="rm-reviewer" class="rm-input" value="' + escHtml(exReviewer) + '" placeholder="Your name or alias" autocomplete="off">',
          '<p class="rm-hint-text">Included in audit metadata for traceability. Default: "manual-review".</p>',
        '</div>',

        // Actions
        '<div class="rm-actions">',
          '<button type="button" id="rm-submit" class="mini-btn primary-btn" disabled><i class="fas fa-save"></i> Save decision</button>',
          '<button type="button" id="rm-cancel" class="mini-btn">Cancel</button>',
        '</div>',
      '</div>',
    ].join('');
  }

  // ---- Init ----
  function init() {
    if (!isReviewMode()) return;

    var meta = getMeetingMeta();
    MEETING_ID = meta.id;
    PENDING_DECISIONS = loadPending();
    loadExportedSet();
    DIRTY_STATE = PENDING_DECISIONS.length > 0 && Object.keys(EXPORTED_SET).length === 0;

    window.addEventListener('beforeunload', handleBeforeUnload);

    if (!isSessionConfirmed()) {
      showPassphraseGate(function () {
        proceedInit();
      });
    } else {
      proceedInit();
    }
  }

  function proceedInit() {
    showReviewBanner();
    renderSidebar();

    var checkAndWire = function () {
      var container = document.getElementById('transcript');
      if (container && container.children.length > 0) {
        wireLabelButtons();
        return true;
      }
      return false;
    };
    if (!checkAndWire()) {
      var observer = new MutationObserver(function () {
        if (checkAndWire()) observer.disconnect();
      });
      observer.observe(document.getElementById('transcript') || document.body, { childList: true, subtree: true });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();