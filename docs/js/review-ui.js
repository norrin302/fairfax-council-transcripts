/* ============================================================
   Review-mode speaker labeling UI
   Enable: add ?review=1 to the transcript page URL.
   Writes to: localStorage (staging) + reviews/<meeting>-review-decisions.json (via apply)
   ============================================================ */

(function () {
  'use strict';

  // ---- Config ----
  const REVIEW_KEY = 'review_mode';
  const PENDING_KEY = (meetingId) => `reviewdecisions:pending:${String(meetingId || '').trim()}`;

  const COUNCIL_QUICK_PICK = [
    'Mayor Catherine Read',
    'Councilmember Anthony Amos',
    'Councilmember Billy Bates',
    'Councilmember Stacy Hall',
    'Councilmember Stacy Hardy-Chandler',
    'Councilmember Rachel McQuillen',
    'Councilmember Tom Peterson',
    'JC Martinez',
    'Mr. Alexander',
    'William Pitchford',
  ];

  // ---- State ----
  let REVIEW_MODE = false;
  let PENDING_DECISIONS = [];

  // ---- Helpers ----
  function getMeetingId() {
    const m = (typeof MEETING !== 'undefined' && MEETING) ? MEETING : {};
    return String(m.meeting_id || '').trim();
  }

  function getTurns() {
    return (typeof TRANSCRIPT_TURNS !== 'undefined') ? TRANSCRIPT_TURNS : [];
  }

  function isReviewMode() {
    const params = new URLSearchParams(window.location.search);
    return params.get('review') === '1';
  }

  function showToast(msg) {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();
    const t = document.createElement('div');
    t.className = 'toast';
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(() => t.classList.add('show'), 10);
    setTimeout(() => {
      t.classList.remove('show');
      setTimeout(() => t.remove(), 300);
    }, 2200);
  }

  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text);
    }
    const ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    ta.remove();
    return Promise.resolve();
  }

  function formatTime(seconds) {
    const s = Math.max(0, Math.floor(Number(seconds) || 0));
    const m = Math.floor((s % 3600) / 60);
    const sec = s % 60;
    return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
  }

  // ---- Pending decisions storage ----
  function loadPending() {
    const key = PENDING_KEY(getMeetingId());
    try {
      return JSON.parse(localStorage.getItem(key) || '[]');
    } catch (_) { return []; }
  }

  function savePending(decisions) {
    const key = PENDING_KEY(getMeetingId());
    localStorage.setItem(key, JSON.stringify(decisions || []));
  }

  function addPending(decision) {
    const all = loadPending();
    // Replace existing decision for same turn_id, or append
    const idx = all.findIndex((d) => d.turn_id === decision.turn_id);
    if (idx >= 0) all[idx] = decision;
    else all.push(decision);
    savePending(all);
    PENDING_DECISIONS = all;
  }

  // ---- Build speaker block info (index → turn_ids) ----
  function buildBlockIndexMap() {
    // Returns array parallel to rendered blocks: each entry = { start, end, turnIds[] }
    const turns = getTurns();
    const blocks = [];
    let i = 0;
    turns.forEach((turn) => {
      let speaker = String(turn.speaker || 'Unknown').trim();
      if (!speaker || speaker.toLowerCase() === 'speaker' || speaker.toLowerCase() === 'unknown') {
        speaker = 'Unknown Speaker';
      }
      const speakerSource = String(turn.speaker_source || '').trim() || (speaker === 'Unknown Speaker' ? 'unknown' : '');
      const spKey = speakerKey(speaker);
      const start = Number(turn.start) || 0;
      const end = Number(turn.end) || start;
      const text = String(turn.text || '').replace(/\s+/g, ' ').trim();
      if (!text) return;

      const last = blocks.length ? blocks[blocks.length - 1] : null;
      const canMerge = speaker !== 'Unknown Speaker';
      if (canMerge && last && String(last.speaker) === speaker && String(last.speakerSource || '') === String(speakerSource || '')) {
        last.end = Math.max(Number(last.end) || 0, end);
        last.turnIds.push(turn.turn_id);
        last.texts.push(text);
      } else {
        blocks.push({
          speaker,
          speakerKey: spKey,
          speakerSource,
          start,
          end,
          turnIds: [turn.turn_id],
          texts: [text]
        });
      }
    });
    return blocks;
  }

  function speakerKey(s) {
    return String(s || '').toLowerCase().replace(/\s+/g, ' ').trim();
  }

  // ---- Inject Label Speaker buttons into unlabeled blocks ----
  function wireLabelButtons() {
    document.querySelectorAll('.speaker-block').forEach((block) => {
      const speakerKey2 = String(block.dataset.speaker || '').toLowerCase();
      if (speakerKey2 !== speakerKey('Unknown Speaker')) return;
      // Already has a label-btn?
      if (block.querySelector('.label-btn')) return;

      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'label-btn';
      btn.title = 'Label this speaker (review mode)';
      btn.innerHTML = '<i class="fas fa-tag"></i> Label speaker';
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        openModal(block);
      });

      // Insert after the header actions
      const header = block.querySelector('.turn-header');
      if (header) header.appendChild(btn);
    });
  }

  // ---- Modal ----
  let activeBlock = null;
  let activeBlockInfo = null;

  function openModal(blockEl) {
    activeBlock = blockEl;
    const idx = parseInt(blockEl.dataset.index || '0', 10);
    const blocks = buildBlockIndexMap();
    activeBlockInfo = blocks[idx] || null;

    // Populate turn info in modal
    const modal = getModal();
    const turnInfo = modal.querySelector('#rm-turn-info');
    const turnText = modal.querySelector('#rm-turn-text');
    const speakerNameInput = modal.querySelector('#rm-speaker-name');
    const typeCouncil = modal.querySelector('#rm-type-council');
    const typeStaff = modal.querySelector('#rm-type-staff');
    const typePublic = modal.querySelector('#rm-type-public');
    const typeUnknown = modal.querySelector('#rm-type-unknown');
    const scopeThis = modal.querySelector('#rm-scope-this');
    const evidenceNote = modal.querySelector('#rm-evidence');
    const submitBtn = modal.querySelector('#rm-submit');
    const decisionOutput = modal.querySelector('#rm-decision-output');
    const copyBtn = modal.querySelector('#rm-copy-decision');
    const applyInstructions = modal.querySelector('#rm-apply-instructions');

    if (turnInfo) turnInfo.textContent = activeBlockInfo
      ? `Turn IDs: ${activeBlockInfo.turnIds.join(', ')} | Time: ${formatTime(activeBlockInfo.start)}`
      : `Index: ${idx}`;
    if (turnText) turnText.textContent = (activeBlockInfo ? activeBlockInfo.texts[0] : blockEl.querySelector('.turn-text')?.textContent || '').slice(0, 120) + '…';

    // Reset form
    speakerNameInput.value = '';
    typeCouncil.checked = false;
    typeStaff.checked = false;
    typePublic.checked = false;
    typeUnknown.checked = false;
    scopeThis.checked = true;
    evidenceNote.value = '';
    decisionOutput.style.display = 'none';
    applyInstructions.style.display = 'none';
    submitBtn.disabled = true;

    // Enable submit only when evidence note has content (for named labels)
    const updateSubmitState = () => {
      const hasName = speakerNameInput.value.trim().length > 0;
      const hasNote = evidenceNote.value.trim().length > 0;
      const hasType = typeCouncil.checked || typeStaff.checked || typePublic.checked || typeUnknown.checked;
      submitBtn.disabled = !hasType || (hasName && !hasNote);
    };

    speakerNameInput.addEventListener('input', updateSubmitState);
    evidenceNote.addEventListener('input', updateSubmitState);
    [typeCouncil, typeStaff, typePublic, typeUnknown].forEach((r) => r.addEventListener('change', updateSubmitState));

    copyBtn.style.display = 'none';

    modal.classList.add('open');
    modal.style.display = 'flex';
  }

  function closeModal() {
    const modal = getModal();
    modal.classList.remove('open');
    setTimeout(() => { modal.style.display = 'none'; }, 200);
    activeBlock = null;
    activeBlockInfo = null;
  }

  function getModal() {
    let modal = document.getElementById('review-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'review-modal';
      modal.className = 'review-modal';
      modal.style.display = 'none';
      modal.innerHTML = getModalHtml();
      document.body.appendChild(modal);

      // Close on backdrop click
      modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
      });

      // Quick-pick wiring
      modal.querySelectorAll('.quick-pick-btn').forEach((btn) => {
        btn.addEventListener('click', () => {
          const input = modal.querySelector('#rm-speaker-name');
          if (input) input.value = btn.textContent;
          // Auto-select council type
          const typeCouncil = modal.querySelector('#rm-type-council');
          if (typeCouncil) typeCouncil.checked = true;
          modal.querySelector('#rm-submit').disabled = false;
        });
      });

      // Submit
      modal.querySelector('#rm-submit').addEventListener('click', () => {
        const decision = buildDecision();
        if (!decision) return;
        addPending(decision);
        showSavedDecision(decision);
      });

      // Copy decision
      modal.querySelector('#rm-copy-decision').addEventListener('click', () => {
        const output = modal.querySelector('#rm-decision-output');
        copyText(output.textContent || '').then(() => showToast('Copied!')).catch(() => showToast('Copy failed'));
      });

      // Close
      modal.querySelector('#rm-cancel').addEventListener('click', closeModal);
    }
    return modal;
  }

  function buildDecision() {
    if (!activeBlockInfo) return null;
    const modal = getModal();

    const speakerName = modal.querySelector('#rm-speaker-name').value.trim();
    const typeCouncil = modal.querySelector('#rm-type-council').checked;
    const typeStaff = modal.querySelector('#rm-type-staff').checked;
    const typePublic = modal.querySelector('#rm-type-public').checked;
    const typeUnknown = modal.querySelector('#rm-type-unknown').checked;
    const scopeThis = modal.querySelector('#rm-scope-this').checked;
    const evidenceNote = modal.querySelector('#rm-evidence').value.trim();

    let action = 'keep_unknown';
    let speakerPublic = '';
    let speakerStatus = '';

    if (typeUnknown) {
      action = 'keep_unknown';
    } else if (typePublic) {
      action = 'mark_public_comment';
      speakerPublic = speakerName || 'Public Comment';
      speakerStatus = 'approved';
    } else if (typeStaff || typeCouncil) {
      action = 'approve_named_official';
      speakerPublic = speakerName;
      speakerStatus = 'approved';
    }

    // For scope, determine which turn_ids
    let turnIds = [];
    if (scopeThis || !activeBlockInfo) {
      turnIds = activeBlockInfo ? [activeBlockInfo.turnIds[0]] : [];
    }

    // Build decision objects
    const decisions = turnIds.map((turn_id) => ({
      turn_id,
      reviewer_action: action,
      speaker_public_override: speakerPublic,
      speaker_status_override: speakerStatus,
      text_override: '',
      suppress: false,
      notes: evidenceNote || `Reviewer: ${action}`,
    }));

    return decisions.length === 1 ? decisions[0] : decisions[0];
  }

  function showSavedDecision(decision) {
    const modal = getModal();
    const output = modal.querySelector('#rm-decision-output');
    const instructions = modal.querySelector('#rm-apply-instructions');
    const copyBtn = modal.querySelector('#rm-copy-decision');

    const json = JSON.stringify(decision, null, 2);
    output.textContent = json;
    output.style.display = 'block';
    instructions.style.display = 'block';
    copyBtn.style.display = 'inline-flex';

    // Disable form fields
    modal.querySelector('#rm-submit').disabled = true;
    modal.querySelector('#rm-speaker-name').disabled = true;
    modal.querySelector('#rm-evidence').disabled = true;
    [modal.querySelector('#rm-type-council'),
     modal.querySelector('#rm-type-staff'),
     modal.querySelector('#rm-type-public'),
     modal.querySelector('#rm-type-unknown')].forEach((r) => r.disabled = true);
    modal.querySelectorAll('.quick-pick-btn').forEach((b) => b.disabled = true);
  }

  function getModalHtml() {
    return `
      <div class="review-modal-content">
        <h3><i class="fas fa-tag"></i> Label Speaker (Review Mode)</h3>

        <div class="rm-section">
          <label class="rm-label">Turn info</label>
          <div id="rm-turn-info" class="rm-info-text"></div>
        </div>

        <div class="rm-section">
          <label class="rm-label">Speaker text preview</label>
          <div id="rm-turn-text" class="rm-turn-preview"></div>
        </div>

        <div class="rm-section">
          <label class="rm-label" for="rm-speaker-name">Speaker name</label>
          <input type="text" id="rm-speaker-name" class="rm-input" placeholder="Type or pick from list below" autocomplete="off">
          <div class="rm-quick-pick">
            <span class="rm-hint">Quick pick:</span>
            ${COUNCIL_QUICK_PICK.map((name) => `
              <button type="button" class="quick-pick-btn">${name}</button>
            `).join('')}
          </div>
        </div>

        <div class="rm-section">
          <label class="rm-label">Speaker type</label>
          <div class="rm-radio-group">
            <label class="rm-radio"><input type="radio" name="rm-type" id="rm-type-council" value="council"> Council / Mayor</label>
            <label class="rm-radio"><input type="radio" name="rm-type" id="rm-type-staff" value="staff"> Staff</label>
            <label class="rm-radio"><input type="radio" name="rm-type" id="rm-type-public" value="public_comment"> Public Comment</label>
            <label class="rm-radio"><input type="radio" name="rm-type" id="rm-type-unknown" value="unknown"> Keep unknown</label>
          </div>
        </div>

        <div class="rm-section">
          <label class="rm-label">Apply to</label>
          <div class="rm-radio-group">
            <label class="rm-radio"><input type="radio" name="rm-scope" id="rm-scope-this" value="this" checked> This turn only</label>
          </div>
          <p class="rm-hint-text">Contiguous block and same-speaker cluster application available via manual JSON editing.</p>
        </div>

        <div class="rm-section">
          <label class="rm-label" for="rm-evidence">Evidence / notes <span class="rm-required">*</span></label>
          <textarea id="rm-evidence" class="rm-textarea" rows="3" placeholder="Describe the evidence that supports this label (video timestamp, adjacent speaker context, etc.)"></textarea>
          <p class="rm-hint-text">Required for any named label. Helps future reviewers understand the decision.</p>
        </div>

        <div id="rm-decision-output" class="rm-decision-output" style="display:none;"></div>
        <div id="rm-apply-instructions" class="rm-instructions" style="display:none;">
          <b>Saved!</b> To apply this decision:<br>
          1. Copy the JSON above<br>
          2. Add it to <code>reviews/&lt;meeting&gt;-review-decisions.json</code> in the <code>decisions</code> array<br>
          3. Run: <code>python scripts/apply_review_decisions.py apr-14-2026</code><br>
          4. Run: <code>python scripts/publish_structured_meeting.py apr-14-2026</code>
        </div>

        <div class="rm-actions">
          <button type="button" id="rm-copy-decision" class="mini-btn" style="display:none;"><i class="fas fa-copy"></i> Copy JSON</button>
          <button type="button" id="rm-submit" class="mini-btn primary-btn" disabled><i class="fas fa-save"></i> Save decision</button>
          <button type="button" id="rm-cancel" class="mini-btn">Cancel</button>
        </div>
      </div>
    `;
  }

  // ---- Show review mode indicator ----
  function showReviewModeBanner() {
    const existing = document.getElementById('review-banner');
    if (existing) return;
    const banner = document.createElement('div');
    banner.id = 'review-banner';
    banner.className = 'review-banner';
    banner.innerHTML = '<i class="fas fa-edit"></i> Review mode active — unlabeled turns can be labeled | <a href="?" class="review-exit-link">Exit review mode</a>';
    document.querySelector('.container').prepend(banner);

    // Add pending count badge
    const pending = loadPending();
    if (pending.length > 0) {
      const badge = document.createElement('span');
      badge.className = 'review-pending-badge';
      badge.textContent = `${pending.length} pending decision${pending.length > 1 ? 's' : ''}`;
      banner.appendChild(badge);
    }
  }

  // ---- Init ----
  function init() {
    REVIEW_MODE = isReviewMode();
    if (!REVIEW_MODE) return;

    // Show banner
    showReviewModeBanner();

    // Load pending
    PENDING_DECISIONS = loadPending();

    // Inject label buttons once transcript is rendered
    // DOMContentLoaded already fired, so run now; use MutationObserver for safety
    if (document.getElementById('transcript') && document.getElementById('transcript').children.length > 0) {
      wireLabelButtons();
    } else {
      const observer = new MutationObserver(() => {
        const container = document.getElementById('transcript');
        if (container && container.children.length > 0) {
          wireLabelButtons();
          observer.disconnect();
        }
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