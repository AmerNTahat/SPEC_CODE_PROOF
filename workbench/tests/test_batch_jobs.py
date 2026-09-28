"""Synthetic scheduling checks, not live extraction evidence."""
import tempfile
import unittest
from unittest.mock import patch
from inspecta_scp.controller import Controller
from inspecta_scp.learning import Learning
from inspecta_scp.campaign import Campaign
from inspecta_scp.learning_plan import LearningPlan
from inspecta_scp.data_preparation import DataPreparation

class BatchJobTests(unittest.TestCase):
    def test_resume_skips_completed_batches_and_pause_blocks_new_work(self):
        with tempfile.TemporaryDirectory() as d:
            c=Controller(d);s=c.store;service=Learning(c)
            try:
                grant=Campaign(s).authorize(200000,60,'TEST ONLY')
                s.record('learning_extraction',{'plan_id':'p','batch_index':0,'status':'DRAFT_PENDING_DEVELOPMENT_VALIDATION'})
                context={'context':[{'text':'a'*60000}],'examples':[]}
                def extracted(plan,campaign,index,focus="full_stack"):
                    return s.record('learning_extraction',{'plan_id':plan,'batch_index':index,'focus':focus,'status':'DRAFT_PENDING_DEVELOPMENT_VALIDATION'})
                with patch.object(DataPreparation,'training_materials',return_value=[]),patch.object(LearningPlan,'training_context',return_value=context),patch.object(service,'extract',side_effect=extracted) as extract:
                    Campaign(s).control(grant['id'],'pause')
                    self.assertEqual(service.extract_remaining('p',grant['id'])['status'],'BLOCKED')
                    extract.assert_not_called()
                    Campaign(s).control(grant['id'],'resume')
                    self.assertEqual(service.extract_remaining('p',grant['id'])['status'],'CONTEXT_BATCHES_EXTRACTED')
                    extract.assert_called_once_with('p',grant['id'],1,focus='full_stack')
                    service.extract_remaining('p',grant['id'])
                    self.assertEqual(extract.call_count,1)
                    service.extract_remaining('p',grant['id'],focus='system_architecture')
                    self.assertEqual(extract.call_count,3)
            finally:c.close()
