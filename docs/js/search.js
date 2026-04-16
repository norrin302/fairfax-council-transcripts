/**
 * Fairfax City Council Transcripts - Cross-Meeting Search
 * Provides full-text search across all meeting transcripts
 */

(function() {
    'use strict';

    // DOM elements
    let searchInput, searchBtn, speakerFilter, dateFrom, dateTo, resultsContainer;

    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', init);

    function init() {
        searchInput = document.getElementById('global-search');
        searchBtn = document.getElementById('search-btn');
        speakerFilter = document.getElementById('filter-speaker');
        dateFrom = document.getElementById('filter-date-from');
        dateTo = document.getElementById('filter-date-to');
        resultsContainer = document.getElementById('search-results');

        if (!searchInput || !resultsContainer) return;

        // Populate speaker filter
        populateSpeakerFilter();

        // Event listeners
        searchBtn.addEventListener('click', performSearch);
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') performSearch();
        });

        // Real-time search on input (debounced)
        let debounceTimer;
        searchInput.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(performSearch, 300);
        });

        // Filter changes trigger search
        if (speakerFilter) speakerFilter.addEventListener('change', performSearch);
        if (dateFrom) dateFrom.addEventListener('change', performSearch);
        if (dateTo) dateTo.addEventListener('change', performSearch);
    }

    function populateSpeakerFilter() {
        if (!speakerFilter || !SEARCH_INDEX || !SEARCH_INDEX.speakers) return;

        SEARCH_INDEX.speakers.forEach(function(speaker) {
            const option = document.createElement('option');
            option.value = speaker;
            option.textContent = speaker;
            speakerFilter.appendChild(option);
        });
    }

    function performSearch() {
        const query = searchInput.value.trim().toLowerCase();
        const speaker = speakerFilter ? speakerFilter.value : '';
        const fromDate = dateFrom ? dateFrom.value : '';
        const toDate = dateTo ? dateTo.value : '';

        // Clear results if query is empty
        if (query.length < 2) {
            resultsContainer.innerHTML = '';
            resultsContainer.style.display = 'none';
            return;
        }

        // Search segments
        const results = searchSegments(query, speaker, fromDate, toDate);

        // Display results
        displayResults(results, query);
    }

    function searchSegments(query, speaker, fromDate, toDate) {
        if (!SEARCH_INDEX || !SEARCH_INDEX.segments) return [];

        return SEARCH_INDEX.segments.filter(function(segment) {
            // Text match
            const textMatch = segment.transcript_text.toLowerCase().includes(query) ||
                              segment.snippet.toLowerCase().includes(query);

            if (!textMatch) return false;

            // Speaker filter
            if (speaker && segment.speaker !== speaker) return false;

            // Date range filter
            if (fromDate && segment.meeting_date < fromDate) return false;
            if (toDate && segment.meeting_date > toDate) return false;

            return true;
        });
    }

    function displayResults(results, query) {
        resultsContainer.style.display = 'block';

        if (results.length === 0) {
            resultsContainer.innerHTML = '<div class="no-results">No results found for "' + escapeHtml(query) + '"</div>';
            return;
        }

        // Group results by meeting
        const grouped = {};
        results.forEach(function(result) {
            if (!grouped[result.meeting_id]) {
                grouped[result.meeting_id] = {
                    meeting: SEARCH_INDEX.meetings.find(function(m) { return m.meeting_id === result.meeting_id; }),
                    segments: []
                };
            }
            grouped[result.meeting_id].segments.push(result);
        });

        // Build HTML
        let html = '<div class="results-count">' + results.length + ' result' + (results.length !== 1 ? 's' : '') + ' found</div>';
        html += '<div class="results-list">';

        Object.keys(grouped).forEach(function(meetingId) {
            const group = grouped[meetingId];
            const meeting = group.meeting;

            html += '<div class="meeting-group">';
            html += '<div class="meeting-header">';
            html += '<h3>' + escapeHtml(meeting.title) + '</h3>';
            html += '<span class="meeting-date">' + formatDate(meeting.meeting_date) + '</span>';
            html += '</div>';

            group.segments.forEach(function(segment) {
                html += '<div class="result-item" data-meeting="' + segment.meeting_id + '" data-time="' + segment.start_seconds + '">';
                html += '<div class="result-meta">';
                html += '<span class="result-speaker"><i class="fas fa-user"></i> ' + escapeHtml(segment.speaker) + '</span>';
                html += '<span class="result-timestamp"><i class="fas fa-clock"></i> ' + segment.timestamp_label + '</span>';
                html += '<span class="result-agenda">' + escapeHtml(segment.agenda_item) + '</span>';
                html += '</div>';
                html += '<div class="result-snippet">' + highlightText(segment.snippet, query) + '</div>';
                html += '<div class="result-actions">';
                html += '<a href="' + meeting.transcript_url + '#t=' + segment.start_seconds + '" class="btn-view">';
                html += '<i class="fas fa-file-alt"></i> View in Transcript</a>';
                html += '<button class="btn-cite" onclick="copyCitation(\'' + segment.meeting_id + '\', ' + segment.start_seconds + ')">';
                html += '<i class="fas fa-quote-right"></i> Copy Citation</button>';
                html += '</div>';
                html += '</div>';
            });

            html += '</div>';
        });

        html += '</div>';
        resultsContainer.innerHTML = html;

        // Add click handlers for results
        document.querySelectorAll('.result-item').forEach(function(item) {
            item.addEventListener('click', function(e) {
                if (e.target.closest('.btn-cite') || e.target.closest('.btn-view')) return;
                const meetingId = this.dataset.meeting;
                const time = this.dataset.time;
                const meeting = SEARCH_INDEX.meetings.find(function(m) { return m.meeting_id === meetingId; });
                if (meeting) {
                    window.location.href = meeting.transcript_url + '#t=' + time;
                }
            });
        });
    }

    function highlightText(text, query) {
        const regex = new RegExp('(' + escapeRegex(query) + ')', 'gi');
        return escapeHtml(text).replace(regex, '<mark>$1</mark>');
    }

    function formatDate(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function escapeRegex(str) {
        return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    // Global function for citation copy
    window.copyCitation = function(meetingId, startSeconds) {
        const segment = SEARCH_INDEX.segments.find(function(s) {
            return s.meeting_id === meetingId && s.start_seconds === startSeconds;
        });
        const meeting = SEARCH_INDEX.meetings.find(function(m) { return m.meeting_id === meetingId; });

        if (!segment || !meeting) return;

        const citation = buildCitation(segment, meeting);
        navigator.clipboard.writeText(citation).then(function() {
            showToast('Citation copied to clipboard!');
        }).catch(function() {
            // Fallback for older browsers
            const textarea = document.createElement('textarea');
            textarea.value = citation;
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            showToast('Citation copied to clipboard!');
        });
    };

    function buildCitation(segment, meeting) {
        const url = window.location.origin + '/' + meeting.transcript_url + '#t=' + segment.start_seconds;
        return `[${formatDate(meeting.meeting_date)} - ${meeting.title}]\n` +
               `Speaker: ${segment.speaker}\n` +
               `Time: ${segment.timestamp_label}\n` +
               `Quote: "${segment.transcript_text}"\n` +
               `Source: ${url}`;
    }

    function showToast(message) {
        // Remove existing toast
        const existing = document.querySelector('.toast');
        if (existing) existing.remove();

        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(function() { toast.classList.add('show'); }, 10);
        setTimeout(function() {
            toast.classList.remove('show');
            setTimeout(function() { toast.remove(); }, 300);
        }, 2000);
    }

    // Page-local search for transcript pages
    window.searchTranscript = function() {
        const searchInput = document.getElementById('transcript-search');
        if (!searchInput) return;

        const query = searchInput.value.toLowerCase();
        const segments = document.querySelectorAll('.transcript-segment');
        let firstMatch = true;

        segments.forEach(function(seg) {
            const textEl = seg.querySelector('.text');
            if (!textEl) return;

            const text = textEl.textContent.toLowerCase();
            if (query.length > 2 && text.includes(query)) {
                seg.style.backgroundColor = '#fff3cd';
                if (firstMatch) {
                    seg.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    firstMatch = false;
                }
            } else {
                seg.style.backgroundColor = '';
            }
        });
    };

    // Handle deep-linking to timestamps
    window.addEventListener('load', function() {
        const hash = window.location.hash;
        if (hash && hash.startsWith('#t=')) {
            const seconds = parseInt(hash.substring(3));
            const segment = document.querySelector('[data-time="' + seconds + '"]');
            if (segment) {
                segment.classList.add('highlight');
                segment.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    });

})();
