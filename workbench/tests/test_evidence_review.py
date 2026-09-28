"""Synthetic policy evidence only; no live engineering claims."""
import unittest
from unittest.mock import patch
from inspecta_scp.evidence_review import EvidenceReview, score_evidence, FORMAL
from inspecta_scp.config import PolicyError
from inspecta_scp.approvals import Approvals

class EvidenceReviewTests(unittest.TestCase):
    def setUp(self):
        from test_scoped_rulebooks import ScopedRulebookTests
        self.fixture=ScopedRulebookTests();self.fixture.setUp()
        self.c=self.fixture.c;self.service=EvidenceReview(self.c);self.run=self.fixture.run
        self.run['config']['required_gates']=['parse_type',FORMAL]
        self.add_formal()
    def tearDown(self):self.fixture.tearDown()
    def add_formal(self,items=None,status='FAIL'):
        items=items or [{'id':'a','requirement':'REQ-A','contract':'guarantee_A','status':'PASS'},
                        {'id':'b','requirement':'REQ-B','contract':'guarantee_B','status':'FAIL'}]
        self.run['result']['gates']=[g for g in self.run['result']['gates'] if g['gate']!=FORMAL]
        self.run['result']['gates'].append({'gate':FORMAL,'status':status,'reason':'Synthetic formal check',
            'evidence':self.c.store.object({'mapped_obligations':items})})
    def propose(self,policy='partial'):return self.service.propose(self.fixture.result['id'],policy,'Synthetic review',require_semantic=False)
    def decide(self,a,decision='APPROVED'):return Approvals(self.c.store).decide(a['id'],a['subject_digest'],decision,'Synthetic human')
    def exclusion(self,r,target=FORMAL+':b'):
        return self.service.exclude(r['id'],target,'TOOL_LIMITATION','Synthetic documented limit','Recheck after tool upgrade')
    def test_partial_formal_acceptance_preserves_failure_and_scores(self):
        r=self.propose();self.assertFalse(r['eligible'])
        e=self.exclusion(r);self.decide(e['approval']);r=self.service.inspect(r['id'])
        self.assertTrue(r['eligible']);self.assertEqual(r['scores']['excluded'],1)
        formal=next(x for x in r['rows'] if x['id']==FORMAL)
        self.assertEqual(formal['status'],'FAILED');self.assertEqual(formal['score']['passed'],1);self.assertEqual(formal['score']['total'],2)
        self.assertEqual(formal['included_total'],1)
        a=self.service.accept(r['id']);self.decide(a)
        accepted=self.service.inspect(r['id']);self.assertEqual(accepted['status'],'ACCEPTED_HUMAN_REVIEWED_PARTIAL_SCOPE')
        self.assertFalse(accepted['publishes_rules']);self.assertTrue(accepted['candidate_retained'])
        self.decide(e['approval'],'REVOKED');self.assertFalse(self.service.inspect(r['id'])['eligible'])
    def test_cannot_waive_all_formal_obligations(self):
        r=self.propose()
        for target in [FORMAL+':a',FORMAL+':b']:self.decide(self.exclusion(r,target)['approval'])
        with self.assertRaises(PolicyError):self.service.accept(r['id'])
    def test_cannot_exclude_whole_unmapped_formal_gate(self):
        self.run['result']['gates'][-1]['evidence']=self.c.store.object({'stdout':'11 verified, 0 errors'})
        r=self.propose()
        with self.assertRaisesRegex(PolicyError,'entire formal'):self.exclusion(r,FORMAL)
    def test_unapproved_rejected_exclusions_keep_failures_required(self):
        r=self.propose();e=self.exclusion(r)
        self.assertFalse(self.service.inspect(r['id'])['eligible']);self.decide(e['approval'],'REJECTED')
        self.assertFalse(self.service.inspect(r['id'])['eligible'])
    def test_stale_evidence_blocks_exclusion_and_acceptance(self):
        r=self.propose();e=self.exclusion(r);self.run['policy_current']=False
        with self.assertRaisesRegex(PolicyError,'changed'):self.decide(e['approval'])
        self.assertFalse(self.service.inspect(r['id'])['eligible'])
    def test_generic_acceptance_rechecks_evidence(self):
        r=self.propose();self.decide(self.exclusion(r)['approval']);a=self.service.accept(r['id'])
        self.run['result']['gates'][0]['status']='FAIL'
        with self.assertRaisesRegex(PolicyError,'changed'):self.decide(a)
    def test_all_checks_policy_and_notes(self):
        r=self.propose('all')
        with self.assertRaises(PolicyError):self.exclusion(r)
        self.service.note(r['id'],'Wait for formal repair','Human')
        self.assertEqual(len(self.service.catalog()['notes']),1)
    def test_full_scope_acceptance_and_revocation(self):
        self.add_formal([{'id':'a','requirement':'REQ-A','contract':'A','status':'PASS'}],'PASS')
        r=self.propose();a=self.service.accept(r['id']);self.decide(a)
        self.assertEqual(self.service.inspect(r['id'])['status'],'ACCEPTED_DECLARED_SCOPE')
        self.decide(a,'REVOKED');self.assertEqual(self.service.inspect(r['id'])['status'],'PARTIAL_PROGRESS_NOT_ACCEPTED')
    def test_malformed_counts_never_qualify(self):
        self.add_formal([{'id':'a','status':'PASS'}],'PASS')
        r=self.propose();self.assertFalse(r['eligible'])
    def test_repair_uses_existing_budget_enforcing_controller(self):
        r=self.propose()
        with patch('inspecta_scp.development.Development.generate_and_check',side_effect=PolicyError('Campaign expired')) as call:
            with self.assertRaisesRegex(PolicyError,'expired'):self.service.repair(r['id'],FORMAL+':b','campaign')
            self.assertEqual(call.call_args.args,(r['scope']['task_id'],'campaign',r['scope']['result_id']))
    def test_unimplemented_rule_declared_checks_remain_required(self):
        rule=self.c.store.read_record('candidate_rule',self.fixture.rule['id'])['record']
        rule['validation_gate_ids']=['PROPOSED-CUSTOM-OBLIGATION']
        candidate=self.c.store.record('candidate_rule',{'record':rule})
        task=self.c.store.record('development_task',{'target_file':'Synthetic.sysml','candidate_ids':[candidate['id']]})
        result=self.c.store.record('development_result',{'task_id':task['id'],'generated_run_id':'synthetic-run'})
        review=self.service.propose(result['id'])
        row=next(r for r in review['rows'] if r['id']=='PROPOSED-CUSTOM-OBLIGATION')
        self.assertTrue(row['required']);self.assertEqual(row['status'],'NOT_RUN')
        self.assertIn('PROPOSED-CUSTOM-OBLIGATION: NOT_RUN',review['blockers'])

    def test_quick_exclusion_and_acceptance_are_atomic(self):
        r=self.propose()
        result=self.service.quick_decision(r['id'],[FORMAL+':b'],'exclude','Human',r['fingerprint'],accept=True)
        self.assertEqual(result['status'],'ACCEPTED_HUMAN_REVIEWED_PARTIAL_SCOPE')
        self.assertEqual(result['scores']['excluded'],1)
    def test_quick_invalid_selection_rolls_back_every_decision(self):
        r=self.propose()
        with self.assertRaises(PolicyError):self.service.quick_decision(r['id'],[FORMAL+':b','missing'],'exclude','Human',r['fingerprint'])
        self.assertEqual(self.service.inspect(r['id'])['exclusions'],[])
        with self.assertRaises(PolicyError):self.service.quick_decision(r['id'],[FORMAL+':b'],'exclude','Human',r['fingerprint'],edits={FORMAL+':b':{'reason_code':'invalid'}})
        self.assertEqual(self.service.inspect(r['id'])['exclusions'],[])
    def test_quick_deferral_preserves_required_obligation_and_stale_rejected(self):
        r=self.propose();result=self.service.quick_decision(r['id'],[FORMAL+':b'],'defer','Human',r['fingerprint'])
        self.assertFalse(result['eligible']);self.assertEqual(result['scores']['excluded'],0)
        self.assertEqual(len(result['decision_deferrals']),1)
        self.run['policy_current']=False
        with self.assertRaisesRegex(PolicyError,'changed'):self.service.quick_decision(r['id'],[FORMAL+':b'],'exclude','Human',r['fingerprint'])
    def test_semantic_distance_authorization_ceiling(self):
        r=self.propose()
        for value in [.300001,1,-.1,float('nan'),True]:
            with self.assertRaisesRegex(PolicyError,'0.3'):
                self.service.set_semantic_policy(r['id'],value,'Human')

    def test_new_suggestions_require_semantic_policy(self):
        r=self.service.propose(self.fixture.result['id'])
        row=next(x for x in r['rows'] if x['id']=='semantic_similarity')
        self.assertTrue(row['required']);self.assertEqual(row['status'],'NOT_CONFIGURED')
    def test_semantic_gate_is_distinct_and_requires_architecture(self):
        from pathlib import Path
        from inspecta_scp.storage import sha_file
        import inspecta_scp.evidence_review as module
        r=self.propose();record=self.c.store.read_record('evidence_review',r['id'])
        snapshot=self.c.store.record('architecture_snapshot',{'run_id':'synthetic-run','config_hash':self.run['config_hash'],
            'normalized':self.c.store.object({'models':[]})})
        self.run['result']['gates'].append({'gate':'architecture_capture','status':'PASS','snapshot_id':snapshot['id'],'evidence':self.fixture.ref})
        result=self.c.store.record('development_result',{'task_id':self.fixture.task['id'],'generated_run_id':'synthetic-run','reference_run_id':'synthetic-run'})
        scope=self.fixture.s.create(result['id'],'Semantic test',['parse_type',FORMAL])
        for graph,expected in [('PASS','VERIFIED'),('FAIL','FAILED')]:
            assessment=self.c.store.record('development_graph_assessment',{'result_id':result['id'],'snapshot_ids':[snapshot['id']]*2,
                'checker_sha256':sha_file(Path(module.__file__).with_name('graph_equivalence.py')),
                'similarity_checker_sha256':sha_file(Path(module.__file__).with_name('contract_similarity.py')),
                'graph':{'status':graph},'similarity_assistance':{'cosine_distance':.05,'cosine_similarity':.95,'representation':'synthetic features'}})
            review=self.c.store.record('evidence_review',{**{k:v for k,v in record.items() if k!='id'},'scope_id':scope['id'],
                'semantic_policy':{'max_distance':.1,'assessment_id':assessment['id'],'reviewer':'Human'}})
            row=next(x for x in self.service.inspect(review['id'])['rows'] if x['id']=='semantic_similarity')
            self.assertEqual(row['status'],expected);self.assertEqual(row['score']['cosine_similarity'],.95)

    def test_monitoring_needs_complete_active_observation(self):
        score=score_evidence('qemu',{'observation':{'completed':True,'duration_seconds':120,'scenario':'nominal','clock':'simulated','monitor_active':True,'anomalies':0}})
        self.assertIn('No monitored anomaly',score['observation_verdict'])
        score=score_evidence('qemu',{'observation':{'completed':True,'duration_seconds':120,'anomalies':0}})
        self.assertIn('not established',score['observation_verdict'])
        self.assertIsNone(score_evidence('qemu',{'exit_code':0})['passed'])
        monitor=score_evidence('r2u2',{'property_verdicts':[{'id':'a','status':'PASS'},{'id':'b','status':'UNKNOWN'}]})
        self.assertEqual((monitor['passed'],monitor['total'],monitor['inconclusive']),(1,2,1))
    def test_verus_test_counts_are_not_requirement_counts(self):
        self.assertEqual(score_evidence('verus',{'stdout':'verification results:: 11 verified, 2 errors'})['total'],13)
        score=score_evidence('gumbox',{'stdout':'test result: ok. 5 passed; 0 failed; 1 ignored'})
        self.assertEqual((score['passed'],score['total'],score['ignored']),(5,6,1))



    def implementation_review(self,model='synthetic-run',proof='PASS'):
        review=self.propose()
        job=self.c.store.record('engineering_execution_job',{'model_run_id':model})
        record=self.c.store.read_record('evidence_review',review['id'])
        revised=self.c.store.record('evidence_review',{**{k:v for k,v in record.items() if k!='id'},'engineering_job_id':job['id']})
        evidence={'current':True,'state':'COMPLETE','components':[{'component':'example','verus_status':proof,
            'declared_contracts':['G1'],'gumbo_tests':{'cases':[{'name':'gumbo::G1','status':'ok'}]}}]}
        return revised,evidence

    def test_bound_implementation_proof_can_qualify_named_contract(self):
        record,evidence=self.implementation_review()
        with patch('inspecta_scp.engineering_progress.EngineeringProgress.inspect',return_value=evidence):
            r=self.service.inspect(record['id'])
        row=next(x for x in r['rows'] if x['id']==FORMAL)
        self.assertEqual(row['score']['passed'],1);self.assertEqual(row['score']['total'],1)
        self.assertEqual(row['score']['items'][0]['contract'],'G1')

    def test_other_model_proof_cannot_qualify_review(self):
        record,evidence=self.implementation_review(model='other-model')
        with patch('inspecta_scp.engineering_progress.EngineeringProgress.inspect',return_value=evidence):
            r=self.service.inspect(record['id'])
        row=next(x for x in r['rows'] if x['id']==FORMAL)
        self.assertEqual(row['score']['passed'],0);self.assertEqual(row['status'],'STALE')
        self.assertFalse(r['eligible'])

    def test_failed_component_does_not_invent_per_guarantee_success(self):
        record,evidence=self.implementation_review(proof='FAIL')
        with patch('inspecta_scp.engineering_progress.EngineeringProgress.inspect',return_value=evidence):
            r=self.service.inspect(record['id'])
        row=next(x for x in r['rows'] if x['id']==FORMAL)
        self.assertEqual(row['score']['passed'],0)
        self.assertEqual(row['score']['items'][0]['status'],'UNKNOWN')
