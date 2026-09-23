import base64
from pathlib import Path
import tempfile
import unittest
from inspecta_scp.approvals import Approvals
from inspecta_scp.context_materials import ContextMaterials
from inspecta_scp.learning_plan import LearningPlan
from inspecta_scp.config import PolicyError
from inspecta_scp.sources import Sources
from inspecta_scp.storage import Store

class MaterialsTests(unittest.TestCase):
    def test_context_selection_holdout_approval_and_freshness(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);store=Store(root/'state');docs=root/'docs';docs.mkdir()
            (docs/'guide.txt').write_text('English requirements guide.\n')
            (docs/'Example.sysml').write_text('Monitor contract\nMonitor implementation\nRegulator contract\nRegulator implementation\n')
            materials=ContextMaterials(store);inventory=materials.inventory(docs)
            self.assertEqual(len(inventory['files']),2)
            document=materials.select(inventory['id'],['guide.txt'])['documents'][0]
            source=Sources(store).register(inventory['id'],'Example.sysml')
            plans=LearningPlan(store)
            train={'source_id':source['id'],'start':1,'end':2,'label':'Monitor'}
            valid={'source_id':source['id'],'start':3,'end':4,'label':'Regulator'}
            with self.assertRaisesRegex(PolicyError,'overlap'):
                plans.propose([document['id']],[train],[{**valid,'start':2}])
            plan=plans.propose([document['id']],[train],[valid])
            self.assertEqual(plan['retrieval']['comparison'],'distance <= epsilon')
            with self.assertRaises(PolicyError):plans.training_context(plan['id'])
            approval=plan['approval'];Approvals(store).decide(approval['id'],approval['subject_digest'],'APPROVED','Synthetic test reviewer')
            context=plans.training_context(plan['id'])
            self.assertFalse(context['validation_material_exported'])
            self.assertNotIn('Regulator',context['examples'][0]['text'])
            self.assertEqual(context['examples'][0]['text'],'Monitor contract\nMonitor implementation\n')
            (docs/'guide.txt').write_text('changed')
            with self.assertRaises(PolicyError):plans.training_context(plan['id'])
            store.close()

    def test_upload_and_no_reference_as_context(self):
        with tempfile.TemporaryDirectory() as d:
            store=Store(d);materials=ContextMaterials(store)
            uploaded=materials.upload('requirements.txt',base64.b64encode(b'English requirements').decode())
            self.assertEqual(len(uploaded['documents']),1)
            with self.assertRaises(PolicyError):materials.upload('../auth.json','eA==')
            with self.assertRaises(PolicyError):materials.upload('notes.txt','invalid-base64')
            store.close()

    def test_context_batches_cover_full_documents_without_validation_export(self):
        from inspecta_scp.learning import Learning
        text='abçλ'*20000
        original={'plan_id':'synthetic','examples':[{'text':'training'}],'context':[{'source_id':'s','name':'book','text':text}],
                  'retrieval':{'epsilon':0.1},'validation_material_exported':False}
        batches=Learning.context_batches(original)
        self.assertEqual(''.join(b['context'][0]['text'] for b in batches),text)
        self.assertEqual(batches[0]['context'][0]['start_character'],0)
        self.assertEqual(batches[-1]['context'][0]['end_character'],len(text))
        self.assertTrue(all(not b['validation_material_exported'] for b in batches))
