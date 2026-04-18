/**
 * Fairfax City Council Transcripts - Cross-Meeting Search
 * Provides full-text search across all meeting transcripts
 */

(function() {
    'use strict';

    // DOM elements
    let searchInput, searchBtn, meetingTypeFilter, speakerFilter, sectionFilter, dateFrom, dateTo, resultsContainer;

    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', init);

    function init() {
        searchInput = document.getElementById('global-search');
        searchBtn = document.getElementById('search-btn');
        meetingTypeFilter = document.getElementById('filter-meeting-type');
        speakerFilter = document.getElementById('filter-speaker');
        sectionFilter = document.getElementById('filter-section');
        dateFrom = document.getElementById('filter-date-from');
        dateTo = document.getElementById('filter-date-to');
        resultsContainer = document.getElementById('search-results');

        if (!searchInput || !resultsContainer) return;

        // Populate filters
        populateMeetingTypeFilter();
        populateSpeakerFilter();
        populateSectionFilter();

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
        if (meetingTypeFilter) meetingTypeFilter.addEventListener('change', performSearch);
        if (speakerFilter) speakerFilter.addEventListener('change', performSearch);
        if (sectionFilter) sectionFilter.addEventListener('change', performSearch);
        if (dateFrom) dateFrom.addEventListener('change', performSearch);
        if (dateTo) dateTo.addEventListener('change', performSearch);
    }

    function populateMeetingTypeFilter() {
        if (!meetingTypeFilter || !SEARCH_INDEX || !SEARCH_INDEX.meetings) return;

        const types = Array.from(new Set(SEARCH_INDEX.meetings.map(function(m) { return m.meeting_type; }).filter(Boolean))).sort();
        types.forEach(function(t) {
            const option = document.createElement('option');
            option.value = t;
            option.textContent = t.charAt(0).toUpperCase() + t.slice(1);
            meetingTypeFilter.appendChild(option);
        });
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

    function populateSectionFilter() {
        if (!sectionFilter || !SEARCH_INDEX || !SEARCH_INDEX.segments) return;

        const sections = Array.from(new Set(SEARCH_INDEX.segments.map(function(s) { return s.section; }).filter(Boolean)))
            .sort(function(a, b) { return a.localeCompare(b); });

        sections.forEach(function(section) {
            const option = document.createElement('option');
            option.value = section;
            option.textContent = section;
            sectionFilter.appendChild(option);
        });
    }

    function performSearch() {
        const query = searchInput.value.trim().toLowerCase();
        const meetingType = meetingTypeFilter ? meetingTypeFilter.value : '';
        const speaker = speakerFilter ? speakerFilter.value : '';
        const section = sectionFilter ? sectionFilter.value : '';
        const fromDate = dateFrom ? dateFrom.value : '';
        const toDate = dateTo ? dateTo.value : '';

        // Clear results if query is empty
        if (query.length < 2) {
            resultsContainer.innerHTML = '';
            resultsContainer.style.display = 'none';
            return;
        }

        // Search segments
        const results = searchSegments(query, meetingType, speaker, section, fromDate, toDate);

        // Display results
        displayResults(results, query);
    }

    function normalizeText(s) {
        return String(s || '')
            .toLowerCase()
            .replace(/[^a-z0-9\s]/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();
    }

    function computeScore(segment, query) {
        const text = normalizeText(segment.transcript_text);
        const q = normalizeText(query);

        if (!q) return 0;
        let score = 0;

        // Exact phrase boost
        const pos = text.indexOf(q);
        if (pos !== -1) {
            score += 500;
            score += Math.max(0, 200 - Math.min(200, pos));
        }

        // Token overlap
        const tokens = q.split(' ').filter(Boolean);
        let hit = 0;
        tokens.forEach(function(tok) {
            if (tok.length < 2) return;
            if (text.includes(tok)) hit += 1;
        });
        score += hit * 40;

        return score;
    }

    function searchSegments(query, meetingType, speaker, section, fromDate, toDate) {
        if (!SEARCH_INDEX || !SEARCH_INDEX.segments) return [];

        const filtered = SEARCH_INDEX.segments.filter(function(segment) {
            // Text match
            const textMatch = segment.transcript_text.toLowerCase().includes(query) ||
                              segment.snippet.toLowerCase().includes(query);

            if (!textMatch) return false;

            // Meeting type filter
            if (meetingType) {
                const meeting = SEARCH_INDEX.meetings.find(function(m) { return m.meeting_id === segment.meeting_id; });
                if (!meeting || meeting.meeting_type !== meetingType) return false;
            }

            // Speaker filter
            if (speaker && segment.speaker !== speaker) return false;

            // Section filter
            if (section && (segment.section || '') !== section) return false;

            // Date range filter
            if (fromDate && segment.meeting_date < fromDate) return false;
            if (toDate && segment.meeting_date > toDate) return false;

            return true;
        });

        // Sort: relevance first, then newest meeting, then chronological within meeting
        filtered.sort(function(a, b) {
            const sa = computeScore(a, query);
            const sb = computeScore(b, query);
            if (sa !== sb) return sb - sa;
            if (a.meeting_date !== b.meeting_date) return a.meeting_date < b.meeting_date ? 1 : -1;
            return (a.start_seconds || 0) - (b.start_seconds || 0);
        });

        return filtered;
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

            group.segments.slice(0, 200).forEach(function(segment) {
                let videoUrl = '';
                if (meeting.source_url) {
                    try {
                        const u = new URL(meeting.source_url);
                        u.searchParams.set('start', String(Math.max(0, Math.floor(segment.start_seconds || 0))));
                        videoUrl = u.toString();
                    } catch (e) {
                        videoUrl = meeting.source_url;
                    }
                }
                html += '<div class="result-item" data-meeting="' + segment.meeting_id + '" data-time="' + segment.start_seconds + '">';
                html += '<div class="result-meta">';
                html += '<span class="result-speaker"><i class="fas fa-user"></i> ' + escapeHtml(segment.speaker) + '</span>';
                html += '<span class="result-timestamp"><i class="fas fa-clock"></i> ' + segment.timestamp_label + '</span>';
                html += '<span class="result-agenda">' + escapeHtml(segment.section || '') + '</span>';
                html += '</div>';
                html += '<div class="result-snippet">' + highlightText(segment.snippet, query) + '</div>';
                html += '<div class="result-actions">';
                html += '<a href="' + meeting.transcript_url + '#t=' + segment.start_seconds + '" class="btn-view">';
                html += '<i class="fas fa-file-alt"></i> View in Transcript</a>';
                if (videoUrl) {
                    html += '<a href="' + videoUrl + '" target="_blank" rel="noopener" class="btn-view">';
                    html += '<i class="fas fa-video"></i> Open Video</a>';
                }
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
        // Build URLs relative to the current page (works on GitHub Pages project sites)
        const transcriptUrl = new URL(meeting.transcript_url, window.location.href);
        transcriptUrl.hash = 't=' + segment.start_seconds;

        let videoUrl = '';
        if (meeting.source_url) {
            try {
                const u = new URL(meeting.source_url);
                u.searchParams.set('start', String(Math.max(0, Math.floor(segment.start_seconds || 0))));
                videoUrl = u.toString();
            } catch (e) {
                videoUrl = meeting.source_url;
            }
        }

        const quote = String(segment.transcript_text || '').replace(/\s+/g, ' ').trim();
        const clippedQuote = quote.length > 400 ? quote.slice(0, 399).trimEnd() + '…' : quote;

        return `[${formatDate(meeting.meeting_date)} - ${meeting.title}]\n` +
               `Speaker: ${segment.speaker}\n` +
               `Time: ${segment.timestamp_label}\n` +
               `Quote: "${clippedQuote}"\n` +
               `Transcript: ${transcriptUrl.toString()}\n` +
               (videoUrl ? `Video: ${videoUrl}` : '');
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
