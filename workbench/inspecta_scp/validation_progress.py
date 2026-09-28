"""Disclose what was checked and track transfer separately from model acceptance."""
from pathlib import Path
from .storage import sha_file
from .behavior_acceptance import BehaviorAcceptance


def validation_progress(controller):
    store=controller.store
    reviews=[BehaviorAcceptance(controller).inspect(r['id']) for r in store.records('behavior_acceptance_review')]
    accepted={r['result_id']:r for r in reviews if r['status']=='ACCEPTED_GOLDEN_SCOPE'}
    tasks={t['id']:t for t in store.records('development_task')}
    results=store.records('development_result');rule_reviews=store.records('rule_review')
    rows=[]
    for candidate in store.records('candidate_rule'):
        attempts=[r for r in results if candidate['id'] in tasks.get(r['task_id'],{}).get('candidate_ids',[])]
        scopes=[]
        for result in attempts:
            if result['id'] not in accepted:continue
            task=tasks[result['task_id']]
            scopes.append({'example':task['target_file'],'golden_sha256':task['golden_sha256'],
                'acceptance_review_id':accepted[result['id']]['id'],
                'excluded_requirements':accepted[result['id']]['excluded_requirements']})
        # A rule-library transfer review must actually pass; tool-fixture proofs
        # and human model acceptance do not establish transfer by themselves.
        passed=[r for r in rule_reviews if r.get('candidate_id')==candidate['id'] and r.get('status')=='TESTED' and not r.get('blockers')
                and any(x.get('generated_run_id')==r.get('supporting_run') and x['id'] in accepted for x in attempts)]
        status='ACCEPTED_AND_TRANSFERRED' if scopes and passed else ('ACCEPTED_CURRENT_SCOPE_TRANSFER_IN_PROGRESS' if scopes else ('TRANSFER_IN_PROGRESS' if attempts else 'TRANSFER_NOT_STARTED'))
        rows.append({'candidate_id':candidate['id'],'rule_id':candidate['record']['id'],'status':status,
            'attempted_examples':sorted({tasks[r['task_id']]['target_file'] for r in attempts}),
            'accepted_golden_scopes':scopes,'transfer_review_ids':[r['id'] for r in passed],
            'scope_expansion':'Only named examples with current acceptance evidence; exclusions remain attached. No universal coverage claim.'})
    proofs=[]
    for note in store.records('proof_execution_note'):
        try:current=sha_file(Path(note['report_path']))==note['report_sha256']
        except OSError:current=False
        proofs.append({**note,'report_current':current,
            'scope':'Historical executed check disclosure; does not attach proof to another run or certify a rule.'})
    return {'rules':rows,'proofs':proofs,'status':'TRANSFER_IN_PROGRESS' if any(r['attempted_examples'] for r in rows) else 'TRANSFER_NOT_STARTED',
        'execution_notice':'In progress describes the validation workflow stage, not a currently running paid model call.',
        'acceptance_and_transfer_are_separate':True}
