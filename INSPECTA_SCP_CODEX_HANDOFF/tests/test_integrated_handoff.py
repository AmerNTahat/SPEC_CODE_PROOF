from __future__ import annotations
import copy, hashlib, importlib.util, json, os, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,root=False):
    p=ROOT/(name+'.py') if root else ROOT/'scripts'/(name+'.py')
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
install=load('install_workflow_goals');split=load('split_dataset');resolve=load('resolve_config');metrics=load('evaluation_tools')
library=load('library_catalog');milestone=load('report_milestone');receipt=load('check_build_result');launcher=load('start',True)

class GoalInstallation(unittest.TestCase):
    def setup_repo(self,d):
        repo=Path(d)/'repo';repo.mkdir();(repo/'.git').mkdir()
        src=Path(d)/'package';(src/'workflow_goals').mkdir(parents=True)
        for n in install.NAMES:(src/'workflow_goals'/n).write_text('new '+n)
        return repo,src
    def test_create_and_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            r,p=self.setup_repo(d);plan=install.plan(r,p);out=install.apply(r,plan,p)
            self.assertEqual(out['status'],'applied');self.assertEqual(install.apply(r,install.plan(r,p),p)['status'],'unchanged')
    def test_backup_original(self):
        with tempfile.TemporaryDirectory() as d:
            r,p=self.setup_repo(d);t=r/install.TARGET;t.mkdir(parents=True);(t/'goal_learn.txt').write_text('my edits')
            out=install.apply(r,install.plan(r,p),p);self.assertEqual((Path(out['backup_directory'])/'goal_learn.txt').read_text(),'my edits')
    def test_concurrent_edit_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            r,p=self.setup_repo(d);plan=install.plan(r,p);t=r/install.TARGET;t.mkdir(parents=True);(t/'goal_user.txt').write_text('new human edit')
            with self.assertRaises(ValueError):install.apply(r,plan,p)
            self.assertEqual((t/'goal_user.txt').read_text(),'new human edit')
    def test_source_change_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            r,p=self.setup_repo(d);plan=install.plan(r,p);(p/'workflow_goals/goal_learn.txt').write_text('changed')
            with self.assertRaises(ValueError):install.apply(r,plan,p)
    def test_symlink_target_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            r,p=self.setup_repo(d);(r/'SCP-extention-artificats').symlink_to(p,target_is_directory=True)
            with self.assertRaises(ValueError):install.plan(r,p)
    def test_wrong_repo_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            r,p=self.setup_repo(d);plan=install.plan(r,p);plan['repository']='/other'
            with self.assertRaises(ValueError):install.apply(r,plan,p)

class DatasetAssignments(unittest.TestCase):
    def source(self):return json.loads((ROOT/'templates/dataset-tasks.example.json').read_text())
    def test_manual_preserved(self):
        s=self.source();r=split.assign(s);self.assertEqual({t['id']:t['role'] for t in s['tasks']},{t['id']:t['role'] for t in r['tasks']})
    def test_group_conflict(self):
        s=self.source();s['tasks'][1]['role']='development'
        with self.assertRaises(ValueError):split.assign(s)
    def test_duplicate_content_conflict(self):
        s=self.source();s['tasks'][0]['content_hashes']=['same'];s['tasks'][2]['content_hashes']=['same']
        with self.assertRaises(ValueError):split.assign(s)
    def test_missing_lineage(self):
        s=self.source();s['tasks'][0]['lineage_id']=None
        with self.assertRaises(ValueError):split.assign(s)
    def test_deterministic_proposal(self):
        s=self.source();a=split.assign(s,'propose_grouped',[.34,.33,.33],'42');b=split.assign(s,'propose_grouped',[.34,.33,.33],'42')
        self.assertEqual(a,b);self.assertEqual(a['approval_state'],'PROPOSED');self.assertFalse(a['source_files_moved'])
    def test_require_explicit_fractions(self):
        with self.assertRaises(ValueError):split.assign(self.source(),'propose_grouped')
    def test_empty_dataset(self):
        with self.assertRaises(ValueError):split.assign({'tasks':[]})
    def test_approval_hash(self):
        r=split.assign(self.source());a=split.approve(r,'local-reviewer');self.assertEqual(a['proposal_sha256'],r['proposal_sha256'])
    def test_tampered_proposal(self):
        r=split.assign(self.source());r['tasks'][0]['role']='final'
        with self.assertRaises(ValueError):split.approve(r,'reviewer')

class Configuration(unittest.TestCase):
    def source(self):return json.loads((ROOT/'configs/learning.example.json').read_text())
    def test_explicit_override_wins(self):
        r=resolve.resolve(self.source(),{'budget':{'wall_seconds':2000}},{'budget':{'wall_seconds':1000}})
        self.assertEqual(r['config']['budget']['wall_seconds'],1000);self.assertEqual(r['config']['budget']['aggregate_model_tokens'],3000000)
    def test_equivalent_ui_cli_request(self):
        a=resolve.resolve(self.source(),{}, {'budget':{'aggregate_model_tokens':999}})
        b=resolve.resolve(self.source(),{}, {'budget':{'aggregate_model_tokens':999}})
        self.assertEqual(a['config_sha256'],b['config_sha256'])
    def test_no_implicit_readiness(self):self.assertEqual(resolve.resolve(self.source())['execution_readiness'],'NOT_ASSESSED')
    def test_create_requires_approval(self):
        with self.assertRaises(ValueError):resolve.resolve(self.source(),{}, {'task_operation':'create-system'})
    def test_explicit_create(self):self.assertEqual(resolve.resolve(self.source(),{}, {'task_operation':'create-system','creation_authorized':True})['config']['task_operation'],'create-system')
    def test_no_third_party(self):
        with self.assertRaises(ValueError):resolve.resolve(self.source(),{}, {'model':{'family':'other'}})
    def test_overlap_blocked(self):
        with self.assertRaises(ValueError):resolve.resolve(self.source(),{}, {'learning_materials':'/tmp/a','development_validation':'/tmp/a/child'})
    def test_bad_token_limit(self):
        with self.assertRaises(ValueError):resolve.resolve(self.source(),{}, {'budget':{'aggregate_model_tokens':0}})

class Evaluation(unittest.TestCase):
    def source(self):return json.loads((ROOT/'demos/synthetic-runs.json').read_text())
    def test_no_cache_double_counting(self):
        a=self.source()[0];m=metrics.calculate(a);self.assertEqual(m['total_tokens'],60000);self.assertEqual(m['verified_count'],1)
    def test_zero_verified_undefined(self):
        a=self.source()[0];a['unit_results']=[];m=metrics.calculate(a)
        self.assertIsNone(m['tokens_per_verified_unit']);self.assertIsNone(m['dollars_per_verified_unit']);self.assertEqual(m['coverage'],0)
    def test_stale_invalidated(self):
        a=self.source()[1];a['unit_results'][0]['artifact_revision']='old';self.assertEqual(metrics.calculate(a)['verified_count'],2)
    def test_missing_formal_not_verified(self):
        a=self.source()[1];a['unit_results'][0]['formal_gates']=[];self.assertEqual(metrics.calculate(a)['verified_count'],2)
    def test_duplicate_unit_blocked(self):
        a=self.source()[0];a['unit_results'].append(a['unit_results'][0])
        with self.assertRaises(ValueError):metrics.calculate(a)
    def test_mismatched_targets(self):
        a,b=self.source();b['target_unit_ids']=['other'];self.assertFalse(metrics.comparable(a,b))
    def test_missing_wall_unknown(self):
        a=self.source()[0];a['wall_seconds']=None;self.assertIsNone(metrics.calculate(a)['verified_per_minute'])
    def test_unmatched_policy(self):
        a,b=self.source();b['policy_id']='changed';self.assertFalse(metrics.comparable(a,b))
    def test_exports_without_models(self):
        with tempfile.TemporaryDirectory() as d:
            result=metrics.export(self.source(),Path(d)/'report',False);self.assertEqual(result['measurement_kinds'],['synthetic']);self.assertTrue((Path(d)/'report/index.html').is_file())
    def test_no_evidence_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d);(out/'keep').write_text('original')
            with self.assertRaises(ValueError):metrics.export(self.source(),out,False)

class IntegrationUtilities(unittest.TestCase):
    def test_catalog_preserves_originals(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'book.md').write_text('# MR-PROC-001\nConfidence: 0.88')
            r=library.catalog(root);self.assertIn('MR-PROC-001',r['rule_occurrences']);self.assertEqual(r['files_modified'],0)
    def test_catalog_no_snapshot(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'snapshot').mkdir();(root/'snapshot/book.md').write_text('MR-HIDDEN-001')
            self.assertNotIn('MR-HIDDEN-001',library.catalog(root)['rule_occurrences'])
    def test_milestone_completion_needs_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):milestone.record(Path(d),{'milestone':'M00','state':'completed','evidence':[]})
    def test_milestone_saved_and_hashed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'test.log').write_text('actual test log fixture')
            r=milestone.record(root,{'milestone':'M00','state':'completed','achieved':['Fixture audit'],'in_progress':['Next fixture step'],'remaining':['M01'],'blockers':[],'evidence':['test.log']})
            self.assertTrue((root/'IMPLEMENTATION_PROGRESS.md').is_file());self.assertEqual(r['evidence'][0]['sha256'],hashlib.sha256(b'actual test log fixture').hexdigest())
    def test_missing_build_is_not_ready(self):
        with tempfile.TemporaryDirectory() as d:self.assertFalse(receipt.check(Path(d))['ok'])
    def test_launcher_safe_flags(self):
        c=launcher.build_cmd('codex',Path('/repo'),'gpt-valid-example','prompt',True,Path('/log'))
        self.assertIn('workspace-write',c);self.assertNotIn('--full-auto',c);self.assertNotIn('danger-full-access',c);self.assertIn('model_provider="openai"',c)
    def test_reject_model_other_provider(self):
        with self.assertRaises(ValueError):launcher.build_cmd('codex',Path('/repo'),'other-model','prompt',False,Path('/log'))
    def test_distribution_goals_task_aware(self):
        for name in ['goal_learn.txt','goal_user.txt']:
            text=(ROOT/'workflow_goals'/name).read_text();self.assertIn('OPTIONAL',text);self.assertIn('full-stack',text);self.assertIn('INTEGRATION CONTRACT',text)
    def test_mode_goals_in_starting_instruction(self):
        t=(ROOT/'CODEX_START_PROMPT.txt').read_text();self.assertIn('goal_learn.txt',t);self.assertIn('goal_user.txt',t);self.assertIn('EVERY milestone',t)

if __name__=='__main__':unittest.main()
