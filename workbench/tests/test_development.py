import json
import tempfile
import unittest
from pathlib import Path
from inspecta_scp.approvals import Approvals
from inspecta_scp.controller import Controller
from inspecta_scp.config import PolicyError
from inspecta_scp.development import Development,bounded_inventory
from inspecta_scp.learning_plan import LearningPlan
from inspecta_scp.sources import Sources

class DevelopmentTests(unittest.TestCase):
    def test_large_optional_diagnostics_keep_whole_entries_and_disclose_omissions(self):
        items=[{'identifier':'large','features':'x'*50000},{'identifier':'small'}]
        result=bounded_inventory(items)
        self.assertEqual(result['components'],[items[1]])
        self.assertEqual(result['omitted_components'],1)
        self.assertEqual(result['total_components'],2)

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
            revised=c.store.record('candidate_rule',{'record':{**rule,'revision':2}})
            c.store.record('learning_extraction',{'plan_id':plan['id'],'candidate_id':revised['id'],
                'revision_of':candidate_id,'status':'DRAFT_PENDING_DEVELOPMENT_VALIDATION'})
            successor=service.prepare(profile,'Golden.sysml',['Types.sysml'],'English requirements',
                [revised['id']],plan['id'],predecessor_task_id=task['id'])
            self.assertEqual(successor['predecessor_task_id'],task['id'])
            failed=c.store.record('development_result',{'task_id':task['id'],'status':'NOT_VALIDATED'})
            reviewed=service.revise_rules(failed['id'],[revised['id']])
            self.assertEqual(reviewed['approval']['status'],'PENDING')
            self.assertEqual(reviewed['requirements'],task['requirements'])
            self.assertEqual(reviewed['validation_plan_id'],task['validation_plan_id'])
            self.assertEqual(reviewed['predecessor_task_id'],task['id'])
            with self.assertRaisesRegex(PolicyError,'preserve generation inputs'):
                service.prepare(profile,'Golden.sysml',['Types.sysml'],'Changed English',
                    [revised['id']],plan['id'],predecessor_task_id=task['id'])
            with self.assertRaisesRegex(PolicyError,'Conflicting revisions|drop or duplicate'):
                service.prepare(profile,'Golden.sysml',['Types.sysml'],'English requirements',
                    [candidate_id,revised['id']],plan['id'],predecessor_task_id=task['id'])
            unrelated=c.store.record('candidate_rule',{'record':{**rule,'revision':3}})
            c.store.record('learning_extraction',{'plan_id':plan['id'],'candidate_id':unrelated['id'],
                'status':'DRAFT_PENDING_DEVELOPMENT_VALIDATION'})
            with self.assertRaisesRegex(PolicyError,'recorded refinement'):
                service.prepare(profile,'Golden.sysml',['Types.sysml'],'English requirements',
                    [unrelated['id']],plan['id'],predecessor_task_id=task['id'])
            with self.assertRaises(PolicyError):service.generate_and_check(task['id'],'nonexistent-campaign')
            bad=c.store.record('candidate_rule',{'record':{**rule,'dependencies':['missing-rule']}})
            c.store.record('learning_extraction',{'plan_id':plan['id'],'candidate_id':bad['id'],'status':'DRAFT_PENDING_DEVELOPMENT_VALIDATION'})
            with self.assertRaisesRegex(PolicyError,'unresolved rule dependencies'):
                service.prepare(profile,'Golden.sysml',['Types.sysml'],'English',[bad['id']],plan['id'])
            self.assertEqual((project/'Golden.sysml').read_text(),'package Heldout {}')
            c.close()
