"""Synthetic transfer-state tests, not engineering acceptance evidence."""
from pathlib import Path
import tempfile,unittest
from unittest.mock import patch
from inspecta_scp.controller import Controller
from inspecta_scp.validation_progress import validation_progress

class ValidationProgressTests(unittest.TestCase):
    def test_acceptance_does_not_invent_transfer_or_erase_exclusions(self):
        with tempfile.TemporaryDirectory() as temp:
            c=Controller(Path(temp)/'state')
            try:
                rule=c.store.record('candidate_rule',{'record':{'id':'SYNTHETIC-RULE'}})
                other=c.store.record('candidate_rule',{'record':{'id':'NOT-ATTEMPTED'}})
                task=c.store.record('development_task',{'candidate_ids':[rule['id']],'target_file':'NewExample.sysml','golden_sha256':'synthetic'})
                result=c.store.record('development_result',{'task_id':task['id'],'generated_run_id':'generated'})
                c.store.record('behavior_acceptance_review',{'result_id':result['id']})
                accepted={'result_id':result['id'],'id':'synthetic-acceptance','status':'CHECKS_INCOMPLETE','excluded_requirements':[{'requirement_id':'R-uncovered'}]}
                with patch('inspecta_scp.validation_progress.BehaviorAcceptance.inspect',return_value=accepted):
                    def row():return next(r for r in validation_progress(c)['rules'] if r['candidate_id']==rule['id'])
                    self.assertEqual(row()['status'],'TRANSFER_IN_PROGRESS')
                    accepted['status']='ACCEPTED_GOLDEN_SCOPE'
                    self.assertEqual(row()['status'],'ACCEPTED_CURRENT_SCOPE_TRANSFER_IN_PROGRESS')
                    c.store.record('rule_review',{'candidate_id':rule['id'],'status':'TESTED','blockers':[],'supporting_run':'unrelated'})
                    self.assertNotEqual(row()['status'],'ACCEPTED_AND_TRANSFERRED')
                    c.store.record('rule_review',{'candidate_id':rule['id'],'status':'TESTED','blockers':[],'supporting_run':'generated'})
                    self.assertEqual(row()['status'],'ACCEPTED_AND_TRANSFERRED')
                    self.assertEqual(row()['accepted_golden_scopes'][0]['excluded_requirements'],accepted['excluded_requirements'])
                    accepted['status']='CHECKS_INCOMPLETE'
                    self.assertEqual(row()['status'],'TRANSFER_IN_PROGRESS')
                    self.assertEqual(row()['accepted_golden_scopes'],[])
            finally:c.close()
