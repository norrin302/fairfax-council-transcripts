/* Transcript page renderer + interactions (static-site friendly) */

(function () {
  'use strict';

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

  function highlightTurn(turnEl) {
    if (!turnEl) return;
    clearHighlights();
    turnEl.classList.add('highlighted');
    setTimeout(() => turnEl.classList.remove('highlighted'), 3500);
  }

  function handleDeepLink(turns) {
    const hash = window.location.hash || '';
    if (!hash.startsWith('#')) return;
    const params = new URLSearchParams(hash.slice(1));
    const t = params.get('t');
    if (!t) return;
    const seconds = parseInt(t, 10);
    if (Number.isNaN(seconds)) return;

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

      line.appendChild(meta);

      const textDiv = document.createElement('div');
      textDiv.className = 'turn-text';
      textDiv.textContent = text;
      textDiv.dataset.originalText = text;
      line.appendChild(textDiv);

      // Clicking a line updates the URL hash (shareable deep link)
      line.addEventListener('click', () => {
        const sec = Math.floor(start);
        const next = `t=${sec}`;
        if (window.location.hash !== `#${next}`) window.location.hash = next;
        highlightTurn(line);
      });

      if (currentGroupLines) currentGroupLines.appendChild(line);
    });
  }

  let ACTIVE_SPEAKER = '';

  function applyTranscriptFilters() {
    const input = document.getElementById('search-input');
    const countEl = document.getElementById('search-count');
    const query = input ? String(input.value || '').toLowerCase().trim() : '';
    const speaker = String(ACTIVE_SPEAKER || '').toLowerCase().trim();

    const groups = document.querySelectorAll('.speaker-group');
    let visibleLines = 0;

    groups.forEach((group) => {
      let anyVisible = false;
      const lines = group.querySelectorAll('.turn-line');
      lines.forEach((line) => {
        const lineSpeaker = String(line.dataset.speaker || '');
        const text = String(line.dataset.text || '');
        const textEl = line.querySelector('.turn-text');
        const originalText = textEl ? (textEl.dataset.originalText || textEl.textContent || '') : '';

        const speakerOk = !speaker || lineSpeaker === speaker;
        const queryOk = !query || text.includes(query);

        if (speakerOk && queryOk) {
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

    if (!countEl) return;
    if (!query && !speaker) {
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
    wireInPageSearch();
    wireBackToTop();
    wireSectionLinks();

    applyTranscriptFilters();

    // Deep links from global search: #t=seconds
    handleDeepLink(turns);
    window.addEventListener('hashchange', () => handleDeepLink(turns));
  });
})();
