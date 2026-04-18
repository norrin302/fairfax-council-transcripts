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
      u.searchParams.set('start', String(Math.max(0, Math.floor(Number(startSeconds) || 0))));
      return u.toString();
    } catch (_) {
      return baseUrl;
    }
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
    document.querySelectorAll('.speaker-turn.highlighted').forEach((el) => el.classList.remove('highlighted'));
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

    turns.forEach((turn, idx) => {
      const speaker = String(turn.speaker || 'Unknown');
      const text = String(turn.text || '');
      const start = Number(turn.start) || 0;

      const speakerClass = speaker.includes('Mayor') ? 'mayor'
        : speaker.includes('Council') ? 'council'
          : speaker.includes('Manager') ? 'staff'
            : 'public';

      const div = document.createElement('div');
      div.className = `speaker-turn ${speakerClass}`;
      div.id = `turn-${idx}`;
      div.dataset.index = String(idx);
      div.dataset.speaker = speaker.toLowerCase();
      div.dataset.text = text.toLowerCase();
      div.dataset.time = String(Math.floor(start));

      const header = document.createElement('div');
      header.className = 'turn-header';

      const nameSpan = document.createElement('span');
      nameSpan.className = 'speaker-name';
      nameSpan.textContent = speaker;
      header.appendChild(nameSpan);

      const timeLink = document.createElement('a');
      timeLink.href = makeVideoUrl(meeting.source_url, start);
      timeLink.target = '_blank';
      timeLink.className = 'timestamp-link';
      timeLink.title = 'Open video at this time';
      timeLink.innerHTML = '<i class="fas fa-play-circle"></i> ' + formatTime(start);
      header.appendChild(timeLink);

      const citeBtn = document.createElement('button');
      citeBtn.className = 'cite-btn';
      citeBtn.type = 'button';
      citeBtn.title = 'Copy citation (quote + timestamp + links)';
      citeBtn.innerHTML = '<i class="fas fa-quote-right"></i> Copy citation';
      citeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const citation = buildCitation(turn, meeting);
        copyText(citation)
          .then(() => showToast('Citation copied'))
          .catch(() => showToast('Copy failed'));
      });
      header.appendChild(citeBtn);

      div.appendChild(header);

      const textDiv = document.createElement('div');
      textDiv.className = 'turn-text';
      textDiv.textContent = text;
      textDiv.dataset.originalText = text;
      div.appendChild(textDiv);

      // Clicking a turn updates the URL hash (shareable deep link)
      div.addEventListener('click', () => {
        const sec = Math.floor(start);
        const next = `t=${sec}`;
        if (window.location.hash !== `#${next}`) window.location.hash = next;
        highlightTurn(div);
      });

      container.appendChild(div);
    });
  }

  function wireInPageSearch() {
    const input = document.getElementById('search-input');
    const countEl = document.getElementById('search-count');
    if (!input) return;

    input.addEventListener('input', function (e) {
      const query = String(e.target.value || '').toLowerCase().trim();
      const turns = document.querySelectorAll('.speaker-turn');
      let matchCount = 0;

      turns.forEach((turn) => {
        const text = String(turn.dataset.text || '');
        const textEl = turn.querySelector('.turn-text');
        if (!textEl) return;

        const originalText = textEl.dataset.originalText || textEl.textContent;

        if (query === '') {
          turn.classList.remove('hidden');
          textEl.textContent = originalText;
        } else if (text.includes(query)) {
          turn.classList.remove('hidden');
          matchCount++;
          const regex = new RegExp('(' + query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi');
          textEl.innerHTML = String(originalText).replace(regex, '<mark>$1</mark>');
        } else {
          turn.classList.add('hidden');
        }
      });

      if (countEl) countEl.textContent = query ? `${matchCount} match${matchCount === 1 ? '' : 'es'} found` : '';
    });
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
    sections.forEach((s) => {
      const sec = Math.max(0, Math.floor(Number(s.start_seconds) || 0));
      let label = String(s.label || '').replace(/\s+/g, ' ').trim() || formatTime(sec);
      if (label.length > 80) label = label.slice(0, 79).trimEnd() + '…';

      const a = document.createElement('a');
      a.href = `#t=${sec}`;
      a.setAttribute('data-jump-seconds', String(sec));
      a.textContent = label;
      container.appendChild(a);
    });
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
    renderSectionLinks(meeting);
    wireInPageSearch();
    wireBackToTop();
    wireSectionLinks();

    // Deep links from global search: #t=seconds
    handleDeepLink(turns);
    window.addEventListener('hashchange', () => handleDeepLink(turns));
  });
})();
