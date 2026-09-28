import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from inspecta_scp.controller import Controller
from inspecta_scp.config import PolicyError
from inspecta_scp.validation_repair import ValidationRepair,classify_errors
from inspecta_scp.development import Development

class ValidationRepairTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();root=Path(self.tmp.name);p=root/'project';p.mkdir();(p/'M.sysml').write_text('package X {}')
        self.c=Controller(root/'state');self.run=self.c.create({'project':str(p),'input_files':['M.sysml'],'model_file':'M.sysml','required_gates':['parse_type'],'budget':{'repairs_per_run':8}})
        rule=json.loads((Path(__file__).parent/'fixtures/synthetic-rule.json').read_text());rule['dependencies']=[]
        self.rule=self.c.store.record('candidate_rule',{'record':rule})
        self.task=self.c.store.record('development_task',{'baseline_run_id':self.run['id'],'candidate_ids':[self.rule['id']]})
        self.service=ValidationRepair(self.c)
    def tearDown(self):self.c.close();self.tmp.cleanup()
    def attempt(self,i,task=None):
        task=task or self.task
        self.c.store.record('development_generation_context',{'task_id':task['id'],'development_retry':{'n':i}})
        return self.c.store.record('development_result',{'task_id':task['id'],'status':'NOT_VALIDATED','attempt':i})
    def test_three_attempts_stop_and_guidance_preserves_total(self):
        for i in range(3):result=self.attempt(i)
        report=self.service.report(result['id']);self.assertTrue(report['repair_state']['human_guidance_required'])
        self.assertEqual(report['rules_consulted'][0]['candidate_id'],self.rule['id'])
        with self.assertRaisesRegex(PolicyError,'history changed'):self.service.guidance(result['id'],'Check binding','Human',2)
        self.service.guidance(result['id'],'Check processor binding without changing requirements','Human',3)
        state=self.service.state(self.task['id']);self.assertEqual(state['total_repair_attempts'],3);self.assertEqual(state['round_repair_attempts'],0)
        for i in range(3,6):result=self.attempt(i)
        self.assertTrue(self.service.state(self.task['id'])['human_guidance_required'])
        self.service.guidance(result['id'],'Check the type','Human',6)
        for i in range(6,8):result=self.attempt(i)
        self.assertTrue(self.service.state(self.task['id'])['run_limit_reached'])
    def test_failure_lesson_evidence_staleness_is_visible(self):
        from inspecta_scp.repair_lessons import catalog
        from inspecta_scp.storage import sha_file
        p=Path(self.tmp.name)/'failure.txt';p.write_text('Observed counterexample')
        self.c.store.record('repair_failure_lesson',{'title':'Guard overlap','evidence':[{'path':str(p),'sha256':sha_file(p)}]})
        current=catalog(self.c.store)[0]
        self.assertTrue(current['evidence_current'])
        self.assertIn('no requirement',current['acceptance_effect'])
        p.write_text('Different failure')
        self.assertFalse(catalog(self.c.store)[0]['evidence_current'])
        p.unlink()
        self.assertFalse(catalog(self.c.store)[0]['evidence_current'])

    def test_six_attempt_amendment_preserves_history_and_run_cap(self):
        for i in range(3):self.attempt(i)
        self.assertTrue(self.service.state(self.task['id'])['human_guidance_required'])
        self.service.set_human_limit(6,3,'User requests six attempts')
        state=self.service.state(self.task['id'])
        self.assertEqual(state['total_repair_attempts'],3)
        self.assertEqual(state['repair_limit_before_human'],6)
        self.assertFalse(state['human_guidance_required'])
        with self.assertRaisesRegex(PolicyError,'policy changed'):
            self.service.set_human_limit(7,3,'Stale amendment')
        for i in range(3,6):result=self.attempt(i)
        self.assertTrue(self.service.state(self.task['id'])['human_guidance_required'])
        self.service.guidance(result['id'],'Review dependency ownership','Human',6)
        for i in range(6,8):self.attempt(i)
        self.assertTrue(self.service.state(self.task['id'])['run_limit_reached'])
        self.assertEqual(self.service.state(self.task['id'])['total_repair_attempts'],8)

    def test_six_attempt_cycle(self):
        self.service.set_human_limit(6,3,'User requests six attempts')
        calls=[]
        def generated(task,campaign,previous=None):
            i=len(calls);calls.append(previous)
            if previous:self.attempt(i)
            return self.c.store.record('development_result',{'task_id':task,'status':'NOT_VALIDATED','call':i})
        with patch.object(Development,'generate_and_check',side_effect=generated):
            out=Development(self.c).validate_cycle(self.task['id'],'synthetic')
        self.assertEqual(len(calls),7)
        self.assertEqual(out['status'],'HUMAN_GUIDANCE_REQUIRED')
        self.assertEqual(out['failure_report']['repair_state']['total_repair_attempts'],6)

    def test_preflight_rejection_does_not_count_as_executed_repair(self):
        context=self.c.store.record('development_generation_context',{'task_id':self.task['id'],'attempt_id':'unique','development_retry':{'previous_result_id':'synthetic'}})
        self.assertEqual(self.service.state(self.task['id'])['total_repair_attempts'],0)
        self.c.store.record('development_attempt_receipt',{'context_id':context['id'],'model_call_id':'synthetic-recorded-call'})
        self.assertEqual(self.service.state(self.task['id'])['total_repair_attempts'],1)

    def test_revision_cannot_reset_human_checkpoint(self):
        for i in range(3):self.attempt(i)
        child=self.c.store.record('development_task',{'baseline_run_id':self.run['id'],'candidate_ids':[self.rule['id']],'predecessor_task_id':self.task['id']})
        self.assertTrue(self.service.state(child['id'])['human_guidance_required'])
    def test_return_to_ancestor_or_sibling_cannot_erase_repair_attempts(self):
        child=self.c.store.record('development_task',{'baseline_run_id':self.run['id'],'candidate_ids':[self.rule['id']],'predecessor_task_id':self.task['id'],'revision':'child'})
        sibling=self.c.store.record('development_task',{'baseline_run_id':self.run['id'],'candidate_ids':[self.rule['id']],'predecessor_task_id':self.task['id'],'revision':'sibling'})
        self.attempt(1);self.attempt(2,child);self.attempt(3,sibling)
        for task in [self.task,child,sibling]:
            state=self.service.state(task['id'])
            self.assertEqual(state['total_repair_attempts'],3)
            self.assertTrue(state['human_guidance_required'])

    def test_cycle_stops_after_initial_and_three_repairs(self):
        calls=[]
        def generated(task,campaign,previous=None):
            i=len(calls);calls.append(previous)
            if previous:self.attempt(i)
            return self.c.store.record('development_result',{'task_id':task,'status':'NOT_VALIDATED','call':i})
        with patch.object(Development,'generate_and_check',side_effect=generated):
            out=Development(self.c).validate_cycle(self.task['id'],'synthetic')
        self.assertEqual(len(calls),4);self.assertEqual(out['status'],'HUMAN_GUIDANCE_REQUIRED')
        self.assertTrue(out['failure_report']['repair_state']['human_guidance_required'])
    def test_cycle_stops_on_success_or_missing_evidence(self):
        for status in ('STRUCTURE_CHECKED_BEHAVIOR_UNASSESSED','BLOCKED'):
            with patch.object(Development,'generate_and_check',return_value={'status':status}) as g:
                result=Development(self.c).validate_cycle(self.task['id'],'synthetic')
            self.assertEqual(g.call_count,1);self.assertEqual(result['status'],status)
    def test_classification_uses_failed_diagnostics_only(self):
        families=classify_errors([{'status':'PASS','reason':'cargo test'},{'status':'FAIL','reason':'Frame period 120 is too small for used budget 160'}])
        self.assertIn('scheduling',families);self.assertNotIn('tool_environment',families)

if __name__=='__main__':unittest.main()
