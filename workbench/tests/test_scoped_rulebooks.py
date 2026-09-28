"""Synthetic policy fixtures only; not rule-transfer or engineering evidence."""
from pathlib import Path
import json,tempfile,unittest
from unittest.mock import patch
from inspecta_scp.controller import Controller
from inspecta_scp.config import PolicyError
from inspecta_scp.approvals import Approvals
from inspecta_scp.scoped_rulebooks import ScopedRulebooks

class ScopedRulebookTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.c=Controller(Path(self.tmp.name)/'state');self.s=ScopedRulebooks(self.c)
        rule=json.loads((Path(__file__).parent/'fixtures/synthetic-rule.json').read_text());rule['dependencies']=[]
        rule['validation_gate_ids']=['parse_type','configured_formal_verification']
        self.rule=self.c.store.record('candidate_rule',{'record':rule})
        self.task=self.c.store.record('development_task',{'target_file':'Synthetic.sysml','candidate_ids':[self.rule['id']]})
        self.result=self.c.store.record('development_result',{'task_id':self.task['id'],'generated_run_id':'synthetic-run','status':'NOT_VALIDATED'})
        self.ref=self.c.store.object({'scope':'synthetic executed gate fixture'})
        self.run={'id':'synthetic-run','evidence_current_for_source':True,'policy_current':True,'config_hash':'test-config',
            'config':{'required_gates':['parse_type','configured_build']},'result':{'gates':[{'gate':g,'status':'PASS','evidence':self.ref,'reason':'Synthetic success'} for g in ['parse_type','configured_build']]}}
        self.mock=patch.object(Controller,'status',return_value=self.run);self.mock.start()
    def tearDown(self):self.mock.stop();self.c.close();self.tmp.cleanup()
    def scope(self,title='Parse only',gates=None):return self.s.create(self.result['id'],title,gates or ['parse_type'])
    def decide(self,b,decision='APPROVED'):
        a=b['approval'];return Approvals(self.c.store).decide(a['id'],a['subject_digest'],decision,'Synthetic human')
    def test_partial_counts_do_not_invent_requirement_coverage(self):
        r=self.scope(gates=['parse_type','configured_formal_verification'])
        self.assertEqual(r['status'],'PARTIAL_SUCCESS');self.assertEqual(r['scores']['scoped_check_fraction'],.5)
        self.assertIsNone(r['scores']['total_declared_requirements']);self.assertIsNone(r['scores']['verified_requirements'])
        self.assertEqual(next(x for x in r['checks'] if x['check']=='configured_formal_verification')['status'],'NOT_RUN')
        with self.assertRaises(PolicyError):self.s.prepare_batch([r['id']],'Not ready')
    def test_bulk_approval_is_scoped_and_revocable(self):
        first=self.scope();second=self.scope('Build only',['configured_build'])
        b=self.s.prepare_batch([first['id'],second['id']],'Synthetic scoped review');self.decide(b)
        for key in [first['id'],second['id']]:
            r=self.s.inspect(key);self.assertEqual(r['status'],'ACCEPTED_CURRENT_SCOPE')
            self.assertFalse(r['publishes_rules']);self.assertFalse(r['whole_system_acceptance'])
            self.assertEqual(r['rule_transfer_status'],'TRANSFER_IN_PROGRESS')
        self.decide(b,'REVOKED');self.assertNotEqual(self.s.inspect(first['id'])['status'],'ACCEPTED_CURRENT_SCOPE')
    def test_generic_approval_endpoint_cannot_bypass_stale_batch(self):
        first=self.scope();second=self.scope('Build',['configured_build']);b=self.s.prepare_batch([first['id'],second['id']],'Before change')
        self.run['result']['gates'][1]['status']='FAIL'
        with self.assertRaisesRegex(PolicyError,'changed'):self.decide(b)
        self.assertEqual(Approvals(self.c.store).get(b['approval']['id'])['status'],'PENDING')
        self.assertNotEqual(self.s.inspect(first['id'])['status'],'ACCEPTED_CURRENT_SCOPE')
    def test_approved_scope_becomes_stale_after_model_or_tool_change(self):
        r=self.scope();b=self.s.prepare_batch([r['id']],'Current');self.decide(b)
        self.run['policy_current']=False
        self.assertFalse(self.s.inspect(r['id'])['eligible'])
        self.assertNotEqual(self.s.inspect(r['id'])['status'],'ACCEPTED_CURRENT_SCOPE')
    def test_damaged_evidence_blocks_approval(self):
        r=self.scope();b=self.s.prepare_batch([r['id']],'Current')
        (self.c.store.root/self.ref['path']).write_text('{}')
        with self.assertRaises(PolicyError):self.decide(b)
    def test_selection_digest_and_empty_or_duplicate_selection(self):
        r=self.scope()
        for ids in [[],[r['id'],r['id']]]:
            with self.assertRaises(PolicyError):self.s.prepare_batch(ids,'Review')
        with self.assertRaises(PolicyError):self.s.prepare_batch([r['id']],'')
        b=self.s.prepare_batch([r['id']],'Review')
        with self.assertRaises(PolicyError):Approvals(self.c.store).decide(b['approval']['id'],'wrong','APPROVED','Human')
    def test_scope_requires_rule_binding_not_standalone_component_pass(self):
        task=self.c.store.record('development_task',{'candidate_ids':[]})
        result=self.c.store.record('development_result',{'task_id':task['id'],'generated_run_id':'synthetic-run'})
        with self.assertRaises(PolicyError):self.s.create(result['id'],'No rules',['parse_type'])
        with self.assertRaises(PolicyError):self.scope(gates=['review'])
    def test_capability_exclusions_need_current_review_and_receive_no_pass_credit(self):
        from inspecta_scp.capability_scope import CapabilityScope, approval_effect
        from inspecta_scp.config import digest
        prepared=self.c.store.record('prepared_requirements',{'english_sha256':'synthetic-english'})
        tool={'identity_digest':'synthetic-tool'}
        cap=self.c.store.record('capability_scope',{'tool_run_id':'synthetic-run','tool':tool,
            'preparation_id':prepared['id'],'english_sha256':'synthetic-english',
            'items':[{'requirement_id':str(i),'status':status,'reason':'Synthetic reason',
                      'revisit_condition':'Recheck after upgrade','evidence_run_ids':['synthetic-run']}
                     for i,status in enumerate(['NOT_SUPPORTED_TOOL_VERSION','OUT_OF_SCOPE_REFERENCE','REQUIRED'])]})
        self.task=self.c.store.record('development_task',{'target_file':'Synthetic.sysml','candidate_ids':[self.rule['id']],
            'capability_scope_id':cap['id'],'prepared_requirements_id':prepared['id']})
        self.result=self.c.store.record('development_result',{'task_id':self.task['id'],'generated_run_id':'synthetic-run'})
        self.run['config']['sireum']='/synthetic/sireum'
        a=Approvals(self.c.store).request('approve_capability_scope',{'scope_id':cap['id'],'scope_digest':digest(cap),'effect':approval_effect(cap)})
        with patch.object(CapabilityScope,'tool',return_value=tool):
            scope=self.scope()
            self.assertEqual(scope['scores']['qualification_requirement_denominator'],3)
            self.assertEqual(scope['scores']['requirement_status_counts'],{'AWAITING_SCOPE_REVIEW':3})
            Approvals(self.c.store).decide(a['id'],a['subject_digest'],'APPROVED','Synthetic reviewer')
            current=self.s.inspect(scope['id'])
            self.assertEqual(current['scores']['qualification_requirement_denominator'],1)
            self.assertEqual(current['scores']['excluded_requirements'],2)
            self.assertEqual(current['scores']['verified_requirements'],0)
            self.assertEqual(current['scores']['requirement_status_counts'],{'TOOL_LIMITATION':1,'OUTSIDE_REVIEWED_SCOPE':1,'NOT_VERIFIED':1})
            b=self.s.prepare_batch([scope['id']],'Synthetic check-only scope');self.decide(b)
            Approvals(self.c.store).decide(a['id'],a['subject_digest'],'REVOKED','Synthetic reviewer')
            self.assertNotEqual(self.s.inspect(scope['id'])['status'],'ACCEPTED_CURRENT_SCOPE')

    def test_suggestion_does_not_claim_unsupported(self):
        suggested=self.s.catalog()['suggested_validation_checks'][0]
        self.assertEqual(suggested['status'],'NOT_VERIFIED');self.assertIn('not an executed',suggested['scope'])

if __name__=='__main__':unittest.main()
