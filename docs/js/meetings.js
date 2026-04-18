/* Populate the homepage meeting list from SEARCH_INDEX.meetings */

(function () {
  'use strict';

  function formatDate(dateStr) {
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
    } catch (_) {
      return dateStr;
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    if (typeof SEARCH_INDEX === 'undefined' || !SEARCH_INDEX || !Array.isArray(SEARCH_INDEX.meetings)) return;
    const container = document.getElementById('meetings');
    if (!container) return;

    container.innerHTML = '';

    // Sort newest first
    const meetings = SEARCH_INDEX.meetings.slice().sort(function (a, b) {
      if (a.meeting_date !== b.meeting_date) return a.meeting_date < b.meeting_date ? 1 : -1;
      return String(a.meeting_id || '').localeCompare(String(b.meeting_id || ''));
    });

    meetings.forEach(function (m) {
      const card = document.createElement('div');
      card.className = 'meeting-card';

      const date = document.createElement('div');
      date.className = 'meeting-date';
      date.innerHTML = '<i class="fas fa-calendar"></i> ' + formatDate(m.meeting_date);
      card.appendChild(date);

      const h3 = document.createElement('h3');
      h3.textContent = m.title || 'Meeting';
      card.appendChild(h3);

      const p = document.createElement('p');
      const secs = Array.isArray(m.sections) ? m.sections.slice(0, 3) : [];
      p.textContent = secs.length ? secs.join(', ') : (m.meeting_type ? (m.meeting_type + ' meeting') : '');
      card.appendChild(p);

      const a = document.createElement('a');
      a.href = m.transcript_url;
      a.innerHTML = '<i class="fas fa-file-alt"></i> View Transcript';
      card.appendChild(a);

      container.appendChild(card);
    });
  });
})();

