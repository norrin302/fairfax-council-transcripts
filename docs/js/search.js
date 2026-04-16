// Fairfax Council Transcripts - Full Text Search
function searchTranscript() {
    const query = document.getElementById('transcript-search').value.toLowerCase();
    const segments = document.querySelectorAll('.transcript-segment');
    
    segments.forEach(seg => {
        const text = seg.querySelector('.text').textContent.toLowerCase();
        if (query && text.includes(query)) {
            seg.style.backgroundColor = '#fff3cd';
            seg.scrollIntoView({ behavior: 'smooth', block: 'center' });
        } else {
            seg.style.backgroundColor = '';
        }
    });
}

// Speaker identification colors
const speakerColors = {
    'Mayor': '#1a365d',
    'Chief Pedroso': '#2b6cb0', 
    'Director Hartley': '#38a169',
    'Council Member': '#805ad5',
    'City Manager': '#dd6b20'
};

function highlightSpeaker(speakerName) {
    // Highlight segments by speaker
}
