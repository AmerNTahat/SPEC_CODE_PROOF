"""Repair storage/control tests, synthetic models; real tests are separate."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from inspecta_scp.controller import Controller
from inspecta_scp.config import PolicyError
from inspecta_scp.repairs import Repairs


class RepairTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.project=self.root/'project';self.project.mkdir();(self.project/'Model.sysml').write_text('package Original {}')
        self.c=Controller(self.root/'state');self.r=Repairs(self.c)
        self.profile={'project':str(self.project),'input_files':['Model.sysml'],'model_file':'Model.sysml',
                      'task_operation':'verify-only','repair_allowed_files':['Model.sysml'],'required_gates':['parse_type']}
        self.run=self.c.create(self.profile)

    def tearDown(self):self.c.close();self.tmp.cleanup()

    def patch(self,text,before='package Original {}'):
        return {'Model.sysml':{'expected_sha256':hashlib.sha256(before.encode()).hexdigest(),'text':text}}

    def test_stage_preserves_original_and_deadline(self):
        candidate=self.r.stage(self.run['id'],'test-diagnostic',self.patch('package Proposed {}'))
        self.assertEqual((self.project/'Model.sysml').read_text(),'package Original {}')
        self.assertEqual(self.c.status(self.run['id'])['deadline'],self.run['deadline'])
        self.assertEqual(candidate['source_files_modified'],0)

    def test_scope_expected_hash_and_noop(self):
        for patch in [{'../escape':{'expected_sha256':'x','text':'x'}},self.patch('changed','wrong'),self.patch('package Original {}')]:
            with self.assertRaises(PolicyError):self.r.stage(self.run['id'],'issue',patch)
        scoped=self.c.create({**self.profile,'repair_allowed_files':[]})
        with self.assertRaises(PolicyError):self.r.stage(scoped['id'],'issue',self.patch('changed'))

    def test_failed_validation_preserves_baseline_result_and_source(self):
        baseline=self.c.execute(self.run['id'])
        candidate=self.r.stage(self.run['id'],'missing-tool',self.patch('package Proposed {}'))
        result=self.r.validate(candidate['id'])
        self.assertEqual(result['status'],'BLOCKED')
        self.assertFalse(result['engineering_accepted'])
        current=self.c.status(self.run['id'])
        self.assertEqual(current['result'],baseline['result']);self.assertEqual(current['deadline'],baseline['deadline'])
        self.assertEqual(self.r.validate(candidate['id']),result)
        self.assertEqual((self.project/'Model.sysml').read_text(),'package Original {}')

    def test_parent_revision_and_cycle_detection(self):
        first=self.r.stage(self.run['id'],'issue',self.patch('first'))
        second=self.r.stage(self.run['id'],'issue',self.patch('second','first'),first['id'])
        self.assertEqual(second['parent_id'],first['id'])
        with self.assertRaises(PolicyError):self.r.stage(self.run['id'],'other-issue',self.patch('first','second'),second['id'])
        with self.assertRaises(PolicyError):self.r.stage(self.run['id'],'issue',self.patch('third'),first['id'])

    def test_attempt_allowance_not_reset_by_new_issue(self):
        run=self.c.create({**self.profile,'budget':{'repairs_per_run':1}})
        self.r.stage(run['id'],'one',self.patch('first'))
        with self.assertRaises(PolicyError):self.r.stage(run['id'],'two',self.patch('second'))

    def test_stale_user_edit_blocks_repair(self):
        candidate=self.r.stage(self.run['id'],'issue',self.patch('proposed'))
        (self.project/'Model.sysml').write_text('user edit')
        with self.assertRaises(PolicyError):self.r.validate(candidate['id'])
        self.assertEqual((self.project/'Model.sysml').read_text(),'user edit')

    def test_late_stop_and_pause_win_atomic_finalization(self):
        for request,expected in [('STOP_REQUESTED','CANCELLED'),('PAUSE_REQUESTED','PAUSED')]:
            run=self.c.create(self.profile)
            self.c.store.change(run['id'],{'READY'},request)
            self.c.store.finish(run['id'],{'gates':[],'task_status':'CHECKED'})
            after=self.c.status(run['id'])
            self.assertEqual(after['state'],expected);self.assertEqual(after['result']['task_status'],expected)


if __name__=='__main__':unittest.main()
