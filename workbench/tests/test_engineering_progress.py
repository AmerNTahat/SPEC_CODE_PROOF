"""Synthetic evidence-integrity tests, not engineering acceptance."""
import json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from inspecta_scp.engineering_progress import EngineeringProgress
from inspecta_scp.storage import sha_file

class EngineeringProgressTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.work=self.root/'work';self.app=self.work/'crates/example/src/component/example_app.rs'
        self.app.parent.mkdir(parents=True);self.app.write_text('// guarantee G1\nrequires true ensures true')
        self.path=self.root/'report.json';self.model={'evidence_current_for_source':True,'policy_current':True}
        self.service=EngineeringProgress(SimpleNamespace(store=None,status=lambda _:self.model))
        self.job={'model_run_id':'model','workspace':str(self.work),'report_path':str(self.path)}
        self.report={'source_run_id':'model','workspace':str(self.work),'source_rs_preserved':True,
            'source_rs_sha256':{str(self.app.relative_to(self.work)):sha_file(self.app)},'checks':[
                {'crate':'example','kind':'verus','exit_code':0,'stdout':'verification results:: 1190 verified, 0 errors\nverification results:: 2 verified, 0 errors'},
                {'crate':'example','kind':'gumbo_tests','exit_code':0,'stdout':'test gumbo::G1 ... ok\ntest initialize ... ok\n'}]}
        self.save()
    def tearDown(self):self.tmp.cleanup()
    def save(self):self.path.write_text(json.dumps(self.report))
    def test_separates_component_dependency_and_test_counts(self):
        r=self.service.inspect(self.job);self.assertEqual(r['state'],'COMPLETE')
        self.assertEqual(r['components'][0]['verus_units_verified'],2)
        self.assertEqual(r['scores']['gumbo_passed'],1);self.assertEqual(r['scores']['other_tests_passed'],1)
    def test_changed_rust_removes_credit(self):
        self.app.write_text('changed');r=self.service.inspect(self.job)
        self.assertFalse(r['current']);self.assertEqual(r['scores']['components_passing_both'],0)
    def test_mismatched_model_removes_credit(self):
        self.report['source_run_id']='other';self.save();self.assertFalse(self.service.inspect(self.job)['current'])
    def test_stale_source_model_removes_credit(self):
        self.model['policy_current']=False;self.assertFalse(self.service.inspect(self.job)['current'])
    def test_dependency_success_does_not_hide_component_failure(self):
        self.report['checks'][0].update(exit_code=1,stdout='verification results:: 1190 verified, 0 errors\nverification results:: 0 verified, 1 errors');self.save()
        r=self.service.inspect(self.job);self.assertEqual(r['scores']['components_passing_both'],0)
        self.assertEqual(r['components'][0]['verus_status'],'FAIL')
    def test_incomplete_execution_not_complete(self):
        self.report.pop('source_rs_preserved');self.save();self.assertEqual(self.service.inspect(self.job)['state'],'RUNNING_OR_INCOMPLETE')
    def test_changed_cargo_configuration_invalidates_proof(self):
        from inspecta_scp.engineering_progress import implementation_manifest
        cargo=self.work/'Cargo.toml';cargo.write_text('[workspace]\n')
        self.report['implementation_manifest']=implementation_manifest(self.work);self.save()
        self.assertTrue(self.service.inspect(self.job)['current'])
        cargo.write_text('[workspace]\nmembers = []\n')
        self.assertFalse(self.service.inspect(self.job)['current'])
    def test_added_rust_source_invalidates_manifest(self):
        from inspecta_scp.engineering_progress import implementation_manifest
        self.report['implementation_manifest']=implementation_manifest(self.work);self.save()
        (self.app.parent/'added.rs').write_text('fn changed() {}')
        self.assertFalse(self.service.inspect(self.job)['current'])
    def system_fixture(self):
        from inspecta_scp.engineering_progress import implementation_manifest
        self.report['implementation_manifest']=implementation_manifest(self.work)
        self.report['checks']=[{'crate':'sys_example_proof','exit_code':0,'stdout':'verification results:: 1190 verified, 0 errors\nverification results:: 5 verified, 0 errors','stderr':''}]
        self.report['complete']=True;self.save()
    def test_system_vcs_separate_from_dependency_counts(self):
        self.system_fixture();r=self.service.system_inspect(self.job)
        self.assertEqual(r['status'],'PASS');self.assertEqual(r['verified_units'],5)
    def test_system_compile_failure_never_credits_dependency_proofs(self):
        self.system_fixture();self.report['checks'][0].update(exit_code=2,stdout='verification results:: 1190 verified, 0 errors',stderr='error[E0428]: duplicate module');self.save()
        r=self.service.system_inspect(self.job)
        self.assertEqual(r['verified_units'],0);self.assertEqual(r['checks'][0]['status'],'COMPILE_FAILURE')
    def test_system_proof_source_change_invalidates_evidence(self):
        self.system_fixture();self.app.write_text('changed')
        self.assertFalse(self.service.system_inspect(self.job)['current'])
