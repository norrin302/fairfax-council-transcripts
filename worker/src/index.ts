export interface Env {
  GH_PAT: string;
}

const GH_PAT = (env: Env) => env.GH_PAT;
const REPO = 'norrin302/fairfax-council-transcripts';
const BRANCH = 'main';
const ACTOR = 'fairfax-apply-worker';

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method !== 'POST') {
      return json({ error: 'Method not allowed' }, 405);
    }

    const token = GH_PAT(env);
    if (!token) {
      return json({ error: 'GH_PAT not configured' }, 500);
    }

    let payload: { meeting_id: string; decisions: any[] };
    try {
      payload = await request.json();
    } catch {
      return json({ error: 'Invalid JSON' }, 400);
    }

    const { meeting_id, decisions } = payload;
    if (!meeting_id || !Array.isArray(decisions) || decisions.length === 0) {
      return json({ error: 'Missing meeting_id or decisions' }, 400);
    }

    const ghHeaders = {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/vnd.github.v3+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'Content-Type': 'application/json'
    };

    // Step 1: Fetch the current structured transcript
    const structUrl = `https://api.github.com/repos/${REPO}/contents/transcripts_structured/${meeting_id}.json`;
    const structResp = await fetch(structUrl, { headers: ghHeaders });
    if (!structResp.ok) {
      return json({ error: `Could not fetch structured transcript: ${structResp.status}` }, structResp.status);
    }
    const structMeta = await structResp.json() as { sha: string; content: string };

    let data: any;
    try {
      data = JSON.parse(atob(structMeta.content));
    } catch {
      return json({ error: 'Invalid JSON in structured transcript' }, 500);
    }

    // Step 2: Apply decisions to turns
    const turnsById: Record<string, any> = {};
    for (const turn of data.turns || []) {
      turnsById[String(turn.turn_id)] = turn;
    }

    let applied = 0;
    let skipped = 0;

    for (const decision of decisions) {
      const turn = turnsById[String(decision.turn_id)];
      if (!turn) { skipped++; continue; }

      const action = decision.reviewer_action;
      const speakerName = String(decision.speaker_name || '');
      const speakerType = String(decision.speaker_type || '');

      if (action === 'suppress_turn') {
        turn.speaker = 'SUPPRESSED';
        turn.speaker_source = 'suppressed';
        turn.speaker_source_detail = decision.evidence_note || 'suppressed:review';
        applied++;
      } else if (action === 'mark_public_comment') {
        turn.speaker = speakerName || 'Public Comment Speaker';
        turn.speaker_source = 'approved';
        turn.speaker_source_detail = 'reviewed:mark_public_comment';
        applied++;
      } else if (action === 'approve_named_official') {
        turn.speaker = speakerName;
        turn.speaker_source = 'approved';
        turn.speaker_source_detail = `reviewed:approve_named_official|${decision.evidence_note || ''}`;
        applied++;
      } else if (action === 'keep_unknown') {
        turn.speaker_source_detail = (turn.speaker_source_detail || '').replace(/\|?reviewed:keep_unknown$/, '') + '|reviewed:keep_unknown';
        applied++;
      }
    }

    if (data.meeting) {
      data.meeting.reviewed = true;
      data.meeting.reviewed_at = new Date().toISOString();
      data.meeting.review_decisions_count = (data.meeting.review_decisions_count || 0) + applied;
    }

    const newContent = btoa(unescape(encodeURIComponent(JSON.stringify(data, null, 2))));

    // Step 3: Commit updated structured JSON to main
    const commitMsg = `apply_review_decisions: ${meeting_id} — ${applied} decision(s) applied`;
    const commitResp = await fetch(`https://api.github.com/repos/${REPO}/contents/transcripts_structured/${meeting_id}.json`, {
      method: 'PUT',
      headers: ghHeaders,
      body: JSON.stringify({ message: commitMsg, sha: structMeta.sha, content: newContent, branch: BRANCH })
    });

    if (!commitResp.ok) {
      const errText = await commitResp.text();
      return json({ error: `Failed to commit: ${errText}` }, commitResp.status);
    }

    // Step 4: Trigger the publish workflow via repository_dispatch
    // (This triggers the publish workflow defined in .github/workflows/publish-meeting.yml)
    const dispatchResp = await fetch(`https://api.github.com/repos/${REPO}/dispatches`, {
      method: 'POST',
      headers: ghHeaders,
      body: JSON.stringify({
        event: 'repository_dispatch',
        description: 'Apply review decisions and republish',
        client_payload: { meeting_id, applied, skipped }
      })
    });

    if (!dispatchResp.ok && dispatchResp.status !== 204) {
      // Non-fatal: decisions were applied, but publish might not trigger
      console.error('Dispatch warning:', await dispatchResp.text());
    }

    return json({
      ok: true,
      meeting_id,
      applied,
      skipped,
      message: `✅ Applied ${applied} decision(s). Pages rebuilding — refresh in ~2 min.`
    });
  }
};

function json(body: any, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' }
  });
}

interface Env {
  GH_PAT: string;
}