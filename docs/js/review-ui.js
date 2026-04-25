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
  var CURRENTLY_HIGHLIGHTED_BLOCK = null;  // currently keyboard-navigated unknown block
  var VOICE_CLUSTERS = null;     // loaded from reviews/<meeting_id>-voice-clusters.json // gitignored, served via raw GitHub
  var VIDEO_EMBED_OPEN = false;  // true when floating video panel is open
  var ACTIVE_CLUSTER_VIDEO = null;  // {start, sourceUrl} for the floating panel
  var ACTIVE_SIDEBAR_TAB = 'decisions';  // 'decisions' | 'clusters'

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
      sourceUrl: String(m.source_url || '').trim(),
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
    console.log('[review-ui] wireLabelButtons called, speaker-blocks:', document.querySelectorAll('.speaker-block').length);
    var blocks = buildBlockIndex();
    console.log('[review-ui] buildBlockIndex returned:', blocks.length, 'blocks');
    if (blocks.length > 0) console.log('[review-ui] first block speaker:', blocks[0].speaker, 'key:', blocks[0].speakerKey);
    console.log('[review-ui] speakerKey("Unknown Speaker"):', speakerKey('Unknown Speaker'));
    document.querySelectorAll('.speaker-block').forEach(function (block) {
      var speakerKey2 = String(block.dataset.speaker || '').toLowerCase();
      console.log('[review-ui] block dataset.speaker:', block.dataset.speaker, '-> key:', speakerKey2, 'compare:', speakerKey2 === speakerKey('Unknown Speaker'));
      // Label button appears on ALL speaker blocks (not just Unknown), so reviewer
      // can correct any misattributed speaker, including named officials and public commenters.
      // Only skip if block has no turn IDs.
      var blockInfoForThisBlock = findDomBlockForBlock({
        speakerKey: block.dataset.speaker || '',
        start: Number(block.dataset.time) || 0
      });
      if (!blockInfoForThisBlock || !blockInfoForThisBlock.turnIds || blockInfoForThisBlock.turnIds.length === 0) return;
      if (block.querySelector('.label-btn')) return;

      var staged = PENDING_DECISIONS.find(function (d) {
        return blockInfoForThisBlock.turnIds.indexOf(d.turn_id) >= 0;
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
        try {
          var tid = blockInfoForThisBlock.turnIds[0];
          openModalForTurn(tid == null ? blockInfoForThisBlock : tid);
        } catch (err) {
          console.error('[review-ui] openModalForTurn error:', err);
        }
      });
      var hdr = block.querySelector('.turn-header');
      if (hdr) {
        hdr.appendChild(btn);
        console.log('[review-ui] Label button appended to turn-header for block speaker=' + blockInfoForThisBlock.speaker + ', turnIds=' + JSON.stringify(blockInfoForThisBlock.turnIds));
      } else {
        console.log('[review-ui] ERROR: no .turn-header found in block - speakerKey=' + block.dataset.speaker + ', start=' + block.dataset.time);
      }
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

    var APPLY_WORKER_URL = 'https://fairfax-apply.norrinopenclaw.workers.dev';

    document.getElementById('review-export-btn').addEventListener('click', function () {
      var payload = getExportPayload();
      if (payload.length === 0) return;
      var decisions = payload; // array of decisions
      var turnIds = decisions.map(function (d) { return d.turn_id; });
      markExported(turnIds);
      showToast('Applying decisions…');
      fetch(APPLY_WORKER_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ meeting_id: MEETING_ID, decisions: decisions })
      }).then(function (res) {
        if (res.ok) {
          return res.json().then(function (r) {
            showToast('✅ ' + r.message);
          });
        } else {
          return res.text().then(function (err) {
            showToast('Apply failed: ' + err.slice(0, 100));
          });
        }
      }).catch(function () {
        showToast('Network error — export manually if needed');
      });
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

  // ---- Voice clusters ----
  function loadVoiceClusters() {
    if (!MEETING_ID) return;
    try {
      var xhr = new XMLHttpRequest();
      xhr.open('GET', '../reviews/' + MEETING_ID + '-voice-clusters.json', false);
      xhr.send(null);
      if (xhr.status === 200) {
        VOICE_CLUSTERS = JSON.parse(xhr.responseText);
      } else {
        VOICE_CLUSTERS = null;
      }
    } catch (e) {
      VOICE_CLUSTERS = null;
    }
  }

  function stageClusterDecisions(cluster) {
    // Stage an 'approve_named_official' decision for every turn in the cluster
    var speakerName = cluster.likely_speaker || '';
    var speakerKey2 = cluster.likely_speaker_key || '';
    // Determine speaker type from key prefix or name heuristics
    var speakerType = 'council';
    if (/^(jc_martinez|mr_alexander|william_pitchford)/i.test(speakerKey2)) {
      speakerType = 'staff';
    }
    for (var i = 0; i < cluster.turn_ids.length; i++) {
      var turnId = cluster.turn_ids[i];
      var existing = PENDING_DECISIONS.find(function (d) { return d.turn_id === turnId; });
      var decision = {
        turn_id: turnId,
        decision_id: existing && existing.decision_id ? existing.decision_id : generateId(),
        reviewer_action: 'approve_named_official',
        speaker_name: speakerName,
        speaker_type: speakerType,
        evidence_note: 'Bulk label from voice cluster "' + cluster.cluster_id + '" (confidence ' + cluster.confidence + ')',
        speaker_public_override: speakerName,
        speaker_status_override: 'approved',
        text_override: '',
        suppress: false,
        notes: 'Bulk label from voice cluster "' + cluster.cluster_id + '" (confidence ' + cluster.confidence + ')',
        timestamp: Date.now(),
        reviewer: REVIEWER_DEFAULT,
      };
      addPending(decision);
    }
    markDirty();
    renderSidebar();
    updateBannerCounts();
    wireLabelButtons();
    showToast('Staged ' + cluster.turn_ids.length + ' turn(s) as "' + speakerName + '"');
  }

  function stageSingletonDecision(turnId, speakerName) {
    // Quick-label a singleton turn as the most likely speaker (council by default)
    var speakerKey2 = speakerName ? speakerName.toLowerCase().replace(/\s+/g, '') : '';
    var speakerType = 'council';
    if (/^(jc_martinez|mr_alexander|william_pitchford)/i.test(speakerKey2)) {
      speakerType = 'staff';
    }
    var existing = PENDING_DECISIONS.find(function (d) { return d.turn_id === turnId; });
    var decision = {
      turn_id: turnId,
      decision_id: existing && existing.decision_id ? existing.decision_id : generateId(),
      reviewer_action: 'approve_named_official',
      speaker_name: speakerName,
      speaker_type: speakerType,
      evidence_note: 'Bulk label from voice cluster singleton',
      speaker_public_override: speakerName,
      speaker_status_override: 'approved',
      text_override: '',
      suppress: false,
      notes: 'Bulk label from voice cluster singleton',
      timestamp: Date.now(),
      reviewer: REVIEWER_DEFAULT,
    };
    addPending(decision);
    markDirty();
    renderSidebar();
    updateBannerCounts();
    wireLabelButtons();
    showToast('Staged turn as "' + speakerName + '"');
  }

  function renderVoiceClustersPanel() {
    var meta = getMeetingMeta();
    if (!meta.id) return '<div class="review-sidebar-empty">No meeting ID.</div>';

    loadVoiceClusters();

    if (!VOICE_CLUSTERS) {
      return '<div class="review-sidebar-header">' +
        '<h3><i class="fas fa-waveform"></i> Voice Clusters</h3>' +
        '</div>' +
        '<div class="review-sidebar-empty">' +
        'No clusters file found for this meeting.<br><br>' +
        'Run clustering first:<br>' +
        '<code style="font-size:11px;">python3 scripts/cluster_for_review.py ' + escHtml(meta.id) + '</code>' +
        '</div>';
    }

    var clusters = VOICE_CLUSTERS.clusters || [];
    var singletons = VOICE_CLUSTERS.singletons || [];
    var totalUnknown = clusters.reduce(function (s, c) { return s + c.turn_ids.length; }, 0) + singletons.length;

    var html = '<div class="review-sidebar-header">' +
      '<h3><i class="fas fa-waveform"></i> Voice Clusters</h3>' +
      '</div>' +
      '<div class="vc-meta">' +
        clusters.length + ' cluster(s), ' + totalUnknown + ' unknown turn(s)</div>' +
      '<div id="vc-video-panel" style="display:none;">' +
        '<div id="vc-video-area"></div>' +
        '<div style="text-align:right;margin-top:4px;">' +
          '<button type="button" id="vc-video-close-btn" style="font-size:11px;padding:2px 8px;background:transparent;border:1px solid #cbd5e0;border-radius:4px;color:#718096;cursor:pointer;">Hide video</button>' +
        '</div>' +
      '</div>';

    // Clusters
    if (clusters.length === 0 && singletons.length === 0) {
      html += '<div class="review-sidebar-empty">No unknown turns to cluster.</div>';
      return html;
    }

    for (var ci = 0; ci < clusters.length; ci++) {
      var cluster = clusters[ci];
      var confPct = Math.round((cluster.confidence || 0) * 100);
      var clusterId = 'vc-cluster-' + ci;
      var isExpanded = ci === 0; // expand first cluster by default

      html += '<div class="vc-cluster">' +
        '<div class="vc-cluster-header" data-cluster="' + ci + '">' +
          '<span class="vc-cluster-toggle"><i class="fas fa-chevron-' + (isExpanded ? 'down' : 'right') + '"></i></span>' +
          '<span class="vc-cluster-speaker">' + escHtml(cluster.likely_speaker || '?') + '</span>' +
          '<span class="vc-cluster-meta">' + cluster.turn_ids.length + ' turn(s) &bull; ' + confPct + '% conf</span>' +
        '</div>' +
        '<div class="vc-cluster-body' + (isExpanded ? '' : ' vc-hidden') + '" id="' + clusterId + '">';

      // Per-turn text previews with video links
      var texts = cluster.texts || [];
      var startTimes = cluster.start_times || [];
      for (var ti = 0; ti < texts.length; ti++) {
        var preview = texts[ti].slice(0, 100) + (texts[ti].length > 100 ? '…' : '');
        var ts = startTimes[ti];
        var videoBtn = '';
        if (ts != null) {
          videoBtn = '<button type="button" class="vc-video-btn" data-start="' + ts + '" title="Watch at ' + formatTime(ts) + '"><i class="fas fa-play"></i></button>';
        }
        html += '<div class="vc-turn-text">' + videoBtn + '<span>' + escHtml(preview) + '</span></div>';
      }

      html +=
        '<div class="vc-cluster-actions">' +
          '<button type="button" class="vc-label-cluster-btn" data-cluster="' + ci + '">' +
            '<i class="fas fa-tag"></i> Label all as ' + escHtml(cluster.likely_speaker || '?') +
          '</button>' +
        '</div>' +
      '</div></div>';
    }

    // Singletons
    if (singletons.length > 0) {
      html += '<div class="vc-singletons-section">' +
        '<div class="vc-singletons-header">' +
          '<span>' + singletons.length + ' singleton(s) — no confident match</span>' +
        '</div>';
      // Show first 10 singletons with quick-label
      var showCount = Math.min(singletons.length, 10);
      for (var si = 0; si < showCount; si++) {
        var sTurnId = singletons[si];
        var sTurnStart = 0;
        // Find the turn text and start time from TRANSCRIPT_TURNS
        var sTurn = null;
        var allTurns = getTurns();
        for (var ti = 0; ti < allTurns.length; ti++) {
          if (String(allTurns[ti].turn_id || '') === String(sTurnId)) {
            sTurn = allTurns[ti];
            break;
          }
        }
        if (sTurn) {
          sTurnStart = parseFloat(sTurn.start || sTurn.time || 0);
        }
        var sText = sTurn ? (sTurn.text || '').slice(0, 80) + ((sTurn.text || '').length > 80 ? '…' : '') : sTurnId;
        var sVideoBtn = sTurnStart > 0
          ? '<button type="button" class="vc-video-btn" data-start="' + sTurnStart + '" title="Watch at ' + formatTime(sTurnStart) + '"><i class="fas fa-play"></i></button>'
          : '';
        html += '<div class="vc-singleton-item">' +
          '<div class="vc-singleton-turn">' + escHtml(String(sTurnId)) + '</div>' +
          '<div class="vc-singleton-text">' + sVideoBtn + '<span>' + escHtml(sText) + '</span></div>' +
          '<div class="vc-singleton-actions">';
        // Show council quick-picks for singleton
        for (var qi = 0; qi < COUNCIL_QUICK_PICK.length; qi++) {
          var qName = COUNCIL_QUICK_PICK[qi];
          html += '<button type="button" class="vc-singleton-label-btn" data-turn="' + escHtml(String(sTurnId)) + '" data-speaker="' + escHtml(qName) + '">' +
            escHtml(qName.split(' ').pop()) + '</button>';
        }
        html += '</div></div>';
      }
      if (singletons.length > 10) {
        html += '<div class="vc-singletons-more">+' + (singletons.length - 10) + ' more (stage individually via transcript)</div>';
      }
      html += '</div>';
    }

    return html;
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

    // Tab bar
    var html = '<div class="review-sidebar-tabs">' +
      '<button type="button" class="review-tab-btn' + (ACTIVE_SIDEBAR_TAB === 'decisions' ? ' active' : '') + '" data-tab="decisions">' +
        '<i class="fas fa-list"></i> Staged <span class="review-tab-count">' + pending.length + '</span>' +
      '</button>' +
      '<button type="button" class="review-tab-btn' + (ACTIVE_SIDEBAR_TAB === 'clusters' ? ' active' : '') + '" data-tab="clusters">' +
        '<i class="fas fa-waveform"></i> Voice Clusters' +
      '</button>' +
    '</div>';

    // Decisions panel
    html += '<div class="review-tab-panel" id="review-decisions-panel">';
    if (pending.length === 0) {
      html += '<div class="review-sidebar-empty">No staged decisions yet.<br>Click "Label speaker" on an unlabeled block to begin.</div>';
    }

    // Close decisions panel and open clusters panel based on active tab
    if (ACTIVE_SIDEBAR_TAB === 'clusters') {
      html += '</div>'; // close decisions panel
      html += '<div class="review-tab-panel" id="review-clusters-panel">';
      html += renderVoiceClustersPanel();
      html += '</div>'; // close clusters panel
      sidebar.innerHTML = html;
      wireSidebarEvents();
      return;
    }

    // ---- Decisions panel content ----
    if (pending.length > 0) {
      html += '<div class="review-sidebar-header">' +
        '<h3><i class="fas fa-list"></i> Staged Decisions <span class="review-sidebar-count">' + pending.length + '</span></h3>' +
      '</div>';
    }

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

    html += '</div>'; // close decisions panel
    html += '</div>'; // close tab-panels wrapper

    sidebar.innerHTML = html;
    wireSidebarEvents();
  }

  function wireSidebarEvents() {
    var sidebar = getSidebar();

    // Tab switching
    sidebar.querySelectorAll('.review-tab-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var tab = btn.getAttribute('data-tab');
        ACTIVE_SIDEBAR_TAB = tab;
        renderSidebar();
      });
    });

    // Decision edit/remove
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

    // Voice cluster expand/collapse
    sidebar.querySelectorAll('.vc-cluster-header').forEach(function (hdr) {
      hdr.addEventListener('click', function () {
        var clusterIdx = parseInt(hdr.getAttribute('data-cluster') || '0', 10);
        var bodyId = 'vc-cluster-' + clusterIdx;
        var body = document.getElementById(bodyId);
        if (!body) return;
        var isHidden = body.classList.contains('vc-hidden');
        body.classList.toggle('vc-hidden');
        var icon = hdr.querySelector('.vc-cluster-toggle i');
        if (icon) {
          icon.className = isHidden ? 'fas fa-chevron-down' : 'fas fa-chevron-right';
        }
      });
    });

    // Video button in cluster turn list
    sidebar.querySelectorAll('.vc-video-btn').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.stopPropagation();
        var startSec = parseInt(btn.getAttribute('data-start') || '0', 10);
        var meta = getMeetingMeta();
        showClusterVideo(startSec, meta.sourceUrl);
      });
    });

    // Close cluster video button
    var vcCloseBtn = document.getElementById('vc-video-close-btn');
    if (vcCloseBtn) {
      vcCloseBtn.addEventListener('click', closeClusterVideo);
    }

    // Label all in cluster
    sidebar.querySelectorAll('.vc-label-cluster-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var clusterIdx = parseInt(btn.getAttribute('data-cluster') || '0', 10);
        if (VOICE_CLUSTERS && VOICE_CLUSTERS.clusters && VOICE_CLUSTERS.clusters[clusterIdx]) {
          stageClusterDecisions(VOICE_CLUSTERS.clusters[clusterIdx]);
        }
      });
    });

    // Label singleton individually
    sidebar.querySelectorAll('.vc-singleton-label-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var turnId = btn.getAttribute('data-turn');
        var speakerName = btn.getAttribute('data-speaker');
        stageSingletonDecision(turnId, speakerName);
      });
    });
  }

  function showClusterVideo(startSec, sourceUrl) {
    if (!sourceUrl) return;
    ACTIVE_CLUSTER_VIDEO = { start: startSec, sourceUrl: sourceUrl };
    var panel = document.getElementById('vc-video-panel');
    var area = document.getElementById('vc-video-area');
    if (!panel || !area) return;
    var embedUrl = makeVideoEmbedUrl(sourceUrl, startSec);
    area.innerHTML = '<div class=\'rm-video-container\'><div class=\'rm-video-placeholder\'>Loading...</div></div>';
    var container = area.querySelector('.rm-video-container');
    var iframe = document.createElement('iframe');
    iframe.src = embedUrl;
    iframe.allow = 'autoplay; fullscreen';
    iframe.title = 'Video at ' + formatTime(startSec);
    container.innerHTML = '';
    container.appendChild(iframe);
    panel.style.display = '';
    VIDEO_EMBED_OPEN = true;
  }

  function closeClusterVideo() {
    var area = document.getElementById('vc-video-area');
    if (area) area.innerHTML = '';
    var panel = document.getElementById('vc-video-panel');
    if (panel) panel.style.display = 'none';
    VIDEO_EMBED_OPEN = false;
    ACTIVE_CLUSTER_VIDEO = null;
  }

  function makeVideoEmbedUrl(sourceUrl, blockStart) {
    if (!sourceUrl) return '';
    try {
      var u = new URL(sourceUrl);
      if (blockStart > 0) {
        u.searchParams.set('entrytime', String(Math.floor(Number(blockStart) || 0)));
        u.searchParams.set('autostart', '1');
      }
      return u.toString();
    } catch (_) {
      return sourceUrl;
    }
  }

  function showVideoEmbed(blockStart, sourceUrl) {
    if (!sourceUrl) return;
    VIDEO_EMBED_OPEN = true;
    var area = document.getElementById('rm-video-embed-area');
    if (!area) return;
    var clipId = sourceUrl.split('/').pop() || '';
    var embedUrl = makeVideoEmbedUrl(sourceUrl, blockStart);
    area.innerHTML = '<div class="rm-video-container"><div class="rm-video-placeholder">Loading video...</div></div>';
    var container = area.querySelector('.rm-video-container');
    var iframe = document.createElement('iframe');
    iframe.src = embedUrl;
    iframe.allow = 'autoplay; fullscreen';
    iframe.title = 'Video at ' + formatTime(blockStart);
    container.innerHTML = '';
    container.appendChild(iframe);
    document.getElementById('rm-video-toggle-btn').style.display = 'none';
    var closeRow = document.createElement('div');
    closeRow.className = 'rm-video-close-row';
    closeRow.innerHTML = '<button type="button" id="rm-video-close-btn" class="rm-video-close-btn"><i class="fas fa-times"></i> Hide video</button>';
    area.appendChild(closeRow);
    document.getElementById('rm-video-close-btn').addEventListener('click', closeVideoEmbed);
  }

  function closeVideoEmbed() {
    VIDEO_EMBED_OPEN = false;
    var area = document.getElementById('rm-video-embed-area');
    if (area) area.innerHTML = '';
    var toggleBtn = document.getElementById('rm-video-toggle-btn');
    if (toggleBtn) toggleBtn.style.display = '';
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
    console.log('[review-ui] openModalForTurn called, turnId=' + turnId);
    var blocks = buildBlockIndex();
    var blockInfo = null;

    // Accept either a turnId string or a blockInfo object directly
    if (turnId && typeof turnId === 'object' && turnId.speaker !== undefined) {
      blockInfo = turnId;
    } else if (turnId === null || turnId === undefined) {
      // Use first block with unknown speaker as fallback for testing
      blockInfo = blocks.find(function(b) { return b.speakerKey === speakerKey('Unknown Speaker'); }) || null;
    } else {
      for (var i = 0; i < blocks.length; i++) {
        if (blocks[i].turnIds.indexOf(String(turnId)) >= 0) {
          blockInfo = blocks[i];
          break;
        }
      }
    }
    if (!blockInfo) { console.log('[review-ui] openModalForTurn: blockInfo not found for turnId=' + turnId); return; }
    console.log('[review-ui] openModalForTurn: blockInfo found, speaker=' + blockInfo.speaker);

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
        // Auto-select Council/Mayor for named council members, Staff for staff names
        if (typeCouncil) typeCouncil.checked = true;
        if (typeStaff) typeStaff.checked = false;
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

    // Quick Public comment — stage decision and show confirmation, keep modal open
    if (quickPublic) {
      quickPublic.addEventListener('click', function () {
        var typePublic = modal.querySelector('#rm-type-public');
        if (typePublic) typePublic.checked = true;
        var decision = buildDecisionFromModal(modal);
        decision.reviewer_action = 'mark_public_comment';
        decision.speaker_type = 'public_comment';
        decision.evidence_note = decision.evidence_note || 'Public comment turn';
        addPending(decision);
        showToast('Public comment staged — ' + PENDING_DECISIONS.length + ' total');
        updateBannerCounts();
        renderSidebar();
        wireLabelButtons();
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
      saveDecision(decision);
    });

    modal.querySelector('#rm-cancel').addEventListener('click', closeModal);
    modal.addEventListener('click', function (e) {
      if (e.target === modal) closeModal();
    });

    updateSubmitState(modal);
    // Wire radio buttons to re-check submit state on change
    modal.querySelectorAll('input[name="rm-type"]').forEach(function (radio) {
      radio.addEventListener('change', function () { updateSubmitState(modal); });
    });
    modal.classList.add('open');
    modal.style.display = 'flex';

    // Wire video toggle
    var videoToggleBtn = modal.querySelector('#rm-video-toggle-btn');
    if (videoToggleBtn) {
      videoToggleBtn.addEventListener('click', function () {
        var meta = getMeetingMeta();
        showVideoEmbed(blockInfo.start, meta.sourceUrl);
      });
    }
  }

  function closeModal() {
    var modal = getModal();
    closeVideoEmbed();
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
    submitBtn.disabled = !hasType;
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
      decision_id: (function () {
        var prev = PENDING_DECISIONS.find(function (d) { return d.turn_id === ACTIVE_TURN_ID; });
        return prev && prev.decision_id ? prev.decision_id : generateId();
      })(),
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
    var exSpeaker = existing ? existing.speaker_name || '' : (blockInfo.speaker || '');
    var exNotes = existing ? (existing.evidence_note || existing.notes || '') : '';
    var exType = existing ? existing.speaker_type || '' : (blockInfo.speaker && blockInfo.speaker !== 'Unknown Speaker' ? 'labeled' : '');
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

        // Video embed
        '<div class="rm-video-section" id="rm-video-section">',
          '<div class="rm-video-header">',
            '<span>Video at ' + timeLabel + '</span>',
            '<button type="button" id="rm-video-toggle-btn" class="rm-video-link-btn">',
              '<i class="fas fa-play"></i> Watch video',
            '</button>',
          '</div>',
          '<div id="rm-video-embed-area"></div>',
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

  // ---- Keyboard navigation ----
  // TRANSCRIPT_BLOCKS is set by transcript-page.js after rendering (via window.TRANSCRIPT_BLOCKS).
  function getAllUnknownDomBlocks() {
    var all = window.TRANSCRIPT_BLOCKS || [];
    var result = [];
    for (var i = 0; i < all.length; i++) {
      if (all[i].speakerKey === speakerKey('Unknown Speaker')) result.push(all[i]);
    }
    return result;
  }

  function findDomBlockForBlock(blockInfo) {
    var all = document.querySelectorAll('.speaker-block');
    for (var i = 0; i < all.length; i++) {
      var el = all[i];
      // Normalize both sides to lowercase for reliable comparison.
      // transcript-page.js stores dataset.speaker via speakerKey() (already lowercased),
      // but we lowercase again here to handle any edge cases.
      if (String(el.dataset.speaker || '').toLowerCase() === String(blockInfo.speakerKey || '').toLowerCase() &&
          String(el.dataset.time || '') === String(Math.floor(blockInfo.start || 0))) {
        return el;
      }
    }
    return null;
  }

  function setReviewHighlight(blockEl) {
    if (CURRENTLY_HIGHLIGHTED_BLOCK) {
      CURRENTLY_HIGHLIGHTED_BLOCK.classList.remove('review-highlighted');
    }
    CURRENTLY_HIGHLIGHTED_BLOCK = blockEl;
    if (blockEl) {
      blockEl.classList.add('review-highlighted');
      blockEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

  function showShortcutsOverlay() {
    var existing = document.getElementById('review-shortcuts-overlay');
    if (existing) existing.remove();
    var overlay = document.createElement('div');
    overlay.id = 'review-shortcuts-overlay';
    overlay.innerHTML =
      '<div class="review-shortcuts-box">' +
        '<h3>Keyboard Shortcuts</h3>' +
        '<table>' +
          '<tr><td><kbd>j</kbd> / <kbd>\u2193</kbd></td><td>Next unknown block</td></tr>' +
          '<tr><td><kbd>k</kbd> / <kbd>\u2191</kbd></td><td>Previous unknown block</td></tr>' +
          '<tr><td><kbd>l</kbd></td><td>Label currently highlighted block</td></tr>' +
          '<tr><td><kbd>Esc</kbd></td><td>Close modal</td></tr>' +
          '<tr><td><kbd>?</kbd></td><td>Show this overlay</td></tr>' +
        '</table>' +
        '<button type="button" id="review-shortcuts-close" class="mini-btn" style="margin-top:14px;">Close</button>' +
      '</div>';
    overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);z-index:4000;display:flex;align-items:center;justify-content:center;padding:20px;';
    document.body.appendChild(overlay);
    overlay.querySelector('#review-shortcuts-close').addEventListener('click', function () { overlay.remove(); });
    overlay.addEventListener('click', function (e) { if (e.target === overlay) overlay.remove(); });
  }

  function showShortcutsToast() {
    try {
      if (sessionStorage.getItem('review_shortcuts_toast_shown')) return;
      sessionStorage.setItem('review_shortcuts_toast_shown', '1');
    } catch (e) {}
    var toast = document.createElement('div');
    toast.id = 'review-shortcuts-toast';
    toast.className = 'toast';
    toast.textContent = 'Press ? for keyboard shortcuts';
    document.body.appendChild(toast);
    setTimeout(function () { toast.classList.add('show'); }, 10);
    setTimeout(function () {
      toast.classList.remove('show');
      setTimeout(function () { toast.remove(); }, 300);
    }, 3500);
  }

  function handleReviewKeyboard(e) {
    var modal = getModal();
    var modalOpen = modal && modal.style.display !== 'none' && modal.classList.contains('open');

    if (e.key === 'Escape') {
      if (modalOpen) { closeModal(); e.preventDefault(); }
      return;
    }

    if (modalOpen) return;

    var unknownBlocks = getAllUnknownDomBlocks();
    if (!unknownBlocks.length) return;

    if (e.key === '?' || e.key === '/') {
      showShortcutsOverlay();
      e.preventDefault();
      return;
    }

    if (e.key === 'j' || e.key === 'ArrowDown') {
      var unknownDomEls = [];
      var allEls = document.querySelectorAll('.speaker-block');
      for (var ai = 0; ai < allEls.length; ai++) {
        if (allEls[ai].dataset.speaker === speakerKey('Unknown Speaker')) unknownDomEls.push(allEls[ai]);
      }
      var curIdx = CURRENTLY_HIGHLIGHTED_BLOCK ? unknownDomEls.indexOf(CURRENTLY_HIGHLIGHTED_BLOCK) : -1;
      var nextIdx = curIdx < unknownDomEls.length - 1 ? curIdx + 1 : 0;
      setReviewHighlight(unknownDomEls[nextIdx]);
      e.preventDefault();
    } else if (e.key === 'k' || e.key === 'ArrowUp') {
      var unknownDomEls2 = [];
      var allEls2 = document.querySelectorAll('.speaker-block');
      for (var bi = 0; bi < allEls2.length; bi++) {
        if (allEls2[bi].dataset.speaker === speakerKey('Unknown Speaker')) unknownDomEls2.push(allEls2[bi]);
      }
      var curIdx2 = CURRENTLY_HIGHLIGHTED_BLOCK ? unknownDomEls2.indexOf(CURRENTLY_HIGHLIGHTED_BLOCK) : 0;
      var prevIdx = curIdx2 > 0 ? curIdx2 - 1 : unknownDomEls2.length - 1;
      setReviewHighlight(unknownDomEls2[prevIdx]);
      e.preventDefault();
    } else if (e.key === 'l') {
      var el = CURRENTLY_HIGHLIGHTED_BLOCK;
      if (!el && unknownBlocks.length > 0) {
        var firstEl = findDomBlockForBlock(unknownBlocks[0]);
        if (firstEl) { setReviewHighlight(firstEl); el = firstEl; }
      }
      if (el) {
        var blockStart = parseInt(el.dataset.time || '0', 10);
        var blockSpk = el.dataset.speaker || '';
        for (var ci = 0; ci < unknownBlocks.length; ci++) {
          if (String(unknownBlocks[ci].speakerKey || '') === String(blockSpk) &&
              Math.floor(unknownBlocks[ci].start || 0) === blockStart) {
            ACTIVE_TURN_ID = String(unknownBlocks[ci].turnIds[0] || '');
            openModalForTurn(ACTIVE_TURN_ID);
            break;
          }
        }
        e.preventDefault();
      }
    }
  }

  // ---- Init ----
  function init() {
    console.log('[review-ui] init called, isReviewMode=' + isReviewMode() + ', document.readyState=' + document.readyState);
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
      if (container && container.querySelector('.speaker-block')) {
        wireLabelButtons();
        return true;
      }
      return false;
    };
    if (!checkAndWire()) {
      var observer = new MutationObserver(function () {
        if (checkAndWire()) { observer.disconnect(); }
      });
      observer.observe(document.getElementById('transcript') || document.body, { childList: true, subtree: true });
    }

    // Keyboard navigation + first-session shortcut toast
    showShortcutsToast();
    document.addEventListener('keydown', handleReviewKeyboard);
  }

  console.log('[review-ui] init setup, about to call init()');
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
    console.log('[review-ui] added DOMContentLoaded listener');
  } else {
    console.log('[review-ui] calling init() immediately');
    init();
  }
})();