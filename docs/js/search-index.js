// Search index for Fairfax City Council transcripts
// Generated from transcript data

const SEARCH_INDEX = {
    meetings: [
        {
            meeting_id: "apr-14-2026",
            meeting_date: "2026-04-14",
            title: "City Council Meeting",
            meeting_type: "Regular Meeting",
            source_url: "https://fairfax.granicus.com/player/clip/4519",
            duration_seconds: 600,
            transcript_url: "transcripts/apr-14-2026.html"
        }
    ],
    
    segments: [
        {
            meeting_id: "apr-14-2026",
            meeting_date: "2026-04-14",
            title: "City Council Meeting",
            speaker: "Mayor Catherine Read",
            agenda_item: "Call to Order",
            start_seconds: 72,
            timestamp_label: "01:12",
            transcript_text: "Good evening. I would like to call the regular meeting of April 14th, 2026 to order.",
            snippet: "Good evening. I would like to call the regular meeting of April 14th, 2026 to order."
        },
        {
            meeting_id: "apr-14-2026",
            meeting_date: "2026-04-14",
            title: "City Council Meeting",
            speaker: "Mayor Catherine Read",
            agenda_item: "Call to Order",
            start_seconds: 77,
            timestamp_label: "01:17",
            transcript_text: "It's good to see the chamber full. We have a lot of things to celebrate tonight.",
            snippet: "It's good to see the chamber full. We have a lot of things to celebrate tonight."
        },
        {
            meeting_id: "apr-14-2026",
            meeting_date: "2026-04-14",
            title: "City Council Meeting",
            speaker: "Mayor Catherine Read",
            agenda_item: "Pledge of Allegiance",
            start_seconds: 81,
            timestamp_label: "01:21",
            transcript_text: "If you are able and so choose, please rise for the Pledge of Allegiance.",
            snippet: "If you are able and so choose, please rise for the Pledge of Allegiance."
        },
        {
            meeting_id: "apr-14-2026",
            meeting_date: "2026-04-14",
            title: "City Council Meeting",
            speaker: "Assembly",
            agenda_item: "Pledge of Allegiance",
            start_seconds: 85,
            timestamp_label: "01:25",
            transcript_text: "I pledge allegiance to the flag of the United States of America, and to the republic for which it stands, one nation, under God, indivisible, with liberty and justice for all.",
            snippet: "I pledge allegiance to the flag of the United States of America..."
        },
        {
            meeting_id: "apr-14-2026",
            meeting_date: "2026-04-14",
            title: "City Council Meeting",
            speaker: "Mayor Catherine Read",
            agenda_item: "National Library Week Proclamation",
            start_seconds: 102,
            timestamp_label: "01:42",
            transcript_text: "I will now ask Suzanne Levy, Eric Carson, and Alana Quarles with the City of Fairfax Library to come down for the proclamation acknowledging National Library Week.",
            snippet: "I will now ask Suzanne Levy, Eric Carson, and Alana Quarles with the City of Fairfax Library..."
        },
        {
            meeting_id: "apr-14-2026",
            meeting_date: "2026-04-14",
            title: "City Council Meeting",
            speaker: "Mayor Catherine Read",
            agenda_item: "National Library Week Proclamation",
            start_seconds: 133,
            timestamp_label: "02:13",
            transcript_text: "Whereas, libraries spark creativity, fuel imagination, and inspire lifelong learning, offering a space where individuals of all ages can find joy through exploration and discovery.",
            snippet: "Whereas, libraries spark creativity, fuel imagination, and inspire lifelong learning..."
        },
        {
            meeting_id: "apr-14-2026",
            meeting_date: "2026-04-14",
            title: "City Council Meeting",
            speaker: "Mayor Catherine Read",
            agenda_item: "National Library Week Proclamation",
            start_seconds: 148,
            timestamp_label: "02:28",
            transcript_text: "And whereas libraries serve as vibrant community hubs connecting people with knowledge, technology, and resources while fostering civic engagement, critical thinking, and cultural enrichment.",
            snippet: "And whereas libraries serve as vibrant community hubs connecting people with knowledge..."
        },
        {
            meeting_id: "apr-14-2026",
            meeting_date: "2026-04-14",
            title: "City Council Meeting",
            speaker: "Mayor Catherine Read",
            agenda_item: "National Library Week Proclamation",
            start_seconds: 159,
            timestamp_label: "02:39",
            transcript_text: "And whereas libraries provide free and equitable access to books, digital tools, and innovative programming, ensuring that all individuals, regardless of background, have the support they need to learn, connect, and thrive.",
            snippet: "And whereas libraries provide free and equitable access to books, digital tools..."
        }
    ],
    
    // Unique speakers for filter dropdown
    speakers: [
        "Mayor Catherine Read",
        "Assembly"
    ],
    
    // Agenda items for grouping
    agenda_items: [
        "Call to Order",
        "Pledge of Allegiance",
        "National Library Week Proclamation"
    ]
};

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SEARCH_INDEX;
}
