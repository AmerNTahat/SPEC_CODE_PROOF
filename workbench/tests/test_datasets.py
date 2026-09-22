"""Real assignment services with disposable sources; no independence claims."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from inspecta_scp.approvals import Approvals
from inspecta_scp.api import Application
from inspecta_scp.config import PolicyError
from inspecta_scp.controller import Controller
from inspecta_scp.datasets import Datasets
from inspecta_scp.sources import Sources


class DatasetTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.c=Controller(self.root/'state');self.d=Datasets(self.c.store)
        self.project=self.root/'project';self.project.mkdir()
        sources=Sources(self.c.store);root=sources.register_root(self.project,'learning')
        self.tasks=[]
        for i,role in enumerate(['learning','development','final']):
            name=f'M{i}.sysml';(self.project/name).write_text(f'package P{i} {{}}')
            source=sources.register(root['id'],name)
            self.tasks.append({'id':str(i),'family_id':str(i),'lineage_id':str(i),'role':role,
                               'source_ids':[source['id']],'reference_ids':[]})
        self.request={'tasks':self.tasks,'strategy':'user_assigned','fractions':None,'seed':'42'}

    def tearDown(self):
        self.c.close();self.temp.cleanup()

    def approve(self,record):
        request=self.d.request_review(record['id'])
        Approvals(self.c.store).decide(request['id'],request['subject_digest'],'APPROVED','TEST ONLY')
        return request

    def profile(self,record,task='0',mode='user'):
        return {'project':str(self.project),'input_files':[f'M{task}.sysml'],'model_file':f'M{task}.sysml',
                'dataset_assignment':record['id'],'dataset_task':task,'mode':mode,'task_operation':'verify-only'}

    def test_approval_freshness_revocation_and_input_scope(self):
        record=self.d.propose(self.request)
        with self.assertRaises(PolicyError):self.c.create(self.profile(record))
        approval=self.approve(record)
        run=self.c.create(self.profile(record));self.assertTrue(run['policy_current'])
        invalid=self.profile(record);invalid['input_files']=['M1.sysml'];invalid['model_file']='M1.sysml'
        with self.assertRaises(PolicyError):self.c.create(invalid)
        (self.project/'M0.sysml').write_text('changed')
        self.assertFalse(self.c.status(run['id'])['policy_current'])
        with self.assertRaises(PolicyError):self.d.approved(record['id'])
        (self.project/'M0.sysml').write_text('package P0 {}')
        Approvals(self.c.store).decide(approval['id'],approval['subject_digest'],'REVOKED','TEST ONLY')
        with self.assertRaises(PolicyError):self.c.create(self.profile(record))

    def test_lineage_and_duplicate_content_conflicts(self):
        for field in ['family_id','lineage_id','source_ids']:
            request=copy.deepcopy(self.request);request['tasks'][1][field]=request['tasks'][0][field]
            with self.assertRaises(PolicyError):self.d.propose(request)
        request=copy.deepcopy(self.request);request['tasks'][0]['lineage_id']=''
        with self.assertRaises(PolicyError):self.d.propose(request)

    def test_seeded_proposal_and_api_parity(self):
        request={**self.request,'strategy':'propose_grouped','fractions':[.34,.33,.33]}
        a=self.d.propose(request);b=self.d.propose(request)
        self.assertEqual(a,b);self.assertEqual(len(a['proposal']['groups']),3)
        api=Application(self.root/'state',[],[])
        self.assertEqual(api.call('POST','/api/datasets/propose',request),a)
        self.assertEqual(api.call('GET','/api/datasets')['datasets'][0]['id'],a['id'])
        self.assertEqual([t['role'] for t in self.tasks],['learning','development','final'])

    def test_final_cannot_train_and_references_never_inputs(self):
        record=self.d.propose(self.request);self.approve(record)
        with self.assertRaises(PolicyError):self.c.create(self.profile(record,'2','learning'))
        evaluator=self.root/'evaluator';evaluator.mkdir();(evaluator/'Answer.sysml').write_text('package P0 {}')
        sources=Sources(self.c.store);root=sources.register_root(evaluator,'evaluator')
        ref=sources.register(root['id'],'Answer.sysml')
        request=copy.deepcopy(self.request);request['tasks'][0]['reference_ids']=[ref['id']]
        record=self.d.propose(request);self.approve(record)
        with self.assertRaises(PolicyError):self.c.create(self.profile(record))
        request['tasks'][0]['source_ids']=[ref['id']]
        with self.assertRaises(PolicyError):self.d.propose(request)

    def test_ui_registration_uses_only_server_approved_allowlist(self):
        path=self.root/'inspected.json'
        path.write_text(json.dumps({'project':str(self.project),'input_files':['M0.sysml'],
                                    'model_file':'M0.sysml','dataset_task':'old-incomplete-selection'}))
        app=Application(self.root/'state',[path],[])
        result=app.call('POST','/api/datasets/register-profile',{'profile_id':'inspected','role':'learning'})
        self.assertEqual(result['source_ids'],self.tasks[0]['source_ids'])
        self.assertEqual(result['files'],['M0.sysml'])
        for body in [{'profile_id':'../../outside','role':'learning'},
                     {'profile_id':'inspected','role':'evaluator'}]:
            with self.assertRaises(PolicyError):app.call('POST','/api/datasets/register-profile',body)


if __name__=='__main__':unittest.main()
