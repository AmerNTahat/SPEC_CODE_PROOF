import tempfile
import unittest
from pathlib import Path
from inspecta_scp.api import Application
from inspecta_scp.config import PolicyError
from inspecta_scp.controller import Controller
from inspecta_scp.traceability import Traceability


class TraceabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        project=self.root/'project';project.mkdir();(project/'Model.sysml').write_text('package Test {}')
        self.controller=Controller(self.root/'state')
        self.run=self.controller.create({'project':str(project),'input_files':['Model.sysml'],'model_file':'Model.sysml','task_operation':'verify-only'})
        self.trace=Traceability(self.controller)

    def tearDown(self):
        self.controller.close();self.temp.cleanup()

    def test_exact_snapshot_and_unknown_links(self):
        report=self.trace.report(self.run['id'])
        self.assertEqual(report['units'],[])
        self.assertIn('No reviewed unit registry',report['missing_links'])
        app=Application(self.root/'state',[],[])
        self.assertEqual(app.call('GET',f"/api/runs/{self.run['id']}/trace"),report)
        self.assertEqual(self.trace.input(self.run['id'],'Model.sysml')['text'],'package Test {}')
        (self.root/'project/Model.sysml').write_text('changed')
        self.assertFalse(self.trace.input(self.run['id'],'Model.sysml')['original_source_current'])
        self.assertEqual(self.trace.input(self.run['id'],'Model.sysml')['text'],'package Test {}')

    def test_unregistered_path_traversal_and_modified_snapshot_rejected(self):
        for relative in ['../outside','/etc/passwd','Other.sysml']:
            with self.assertRaises(PolicyError):self.trace.input(self.run['id'],relative)
        path=self.controller.store.root/'runs'/self.run['id']/'candidate/Model.sysml'
        path.write_text('tampered')
        with self.assertRaises(PolicyError):self.trace.input(self.run['id'],'Model.sysml')

    def test_unattached_object_not_exposed(self):
        unrelated=self.controller.store.object({'not_this_run':True})
        with self.assertRaises(PolicyError):self.trace.evidence(self.run['id'],unrelated['sha256'])

    def test_attached_record_is_hash_checked(self):
        # Synthetic record exercises viewer provenance, not a tool invocation.
        store=self.controller.store
        reference=store.object({'fixture':'viewer-only','exit_code':None})
        store.change(self.run['id'],{'READY'},'CHECKING')
        store.finish(self.run['id'],{'gates':[{'gate':'parse_type','status':'UNKNOWN','evidence':reference}],
                                    'task_status':'BLOCKED','engineering_accepted':False})
        self.assertEqual(self.trace.evidence(self.run['id'],reference['sha256'])['record']['fixture'],'viewer-only')
        (store.root/reference['path']).write_text('{}')
        with self.assertRaises(PolicyError):self.trace.evidence(self.run['id'],reference['sha256'])


if __name__=='__main__':unittest.main()
