"""Synthetic acceptance-policy tests; no model proof claims."""
from pathlib import Path
import tempfile,unittest
from unittest.mock import patch
from inspecta_scp.controller import Controller
from inspecta_scp.behavior_acceptance import BehaviorAcceptance
from inspecta_scp.approvals import Approvals

class BehaviorAcceptanceTests(unittest.TestCase):
    def test_human_acceptance_needs_all_checks_but_not_rule_transfer(self):
        with tempfile.TemporaryDirectory() as temp:
            c=Controller(Path(temp)/'state')
            try:
                task=c.store.record('development_task',{'capability_scope_id':None})
                result=c.store.record('development_result',{'task_id':task['id'],'generated_run_id':'generated','reference_run_id':'golden'})
                gates=[{'gate':g,'status':'PASS','evidence':{'path':'synthetic'}} for g in ['parse_type','configured_formal_verification','independent_requirements_tests']]
                def status(key):return {'id':key,'evidence_current_for_source':True,'policy_current':True,'config':{'required_gates':['parse_type','review']},'result':{'gates':gates}}
                service=BehaviorAcceptance(c)
                with patch.object(c,'status',side_effect=status),patch('inspecta_scp.development.Development.compare_graph',return_value={'id':'synthetic-graph','graph':{'status':'PASS'}}):
                    review=service.prepare(result['id']);self.assertEqual(review['status'],'READY_FOR_HUMAN_REVIEW')
                    self.assertFalse(review['rule_transfer_required'])
                    a=review['approval'];Approvals(c.store).decide(a['id'],a['subject_digest'],'APPROVED','Synthetic human')
                    accepted=service.inspect(review['id']);self.assertEqual(accepted['status'],'ACCEPTED_GOLDEN_SCOPE')
                    self.assertFalse(accepted['whole_system_acceptance']);self.assertFalse(accepted['publishes_rules'])
                    gates[1]['status']='NOT_RUN'
                    self.assertEqual(service.inspect(review['id'])['status'],'CHECKS_INCOMPLETE')
                    self.assertFalse(service.inspect(review['id'])['checks_current'])
                    blocked=service.prepare(result['id']);a=blocked['approval']
                    Approvals(c.store).decide(a['id'],a['subject_digest'],'APPROVED','Synthetic human')
                    self.assertEqual(service.inspect(blocked['id'])['status'],'CHECKS_INCOMPLETE')
            finally:c.close()
