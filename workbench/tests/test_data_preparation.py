"""Preparation policy tests use synthetic materials and a stub response, not live evidence."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from inspecta_scp.controller import Controller
from inspecta_scp.sources import Sources
from inspecta_scp.context_materials import ContextMaterials
from inspecta_scp.learning_plan import LearningPlan
from inspecta_scp.data_preparation import DataPreparation
from inspecta_scp.approvals import Approvals
from inspecta_scp.campaign import Campaign
from inspecta_scp.model_worker import ModelWorker
from inspecta_scp.config import PolicyError


class DataPreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.c=Controller(self.root/'state');self.s=self.c.store;self.service=DataPreparation(self.c)
        docs=self.root/'docs';docs.mkdir();self.file=docs/'Model.sysml'
        self.file.write_text('TRAIN output must be Off\nGOLDEN secret validation\n')
        (docs/'guide.txt').write_text('Identify atomic requirements and state assumptions.')
        inv=ContextMaterials(self.s).inventory(docs)
        self.guide=ContextMaterials(self.s).select(inv['id'],['guide.txt'])['documents'][0]
        source=Sources(self.s).register(inv['id'],'Model.sysml')
        self.plan=LearningPlan(self.s).propose([self.guide['id']],
            [{'source_id':source['id'],'start':1,'end':1,'label':'Train'}],
            [{'source_id':source['id'],'start':2,'end':2,'label':'Validate'}])
        self.approve(self.plan)
    def approve(self,r):
        a=r['approval'];Approvals(self.s).decide(a['id'],a['subject_digest'],'APPROVED','TEST ONLY')
    def tearDown(self):self.c.close();self.temp.cleanup()
    def test_review_role_revision_and_source_freshness(self):
        p=self.service.prepare(self.plan['id'],'training',0,existing_english='R1: output shall initially be Off.')
        with self.assertRaises(PolicyError):self.service.training_materials(self.plan['id'])
        self.approve(p);self.assertEqual(self.service.training_materials(self.plan['id'])[0]['english'],p['english'])
        with self.assertRaises(PolicyError):self.service.approved(p['id'],self.plan['id'],'validation')
        revision=self.service.revise(p['proposal_id'],'R1: revised statement requires new review.')
        with self.assertRaises(PolicyError):self.service.approved(revision['id'],self.plan['id'],'training')
        self.file.write_text('changed\nGOLDEN secret validation\n')
        with self.assertRaises(PolicyError):self.service.approved(p['id'],self.plan['id'],'training')
    def test_extraction_is_selected_role_only_and_quotes_must_exist(self):
        grant=Campaign(self.s).authorize(200000,60,'TEST ONLY')
        value={'title':'Train','system_description':'Observed train component.',
            'requirements':[{'id':'R1','statement':'The output shall be Off.','category':'functional',
                             'source_start':1,'source_end':1,'evidence_quote':'output must be Off'}],
            'assumptions':[],'unresolved':['Purpose not specified.']}
        response={'id':'stub-not-live','result':{'status':'RESPONSE_RECEIVED','response':value}}
        with patch.object(ModelWorker,'propose',return_value=response) as model:
            p=self.service.prepare(self.plan['id'],'training',0,grant['id'],self.guide['id'])
            prompt=model.call_args.args[1]
            self.assertIn('TRAIN',prompt);self.assertNotIn('GOLDEN',prompt)
            self.assertFalse(p['derived_from_reference']);self.assertIn('R1',p['english'])
            value['requirements'][0]['evidence_quote']='invented number 120'
            with self.assertRaisesRegex(PolicyError,'quotation'):
                self.service.prepare(self.plan['id'],'training',0,grant['id'],self.guide['id'])
    def test_existing_validation_english_never_becomes_training(self):
        p=self.service.prepare(self.plan['id'],'validation',0,existing_english='Held-out requirements.')
        self.approve(p)
        self.assertEqual(self.service.approved(p['id'],self.plan['id'],'validation')['english'],'Held-out requirements.')
        with self.assertRaises(PolicyError):self.service.training_materials(self.plan['id'])

    def test_unchanged_approved_english_reuses_authorization_but_edit_does_not(self):
        r=self.service.prepare_from_context(self.plan['id'],'training',0,self.guide['id'],1,1)
        self.assertEqual(r['approval']['status'],'APPROVED')
        self.assertIn('source reuse only',r['approval']['reviewer'])
        self.assertEqual(r['english'],'Identify atomic requirements and state assumptions.')
        self.assertTrue(self.service.training_materials(self.plan['id'])[0]['english_source'])
        changed=self.service.revise(r['proposal_id'],'A changed requirement is not approved by copying the source authorization.')
        self.assertEqual(changed['approval']['status'],'PENDING')
        with self.assertRaises(PolicyError):self.service.approved(changed['id'],self.plan['id'],'training')

    def test_context_supplement_keeps_original_and_requires_new_review(self):
        original=self.service.prepare(self.plan['id'],'validation',0,existing_english='R1: a reviewed obligation.')
        self.approve(original)
        passage={'context_id':self.guide['id'],'start':1,'end':1}
        revised=self.service.supplement_context(original['id'],[passage],'Recover environmental assumptions referenced by R1')
        self.assertEqual(revised['approval']['status'],'PENDING')
        self.assertTrue(revised['english'].startswith(original['english']))
        self.assertIn('Identify atomic requirements',revised['english'])
        self.assertEqual(revised['context_supplements'][0]['source_id'],self.guide['source_id'])
        self.assertEqual(revised['previous_preparation_id'],original['id'])
        import json
        from inspecta_scp.cli import parser,dispatch
        passages=self.root/'passages.json';passages.write_text(json.dumps([passage]))
        cli=dispatch(parser().parse_args(['--state-dir',str(self.s.root),'learning','supplement-context',
            '--preparation',original['id'],'--passages',str(passages),
            '--rationale','Recover environmental assumptions referenced by R1']))
        self.assertEqual(cli['id'],revised['id'])
        self.assertEqual(self.service.approved(original['id'],self.plan['id'],'validation')['english'],original['english'])
        with self.assertRaises(PolicyError):self.service.approved(revised['id'],self.plan['id'],'validation')
        with self.assertRaisesRegex(PolicyError,'already included'):self.service.supplement_context(revised['id'],[passage],'Duplicate')
        with self.assertRaisesRegex(PolicyError,'approved context'):self.service.supplement_context(original['id'],[{**passage,'context_id':'unselected'}],'Unapproved')
        edited=self.service.revise(revised['proposal_id'],revised['english']+'\nHuman interpretation requires review.')
        self.assertEqual(edited['context_supplements'],revised['context_supplements'])

    def test_large_preparation_resumes_completed_batches_without_rebilling(self):
        self.file.write_text('TRAIN output must be Off\n'+('comment\n'*99)+'Second output must be On\n'+('comment\n'*20)+'GOLDEN\n')
        source=Sources(self.s).register(ContextMaterials(self.s).inventory(self.file.parent)['id'],'Model.sysml')
        plan=LearningPlan(self.s).propose([self.guide['id']],
            [{'source_id':source['id'],'start':1,'end':121,'label':'Large'}],
            [{'source_id':source['id'],'start':122,'end':122,'label':'Held out'}]);self.approve(plan)
        grant=Campaign(self.s).authorize(200000,60,'TEST ONLY')
        def response(start,quote):
            return {'id':'stub-'+str(start),'result':{'status':'RESPONSE_RECEIVED','response':{
                'title':'Component','system_description':'Description','requirements':[{'id':'R1',
                'statement':'Preserve source behavior.','category':'functional','source_start':start,
                'source_end':start,'evidence_quote':quote}],'assumptions':[],'unresolved':[]}}}
        with patch.object(ModelWorker,'propose',side_effect=[response(1,'output must be Off'),
                {'id':'failed-stub','result':{'status':'BLOCKED','reason':'synthetic timeout'}},response(101,'Second output must be On')]) as model:
            blocked=self.service.prepare(plan['id'],'training',0,grant['id'],self.guide['id'])
            self.assertEqual(blocked['status'],'BLOCKED');self.assertEqual(len(blocked['completed_proposal_ids']),1)
            result=self.service.prepare(plan['id'],'training',0,grant['id'],self.guide['id'])
            self.assertEqual(model.call_count,3)
            self.assertEqual([x['id'] for x in result['source_claims']],['L1-R1','L101-R1'])
            self.assertEqual(result['approval']['status'],'PENDING')
