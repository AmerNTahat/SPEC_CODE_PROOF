"""Synthetic policy checks. These do not establish live learning success."""
import tempfile
import unittest
from unittest.mock import patch
from inspecta_scp.controller import Controller
from inspecta_scp.learning import Learning
from inspecta_scp.config import PolicyError
from inspecta_scp.api import Application
from inspecta_scp.cli import parser


class WorkflowLearningTests(unittest.TestCase):
    def test_generated_provenance_freshness_and_failure_required(self):
        with tempfile.TemporaryDirectory() as d:
            c=Controller(d);s=c.store;service=Learning(c)
            origin=s.record('development_result',{'generated_run_id':'generated'})
            evidence=s.object({'stderr':'Frame period 120 is too small for the used budget 160'})
            baseline={'config':{'project':'generated','input_files':['model.sysml']}}
            run={**baseline,'evidence_current_for_source':True,'policy_current':True,
                 'result':{'gates':[{'gate':'hamr_codegen','status':'FAIL','reason':'failed','evidence':evidence}]}}
            def status(key):return baseline if key=='generated' else run
            try:
                with patch.object(c,'status',side_effect=status),patch.object(service,'extract',return_value={'draft':True}) as extract:
                    call=lambda:service.learn_workflow_failure('plan','campaign',['context'],'attempt',origin['id'],'generalize')
                    self.assertEqual(call(),{'draft':True})
                    feedback=extract.call_args.kwargs['_workflow_feedback']
                    self.assertFalse(feedback['golden_feedback_exported'])
                    self.assertIn('120',feedback['failures'][0]['stderr'])
                    for changed in ({'config':{'project':'golden','input_files':['model.sysml']}},
                                    {'evidence_current_for_source':False},{'policy_current':False},
                                    {'result':{'gates':[]}}):
                        previous=dict(run);run.update(changed);extract.reset_mock()
                        with self.assertRaises(PolicyError):call()
                        extract.assert_not_called();run.clear();run.update(previous)
                    with self.assertRaises(PolicyError):service.learn_workflow_failure('p','c',[],'r',origin['id'],'generalize')
                    with self.assertRaises(PolicyError):service.learn_workflow_failure('p','c',['ctx'],'r',origin['id'],'specialize')
            finally:c.close()

    def test_cli_and_api_share_service_arguments(self):
        args=parser().parse_args(['learning','learn-workflow-failure','--plan','p','--campaign','c',
            '--context-ids','a','b','--run','r','--result','g','--strategy','specialize','--prior-candidate','old'])
        self.assertEqual(args.context_ids,['a','b'])
        with tempfile.TemporaryDirectory() as d,patch.object(Learning,'learn_workflow_failure',return_value={'draft':True}) as learn:
            result=Application(d,[],[]).call('POST','/api/learning/workflow-failure',{
                'plan_id':args.plan,'campaign_id':args.campaign,'context_ids':args.context_ids,
                'run_id':args.run,'generated_result_id':args.result,'strategy':args.strategy,'prior_candidate_id':args.prior_candidate})
            learn.assert_called_once_with('p','c',['a','b'],'r','g','specialize','old')
            self.assertEqual(result,{'draft':True})
