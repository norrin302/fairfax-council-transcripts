/* Transcript page renderer + interactions (static-site friendly) */

(function () {
  'use strict';

  // Page state (shareable via URL hash params)
  let ACTIVE_SPEAKER = '';
  let ACTIVE_SECTION_KEY = '';
  let CURRENT_T = 0;
  let MATCH_INDEX = -1;
  let MATCH_IDS = [];

  function formatTime(seconds) {
    const s = Math.max(0, Math.floor(Number(seconds) || 0));
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = s % 60;
    if (h > 0) return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
    return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
  }

  function makeVideoUrl(baseUrl, startSeconds) {
    if (!baseUrl) return '';
    try {
      const u = new URL(baseUrl);
      // Granicus supports deep-linking via entrytime (seconds) + autostart.
      u.searchParams.set('entrytime', String(Math.max(0, Math.floor(Number(startSeconds) || 0))));
      u.searchParams.set('autostart', '1');
      return u.toString();
    } catch (_) {
      return baseUrl;
    }
  }

  function parseHashParams() {
    const hash = window.location.hash || '';
    if (!hash.startsWith('#')) return new URLSearchParams();
    return new URLSearchParams(hash.slice(1));
  }

  function buildShareUrl(opts) {
    const base = new URL(window.location.href);
    base.hash = '';
    const params = new URLSearchParams();
    if (opts && opts.t != null) params.set('t', String(Math.max(0, Math.floor(Number(opts.t) || 0))));
    if (opts && opts.speaker) params.set('speaker', String(opts.speaker));
    if (opts && opts.section) params.set('section', String(opts.section));
    if (opts && opts.q) params.set('q', String(opts.q));
    base.hash = params.toString();
    return base.toString();
  }

  function sectionKeyForSeconds(seconds, sections) {
    if (!sections || !Array.isArray(sections) || sections.length === 0) return '';
    const s = Math.max(0, Math.floor(Number(seconds) || 0));
    let key = String(Math.max(0, Math.floor(Number(sections[0].start_seconds) || 0)));
    for (let i = 0; i < sections.length; i++) {
      const start = Math.max(0, Math.floor(Number(sections[i].start_seconds) || 0));
      if (s >= start) key = String(start);
      else break;
    }
    return key;
  }

  function sectionLabelForKey(key, sections) {
    if (!key) return '';
    const k = String(key);
    const secs = (sections && Array.isArray(sections)) ? sections : [];
    const hit = secs.find((s) => String(Math.max(0, Math.floor(Number(s.start_seconds) || 0))) === k);
    return hit ? String(hit.label || '').replace(/\s+/g, ' ').trim() : '';
  }

  function getHighlightsKey(meetingId) {
    return `highlights:${String(meetingId || '').trim()}`;
  }

  function highlightIdFor(meetingId, startSeconds) {
    return `${String(meetingId)}:${Math.max(0, Math.floor(Number(startSeconds) || 0))}`;
  }

  function loadHighlights(meetingId) {
    try {
      const raw = localStorage.getItem(getHighlightsKey(meetingId));
      if (!raw) return [];
      const arr = JSON.parse(raw);
      return Array.isArray(arr) ? arr : [];
    } catch (_) {
      return [];
    }
  }

  function saveHighlights(meetingId, highlights) {
    try {
      localStorage.setItem(getHighlightsKey(meetingId), JSON.stringify(highlights || []));
    } catch (_) {
      // ignore
    }
  }

  function speakerClassFor(speaker) {
    const s = String(speaker || '');
    return s.includes('Mayor') ? 'mayor'
      : s.includes('Council') ? 'council'
        : s.includes('Manager') ? 'staff'
          : 'public';
  }

  function showToast(message) {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 300);
    }, 1800);
  }

  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise((resolve, reject) => {
      try {
        const ta = document.createElement('textarea');
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        ta.remove();
        resolve();
      } catch (e) {
        reject(e);
      }
    });
  }

  function setHighlightedText(el, originalText, query) {
    if (!el) return;
    const text = String(originalText || '');
    const q = String(query || '').toLowerCase();
    if (!q) {
      el.textContent = text;
      return;
    }

    const lower = text.toLowerCase();
    el.textContent = '';

    let i = 0;
    while (i < text.length) {
      const idx = lower.indexOf(q, i);
      if (idx < 0) {
        el.appendChild(document.createTextNode(text.slice(i)));
        break;
      }
      if (idx > i) el.appendChild(document.createTextNode(text.slice(i, idx)));
      const mark = document.createElement('mark');
      mark.textContent = text.slice(idx, idx + q.length);
      el.appendChild(mark);
      i = idx + q.length;
    }
  }

  function buildCitation(turn, meeting) {
    const transcriptUrl = new URL(window.location.href);
    transcriptUrl.hash = `t=${Math.floor(Number(turn.start) || 0)}`;

    const videoUrl = makeVideoUrl(meeting.source_url, turn.start);
    const quote = String(turn.text || '').replace(/\s+/g, ' ').trim();
    const clippedQuote = quote.length > 400 ? quote.slice(0, 399).trimEnd() + '…' : quote;

    const dateLabel = meeting.display_date || meeting.meeting_date || '';
    return (
      `[${dateLabel} - ${meeting.title}]\n` +
      `Speaker: ${turn.speaker}\n` +
      `Time: ${formatTime(turn.start)}\n` +
      `Quote: "${clippedQuote}"\n` +
      `Transcript: ${transcriptUrl.toString()}\n` +
      (videoUrl ? `Video: ${videoUrl}\n` : '')
    ).trim();
  }

  function findTurnIndexAtOrAfter(turns, seconds) {
    const t = Math.max(0, Math.floor(Number(seconds) || 0));
    let lo = 0;
    let hi = turns.length - 1;
    let ans = 0;
    while (lo <= hi) {
      const mid = (lo + hi) >> 1;
      const start = Math.floor(Number(turns[mid].start) || 0);
      if (start >= t) {
        ans = mid;
        hi = mid - 1;
      } else {
        lo = mid + 1;
      }
    }
    // If everything is before t, jump to last element.
    if (turns.length && Math.floor(Number(turns[turns.length - 1].start) || 0) < t) return turns.length - 1;
    return ans;
  }

  function clearHighlights() {
    document.querySelectorAll('.turn-line.highlighted').forEach((el) => el.classList.remove('highlighted'));
  }

  function syncChipState() {
    const speakerChips = document.getElementById('speaker-chips');
    if (speakerChips) {
      speakerChips.querySelectorAll('.speaker-chip').forEach((b) => {
        const k = String(b.dataset.speaker || '').toLowerCase();
        if (k === String(ACTIVE_SPEAKER || '').toLowerCase()) b.classList.add('active');
        else if (!ACTIVE_SPEAKER && !k) b.classList.add('active');
        else b.classList.remove('active');
      });
    }

    const sectionChips = document.getElementById('section-chips');
    if (sectionChips) {
      sectionChips.querySelectorAll('.speaker-chip').forEach((b) => {
        const k = String(b.dataset.section || '');
        if (k === String(ACTIVE_SECTION_KEY || '')) b.classList.add('active');
        else if (!ACTIVE_SECTION_KEY && !k) b.classList.add('active');
        else b.classList.remove('active');
      });
    }
  }

  function highlightTurn(turnEl) {
    if (!turnEl) return;
    clearHighlights();
    turnEl.classList.add('highlighted');
    setTimeout(() => turnEl.classList.remove('highlighted'), 3500);
  }

  function handleDeepLink(turns) {
    const params = parseHashParams();

    const speaker = params.get('speaker');
    const section = params.get('section');
    const q = params.get('q');
    const t = params.get('t');

    if (speaker != null) ACTIVE_SPEAKER = String(speaker || '').toLowerCase();
    if (section != null) ACTIVE_SECTION_KEY = String(section || '').trim();
    if (q != null) {
      const input = document.getElementById('search-input');
      if (input) input.value = String(q || '');
    }

    syncChipState();
    applyTranscriptFilters();

    if (!t) return;
    const seconds = parseInt(t, 10);
    if (Number.isNaN(seconds)) return;

    CURRENT_T = seconds;

    const idx = findTurnIndexAtOrAfter(turns, seconds);
    const el = document.getElementById(`turn-${idx}`);
    if (!el) return;
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    highlightTurn(el);
  }

  function renderTranscript(turns, meeting) {
    const container = document.getElementById('transcript');
    if (!container) return;
    container.innerHTML = '';

    if (!turns || !Array.isArray(turns) || turns.length === 0) {
      container.innerHTML = '<p style="color: #e53e3e;">Error loading transcript data. Please refresh the page.</p>';
      return;
    }

    let currentSpeaker = null;
    let currentGroup = null;
    let currentGroupLines = null;

    turns.forEach((turn, idx) => {
      let speaker = String(turn.speaker || 'Unknown').trim();
      if (!speaker || speaker.toLowerCase() === 'speaker' || speaker.toLowerCase() === 'unknown') {
        speaker = 'Unknown Speaker';
      }
      const text = String(turn.text || '');
      const start = Number(turn.start) || 0;
      const sectionKey = sectionKeyForSeconds(start, meeting.sections);
      const sectionLabel = sectionLabelForKey(sectionKey, meeting.sections);

      if (speaker !== currentSpeaker) {
        currentSpeaker = speaker;
        const speakerClass = speakerClassFor(speaker);

        currentGroup = document.createElement('div');
        currentGroup.className = `speaker-group ${speakerClass}`;
        currentGroup.dataset.speaker = speaker.toLowerCase();

        const header = document.createElement('div');
        header.className = 'group-header';

        const nameSpan = document.createElement('span');
        nameSpan.className = 'speaker-name';
        nameSpan.textContent = speaker;
        header.appendChild(nameSpan);

        currentGroup.appendChild(header);

        currentGroupLines = document.createElement('div');
        currentGroupLines.className = 'group-lines';
        currentGroup.appendChild(currentGroupLines);

        container.appendChild(currentGroup);
      }

      const line = document.createElement('div');
      line.className = 'turn-line';
      line.id = `turn-${idx}`;
      line.dataset.index = String(idx);
      line.dataset.speaker = String(currentSpeaker || '').toLowerCase();
      line.dataset.text = text.toLowerCase();
      line.dataset.time = String(Math.floor(start));
      line.dataset.sectionKey = String(sectionKey || '');
      line.dataset.sectionLabel = String(sectionLabel || '');

      const meta = document.createElement('div');
      meta.className = 'turn-line-meta';

      const timeLink = document.createElement('a');
      timeLink.href = makeVideoUrl(meeting.source_url, start);
      timeLink.target = '_blank';
      timeLink.className = 'timestamp-link';
      timeLink.title = 'Open video at this time';
      timeLink.innerHTML = '<i class="fas fa-play-circle"></i> ' + formatTime(start);
      meta.appendChild(timeLink);

      const citeBtn = document.createElement('button');
      citeBtn.className = 'cite-btn';
      citeBtn.type = 'button';
      citeBtn.title = 'Copy citation (quote + timestamp + links)';
      citeBtn.innerHTML = '<i class="fas fa-quote-right"></i> Copy citation';
      citeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const citation = buildCitation({ ...turn, speaker: currentSpeaker }, meeting);
        copyText(citation)
          .then(() => showToast('Citation copied'))
          .catch(() => showToast('Copy failed'));
      });
      meta.appendChild(citeBtn);

      const saveBtn = document.createElement('button');
      saveBtn.className = 'save-btn';
      saveBtn.type = 'button';
      saveBtn.title = 'Save quote to Highlights';
      saveBtn.innerHTML = '<i class="fas fa-thumbtack"></i> Save';
      saveBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const meetingId = meeting.meeting_id || '';
        const id = highlightIdFor(meetingId, start);
        const items = loadHighlights(meetingId);
        const exists = items.some((x) => x && x.id === id);
        if (exists) {
          saveHighlights(meetingId, items.filter((x) => x && x.id !== id));
          showToast('Removed from Highlights');
        } else {
          items.push({
            id,
            meeting_id: meetingId,
            speaker: String(currentSpeaker || ''),
            start: Math.max(0, Math.floor(Number(start) || 0)),
            text: String(text || ''),
            created_at: new Date().toISOString()
          });
          saveHighlights(meetingId, items);
          showToast('Saved to Highlights');
        }
        renderHighlights(meeting);
      });
      meta.appendChild(saveBtn);

      line.appendChild(meta);

      const textDiv = document.createElement('div');
      textDiv.className = 'turn-text';
      textDiv.textContent = text;
      textDiv.dataset.originalText = text;
      line.appendChild(textDiv);

      // Clicking a line updates the URL hash (shareable deep link)
      line.addEventListener('click', () => {
        const sec = Math.floor(start);
        CURRENT_T = sec;
        const next = `t=${sec}`;
        if (window.location.hash !== `#${next}`) window.location.hash = next;
        highlightTurn(line);
      });

      if (currentGroupLines) currentGroupLines.appendChild(line);
    });
  }

  function applyTranscriptFilters() {
    const input = document.getElementById('search-input');
    const countEl = document.getElementById('search-count');
    const query = input ? String(input.value || '').toLowerCase().trim() : '';
    const speaker = String(ACTIVE_SPEAKER || '').toLowerCase().trim();
    const sectionKey = String(ACTIVE_SECTION_KEY || '').trim();

    const groups = document.querySelectorAll('.speaker-group');
    let visibleLines = 0;

    groups.forEach((group) => {
      let anyVisible = false;
      const lines = group.querySelectorAll('.turn-line');
      lines.forEach((line) => {
        const lineSpeaker = String(line.dataset.speaker || '');
        const lineSectionKey = String(line.dataset.sectionKey || '');
        const text = String(line.dataset.text || '');
        const textEl = line.querySelector('.turn-text');
        const originalText = textEl ? (textEl.dataset.originalText || textEl.textContent || '') : '';

        const speakerOk = !speaker || lineSpeaker === speaker;
        const sectionOk = !sectionKey || lineSectionKey === sectionKey;
        const queryOk = !query || text.includes(query);

        if (speakerOk && sectionOk && queryOk) {
          line.classList.remove('hidden');
          anyVisible = true;
          visibleLines++;
          if (textEl) {
            if (!query) {
              textEl.textContent = originalText;
            } else {
              setHighlightedText(textEl, originalText, query);
            }
          }
        } else {
          line.classList.add('hidden');
          if (textEl) textEl.textContent = originalText;
        }
      });

      if (anyVisible) group.classList.remove('hidden');
      else group.classList.add('hidden');
    });

    // Build match list for Next/Prev when query is set
    MATCH_IDS = [];
    MATCH_INDEX = -1;
    if (query) {
      document.querySelectorAll('.turn-line').forEach((line) => {
        if (!line.classList.contains('hidden')) MATCH_IDS.push(line.id);
      });
      if (MATCH_IDS.length) MATCH_INDEX = 0;
    }
    updateMatchUi();

    if (!countEl) return;
    if (!query && !speaker && !sectionKey) {
      countEl.textContent = '';
      return;
    }
    if (query) {
      countEl.textContent = `${visibleLines} match${visibleLines === 1 ? '' : 'es'} found`;
    } else {
      countEl.textContent = `${visibleLines} turn${visibleLines === 1 ? '' : 's'} shown`;
    }
  }

  function wireInPageSearch() {
    const input = document.getElementById('search-input');
    if (!input) return;
    input.addEventListener('input', applyTranscriptFilters);
  }

  function updateMatchUi() {
    const el = document.getElementById('match-nav');
    if (!el) return;
    const label = el.querySelector('#match-label');
    const prev = el.querySelector('#match-prev');
    const next = el.querySelector('#match-next');

    const total = MATCH_IDS.length;
    if (!total) {
      el.classList.add('hidden');
      if (label) label.textContent = '';
      return;
    }
    el.classList.remove('hidden');
    const idx = Math.max(0, MATCH_INDEX);
    if (label) label.textContent = `Match ${idx + 1} / ${total}`;
    if (prev) prev.disabled = total <= 1;
    if (next) next.disabled = total <= 1;
  }

  function jumpToMatch(delta) {
    if (!MATCH_IDS.length) return;
    MATCH_INDEX = (MATCH_INDEX + delta + MATCH_IDS.length) % MATCH_IDS.length;
    const id = MATCH_IDS[MATCH_INDEX];
    const el = document.getElementById(id);
    if (!el) return;
    const sec = parseInt(el.dataset.time || '0', 10);
    if (!Number.isNaN(sec)) {
      CURRENT_T = sec;
      window.location.hash = `t=${sec}`;
    }
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    highlightTurn(el);
    updateMatchUi();
  }

  function wireMatchNav() {
    const container = document.querySelector('.search-container');
    if (!container) return;

    let nav = document.getElementById('match-nav');
    if (!nav) {
      nav = document.createElement('div');
      nav.id = 'match-nav';
      nav.className = 'match-nav hidden';
      nav.innerHTML =
        '<button id="match-prev" type="button" class="mini-btn"><i class="fas fa-chevron-up"></i> Prev</button>' +
        '<span id="match-label" class="match-label"></span>' +
        '<button id="match-next" type="button" class="mini-btn">Next <i class="fas fa-chevron-down"></i></button>';
      container.appendChild(nav);
    }

    const prev = nav.querySelector('#match-prev');
    const next = nav.querySelector('#match-next');
    if (prev) prev.addEventListener('click', () => jumpToMatch(-1));
    if (next) next.addEventListener('click', () => jumpToMatch(1));
  }

  function renderSpeakerChips(turns) {
    const searchContainer = document.querySelector('.search-container');
    if (!searchContainer || !searchContainer.parentNode) return;

    let chips = document.getElementById('speaker-chips');
    if (!chips) {
      const block = document.createElement('div');
      block.className = 'official-links';
      block.id = 'speaker-chips-block';
      block.innerHTML = '<h3><i class="fas fa-users"></i> Speakers</h3><div id="speaker-chips" class="speaker-chips"></div>';
      searchContainer.parentNode.insertBefore(block, searchContainer);
      chips = block.querySelector('#speaker-chips');
    }
    if (!chips) return;

    // Count turns per speaker (as rendered)
    const counts = new Map();
    (turns || []).forEach((t) => {
      let sp = String(t.speaker || 'Unknown').trim();
      if (!sp || sp.toLowerCase() === 'speaker' || sp.toLowerCase() === 'unknown') sp = 'Unknown Speaker';
      counts.set(sp, (counts.get(sp) || 0) + 1);
    });

    const items = Array.from(counts.entries())
      .map(([name, count]) => ({ name, count, cls: speakerClassFor(name), key: String(name).toLowerCase() }))
      .sort((a, b) => (b.count - a.count) || a.name.localeCompare(b.name));

    chips.innerHTML = '';

    function addChip(label, key, cls, count) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = `speaker-chip ${cls || ''}`.trim();
      btn.dataset.speaker = key;
      btn.textContent = count != null ? `${label} (${count})` : label;
      btn.addEventListener('click', () => {
        ACTIVE_SPEAKER = key;
        chips.querySelectorAll('.speaker-chip').forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        applyTranscriptFilters();
      });
      chips.appendChild(btn);
      return btn;
    }

    const allBtn = addChip('All', '', 'council', null);
    allBtn.classList.add('active');

    items.forEach((it) => addChip(it.name, it.key, it.cls, it.count));
  }

  function renderSectionChips(meeting) {
    const after = document.getElementById('speaker-chips-block');
    if (!after || !after.parentNode) return;

    let block = document.getElementById('section-chips-block');
    if (!block) {
      block = document.createElement('div');
      block.className = 'official-links';
      block.id = 'section-chips-block';
      block.innerHTML = '<h3><i class="fas fa-list"></i> Sections</h3><div id="section-chips" class="speaker-chips"></div>';
      after.parentNode.insertBefore(block, after.nextSibling);
    }

    const chips = block.querySelector('#section-chips');
    if (!chips) return;

    const sections = (meeting && Array.isArray(meeting.sections)) ? meeting.sections : [];
    chips.innerHTML = '';

    function addChip(label, key) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'speaker-chip staff';
      btn.dataset.section = String(key || '');
      btn.textContent = label;
      btn.addEventListener('click', () => {
        ACTIVE_SECTION_KEY = String(key || '');
        chips.querySelectorAll('.speaker-chip').forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        applyTranscriptFilters();
      });
      chips.appendChild(btn);
      return btn;
    }

    const all = addChip('All', '');
    all.classList.add('active');

    sections.forEach((s) => {
      const sec = Math.max(0, Math.floor(Number(s.start_seconds) || 0));
      const label = `${formatTime(sec)} — ${String(s.label || '').replace(/\s+/g, ' ').trim()}`;
      addChip(label, String(sec));
    });
  }

  function downloadText(filename, content, mime) {
    const blob = new Blob([content], { type: mime || 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 250);
  }

  function exportVisible(meeting, format) {
    const query = ((document.getElementById('search-input') || {}).value || '');
    const lines = Array.from(document.querySelectorAll('.turn-line')).filter((el) => !el.classList.contains('hidden'));
    const rows = lines.map((el) => {
      const sec = parseInt(el.dataset.time || '0', 10) || 0;
      const speakerKey = String(el.dataset.speaker || '');
      const speaker = speakerKey ? speakerKey.split(' ').map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ') : '';
      const textEl = el.querySelector('.turn-text');
      const text = textEl ? (textEl.dataset.originalText || textEl.textContent || '') : '';
      const section = String(el.dataset.sectionLabel || '');
      const video = makeVideoUrl(meeting.source_url, sec);
      const transcript = buildShareUrl({
        t: sec,
        speaker: ACTIVE_SPEAKER || '',
        section: ACTIVE_SECTION_KEY || '',
        q: String(query || '').trim(),
      });
      return { speaker, time: formatTime(sec), section, text: String(text || '').replace(/\s+/g, ' ').trim(), video, transcript };
    });

    const base = meeting.meeting_id || 'meeting';
    const fname = `${base}_export.${format === 'csv' ? 'csv' : 'md'}`;

    if (format === 'csv') {
      const esc = (s) => {
        const t = String(s == null ? '' : s);
        if (/[\n\r",]/.test(t)) return '"' + t.replace(/"/g, '""') + '"';
        return t;
      };
      const header = ['speaker', 'time', 'section', 'text', 'video', 'transcript'];
      const body = rows.map((r) => header.map((k) => esc(r[k])).join(',')).join('\n');
      downloadText(fname, header.join(',') + '\n' + body + '\n', 'text/csv;charset=utf-8');
      return;
    }

    let md = `# ${meeting.title}\n\n`;
    md += `Date: ${meeting.display_date || meeting.meeting_date || ''}\n\n`;
    if (ACTIVE_SPEAKER) md += `Speaker filter: ${ACTIVE_SPEAKER}\n\n`;
    if (ACTIVE_SECTION_KEY) md += `Section filter: ${sectionLabelForKey(ACTIVE_SECTION_KEY, meeting.sections)}\n\n`;
    if (query) md += `Query: ${String(query).trim()}\n\n`;
    md += `Exported: ${new Date().toISOString()}\n\n---\n\n`;
    rows.forEach((r) => {
      md += `- **${r.speaker || 'Unknown'}** [${r.time}](${r.video})`;
      if (r.section) md += ` (${r.section})`;
      md += `: ${r.text}\n`;
    });
    md += '\n';
    downloadText(fname, md, 'text/markdown;charset=utf-8');
  }

  function renderHighlights(meeting) {
    const tools = document.getElementById('transcript-tools');
    if (!tools) return;
    let panel = document.getElementById('highlights-panel');
    if (!panel) {
      panel = document.createElement('div');
      panel.id = 'highlights-panel';
      panel.className = 'highlights-panel';
      tools.appendChild(panel);
    }

    const items = loadHighlights(meeting.meeting_id || '').slice().sort((a, b) => (a.start || 0) - (b.start || 0));
    if (!items.length) {
      panel.innerHTML = '<div class="highlights-empty">No highlights saved yet. Click <b>Save</b> next to any quote.</div>';
      return;
    }

    let html = '<h4><i class="fas fa-thumbtack"></i> Highlights</h4>';
    items.forEach((x) => {
      const t = Math.max(0, Math.floor(Number(x.start) || 0));
      const url = makeVideoUrl(meeting.source_url, t);
      const tx = String(x.text || '').replace(/\s+/g, ' ').trim();
      const clip = tx.length > 240 ? tx.slice(0, 239).trimEnd() + '…' : tx;
      html += `
        <div class="highlight-row" data-id="${String(x.id)}">
          <div class="highlight-meta">
            <span class="highlight-speaker">${String(x.speaker || '')}</span>
            <a class="timestamp-link" href="${url}" target="_blank" rel="noopener"><i class="fas fa-play-circle"></i> ${formatTime(t)}</a>
            <button class="mini-btn" data-action="copy" type="button"><i class="fas fa-copy"></i> Copy</button>
            <button class="mini-btn" data-action="remove" type="button"><i class="fas fa-trash"></i> Remove</button>
          </div>
          <div class="highlight-text">${clip.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</div>
        </div>
      `;
    });

    panel.innerHTML = html;

    panel.querySelectorAll('button[data-action]').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        const row = btn.closest('.highlight-row');
        if (!row) return;
        const id = row.getAttribute('data-id');
        const action = btn.getAttribute('data-action');
        const meetingId = meeting.meeting_id || '';
        const all = loadHighlights(meetingId);
        const item = all.find((x) => x && x.id === id);
        if (!item) return;

        if (action === 'remove') {
          saveHighlights(meetingId, all.filter((x) => x && x.id !== id));
          renderHighlights(meeting);
          showToast('Removed');
        } else if (action === 'copy') {
          const citation = buildCitation({ speaker: item.speaker, start: item.start, text: item.text }, meeting);
          copyText(citation).then(() => showToast('Copied')).catch(() => showToast('Copy failed'));
        }
      });
    });
  }

  function renderTools(meeting) {
    const anchor = document.getElementById('section-chips-block') || document.getElementById('speaker-chips-block');
    if (!anchor || !anchor.parentNode) return;

    let tools = document.getElementById('transcript-tools');
    if (!tools) {
      tools = document.createElement('div');
      tools.className = 'official-links';
      tools.id = 'transcript-tools';
      tools.innerHTML =
        '<h3><i class="fas fa-wand-magic-sparkles"></i> Transcript Tools</h3>' +
        '<div class="tools-row">' +
        '  <button id="btn-copy-share" type="button" class="mini-btn"><i class="fas fa-link"></i> Copy share link</button>' +
        '  <button id="btn-export-csv" type="button" class="mini-btn"><i class="fas fa-file-csv"></i> Export CSV</button>' +
        '  <button id="btn-export-md" type="button" class="mini-btn"><i class="fas fa-file-lines"></i> Export Markdown</button>' +
        '</div>';
      anchor.parentNode.insertBefore(tools, anchor.nextSibling);
    }

    const shareBtn = document.getElementById('btn-copy-share');
    if (shareBtn && !shareBtn.dataset.bound) {
      shareBtn.dataset.bound = '1';
      shareBtn.addEventListener('click', () => {
        const input = document.getElementById('search-input');
        const q = input ? String(input.value || '').trim() : '';
        const url = buildShareUrl({
          t: CURRENT_T || 0,
          speaker: ACTIVE_SPEAKER || '',
          section: ACTIVE_SECTION_KEY || '',
          q
        });
        copyText(url).then(() => showToast('Share link copied')).catch(() => showToast('Copy failed'));
      });
    }

    const csvBtn = document.getElementById('btn-export-csv');
    if (csvBtn && !csvBtn.dataset.bound) {
      csvBtn.dataset.bound = '1';
      csvBtn.addEventListener('click', () => exportVisible(meeting, 'csv'));
    }

    const mdBtn = document.getElementById('btn-export-md');
    if (mdBtn && !mdBtn.dataset.bound) {
      mdBtn.dataset.bound = '1';
      mdBtn.addEventListener('click', () => exportVisible(meeting, 'md'));
    }

    renderHighlights(meeting);
  }

  function wireBackToTop() {
    const btn = document.getElementById('back-to-top');
    if (!btn) return;
    window.addEventListener('scroll', function () {
      if (window.scrollY > 500) btn.classList.add('show');
      else btn.classList.remove('show');
    });
    btn.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  function wireSectionLinks() {
    document.querySelectorAll('[data-jump-seconds]').forEach((a) => {
      a.addEventListener('click', (e) => {
        e.preventDefault();
        const sec = parseInt(a.getAttribute('data-jump-seconds') || '0', 10);
        if (Number.isNaN(sec)) return;
        window.location.hash = `t=${sec}`;
      });
    });
  }

  function renderSectionLinks(meeting) {
    const container = document.getElementById('section-links');
    if (!container) return;

    const sections = (meeting && Array.isArray(meeting.sections)) ? meeting.sections : [];
    if (!sections.length) {
      container.innerHTML = '<span style="opacity:0.8; font-size:14px;">No sections available.</span>';
      return;
    }

    container.innerHTML = '';
    const ol = document.createElement('ol');
    ol.className = 'section-list';

    sections.forEach((s) => {
      const sec = Math.max(0, Math.floor(Number(s.start_seconds) || 0));
      const label = String(s.label || '').replace(/\s+/g, ' ').trim() || formatTime(sec);

      const li = document.createElement('li');
      const a = document.createElement('a');
      a.href = `#t=${sec}`;
      a.setAttribute('data-jump-seconds', String(sec));
      a.textContent = `${formatTime(sec)} — ${label}`;
      li.appendChild(a);
      ol.appendChild(li);
    });

    container.appendChild(ol);
  }

  function renderOfficialResources(meeting) {
    const container = document.getElementById('official-resources');
    if (!container) return;

    const video = meeting && meeting.source_url ? String(meeting.source_url) : '';
    const agenda = meeting && meeting.official_agenda_url ? String(meeting.official_agenda_url) : '';
    const minutes = meeting && meeting.official_minutes_url ? String(meeting.official_minutes_url) : '';
    const portal = meeting && meeting.official_meetings_portal_url ? String(meeting.official_meetings_portal_url) : '';

    const links = [];
    if (video) links.push(`<a href="${video}" target="_blank" rel="noopener"><i class="fas fa-video"></i> Watch Video (Granicus)</a>`);
    if (agenda) links.push(`<a href="${agenda}" target="_blank" rel="noopener"><i class="fas fa-file-alt"></i> Agenda</a>`);
    if (minutes) links.push(`<a href="${minutes}" target="_blank" rel="noopener"><i class="fas fa-file-signature"></i> Minutes</a>`);
    if (portal) links.push(`<a href="${portal}" target="_blank" rel="noopener"><i class="fas fa-file"></i> Meeting Portal</a>`);

    container.innerHTML =
      `<h3><i class="fas fa-external-link-alt"></i> Official Resources</h3>` +
      `<p>${links.join(' &bull; ')}</p>` +
      `<p style="margin: 10px 0 0 0; font-size: 14px; color: #4a5568;">` +
      `Video note: the city has reported Granicus streaming issues in Google Chrome. If playback fails, try Firefox, Safari, or Edge.` +
      `</p>`;
  }

  document.addEventListener('DOMContentLoaded', function () {
    // These are provided by docs/transcripts/<meeting_id>-data.js + inline page script
    const meeting = (typeof MEETING !== 'undefined' && MEETING) ? MEETING : {
      title: 'Meeting',
      meeting_date: '',
      display_date: '',
      source_url: ''
    };
    const turns = (typeof TRANSCRIPT_TURNS !== 'undefined') ? TRANSCRIPT_TURNS : [];

    renderTranscript(turns, meeting);
    renderOfficialResources(meeting);
    renderSectionLinks(meeting);
    renderSpeakerChips(turns);
    renderSectionChips(meeting);
    renderTools(meeting);
    wireInPageSearch();
    wireBackToTop();
    wireSectionLinks();

    wireMatchNav();

    applyTranscriptFilters();

    // Deep links from global search: #t=seconds
    handleDeepLink(turns);
    window.addEventListener('hashchange', () => handleDeepLink(turns));
  });
})();
