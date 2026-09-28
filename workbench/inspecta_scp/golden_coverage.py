"""Golden coverage disclosures are not tool-limit or rule-verification evidence."""
from pathlib import Path
from .storage import sha_file


def coverage_catalog(store):
    notes=[]
    for record in store.records('golden_coverage_note'):
        current=True
        for source in record['reference_files']:
            try:
                if sha_file(Path(source['path']))!=source['sha256']:current=False
            except OSError:current=False
        notes.append({**record,'reference_current':current,
            'scope_status':'RECORDED_COVERAGE_LIMIT' if current else 'STALE_RECHECK_REFERENCE',
            'verification_credit':0,'establishes_tool_limitation':False})
    candidates=store.records('candidate_rule')
    reviews=store.records('rule_review')
    pending=[c['id'] for c in candidates if not any(r.get('candidate_id')==c['id'] and r.get('status')=='TESTED' and not r.get('blockers') for r in reviews)]
    return {'notes':notes,'candidate_count':len(candidates),'candidates_without_completed_review':len(pending),
        'qualification_policy':'Accept only for the declared covered scope when all applicable checks and rule-validation evidence pass. Disclose excluded golden features separately; no full-PDF coverage claim.',
        'acceptance_from_coverage_notes':False,
        'remaining_blockers':['Independent rule-application/transfer attestation adapter is incomplete'] if pending else [],
        'scope':'Coverage notes and review inventory only; no publication or verification inferred'}
