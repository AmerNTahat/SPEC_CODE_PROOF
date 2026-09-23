import json
import tempfile
import unittest
from pathlib import Path
from inspecta_scp.approvals import Approvals
from inspecta_scp.controller import Controller
from inspecta_scp.config import PolicyError
from inspecta_scp.development import Development
from inspecta_scp.learning_plan import LearningPlan
from inspecta_scp.sources import Sources

class DevelopmentTests(unittest.TestCase):
    def test_prepare_holds_reference_out_and_requires_correct_split(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);project=root/'project';project.mkdir()
            for name,text in [('Train.sysml','package Training {}'),('Golden.sysml','package Heldout {}'),('Types.sysml','package Types {}')]:
                (project/name).write_text(text)
            c=Controller(root/'state');sources=Sources(c.store);srcroot=sources.register_root(project,'learning')
            training=sources.register(srcroot['id'],'Train.sysml');golden=sources.register(srcroot['id'],'Golden.sysml')
            plan=LearningPlan(c.store).propose([],[{'source_id':training['id'],'start':1,'end':1,'label':'Training'}],[{'source_id':golden['id'],'start':1,'end':1,'label':'Heldout'}])
            a=plan['approval'];Approvals(c.store).decide(a['id'],a['subject_digest'],'APPROVED','Synthetic reviewer')
            rule=json.loads((Path(__file__).parent/'fixtures/synthetic-rule.json').read_text())
            rule['dependencies']=[]
            candidate=c.store.record('candidate_rule',{'record':rule})
            candidate_id=candidate['id']
            c.store.record('learning_extraction',{'plan_id':plan['id'],'candidate_id':candidate_id,'status':'DRAFT_PENDING_DEVELOPMENT_VALIDATION'})
            profile={'project':str(project),'input_files':['Train.sysml','Golden.sysml','Types.sysml'],'model_file':'Golden.sysml','required_gates':['parse_type']}
            service=Development(c)
            with self.assertRaises(PolicyError):service.prepare(profile,'Golden.sysml',['Golden.sysml'],'English',[candidate_id],plan['id'])
            with self.assertRaises(PolicyError):service.prepare(profile,'Train.sysml',[],'English',[candidate_id],plan['id'])
            task=service.prepare(profile,'Golden.sysml',['Types.sysml'],'English requirements',[candidate_id],plan['id'])
            self.assertEqual(task['approval']['status'],'PENDING')
            self.assertNotIn('package Heldout',str(task))
            self.assertEqual(task['required_gates'],['parse_type','architecture_capture'])
            with self.assertRaises(PolicyError):service.generate_and_check(task['id'],'nonexistent-campaign')
            bad=c.store.record('candidate_rule',{'record':{**rule,'dependencies':['missing-rule']}})
            c.store.record('learning_extraction',{'plan_id':plan['id'],'candidate_id':bad['id'],'status':'DRAFT_PENDING_DEVELOPMENT_VALIDATION'})
            with self.assertRaisesRegex(PolicyError,'unresolved rule dependencies'):
                service.prepare(profile,'Golden.sysml',['Types.sysml'],'English',[bad['id']],plan['id'])
            self.assertEqual((project/'Golden.sysml').read_text(),'package Heldout {}')
            c.close()
