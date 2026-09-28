"""Synthetic executable tests. No model calls, downloads or engineering runs."""
from __future__ import annotations
from contextlib import redirect_stdout, redirect_stderr
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import tool_selection as tools
import prepare_tools as prepare
import preflight
spec=importlib.util.spec_from_file_location('reuse_launcher',ROOT/'start.py')
launcher=importlib.util.module_from_spec(spec);spec.loader.exec_module(launcher)

FLAGS='--sandbox --model --ask-for-approval --cd --config --json --output-last-message'

def binary(path:Path,version:str='0.155.0',flags:str=FLAGS)->Path:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(f'#!{sys.executable}\nimport sys\nif sys.argv[1:]==["--version"]: print("codex-cli {version}")\nelse: print({flags!r})\n')
    path.chmod(0o755);return path

def rec(p:Path,name='codex')->dict:
    return tools.path_record(name,str(p),'explicit_cli',{'PATH':''})

class SelectionTests(unittest.TestCase):
    def test_user_family_and_not_filename(self):
        self.assertTrue(tools.version_matches('0.155.0','0.155.*'))
        self.assertFalse(tools.version_matches('0.156.0','0.155.*'))
        self.assertIsNone(tools.parsed_codex_version('downloaded-v_155'))
    def test_prerelease_not_silent(self):self.assertFalse(tools.version_matches('0.155.0-alpha.1','0.155.*'))
    def test_explicit_path_outside_path_with_spaces(self):
        with tempfile.TemporaryDirectory() as d:
            p=binary(Path(d)/'Downloads/my codex v_155')
            result=tools.discover('codex',str(p),env={'PATH':''},home=Path(d))
            self.assertEqual(result[0]['path'],str(p));self.assertEqual(tools.validate_codex(result[0])['status'],'REUSE_CLI_READY')
    def test_explicit_over_environment(self):
        with tempfile.TemporaryDirectory() as d:
            a=binary(Path(d)/'a');b=binary(Path(d)/'b')
            self.assertEqual(tools.discover('codex',str(a),env={'CODEX_BIN':str(b),'PATH':''})[0]['path'],str(a))
    def test_environment_over_saved(self):
        with tempfile.TemporaryDirectory() as d:
            a=binary(Path(d)/'a');b=binary(Path(d)/'b')
            saved={'tools':{'codex':{'path':str(b)}}}
            self.assertEqual(tools.discover('codex',saved=saved,env={'CODEX_BIN':str(a),'PATH':''})[0]['path'],str(a))
    def test_broken_explicit_no_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);binary(root/'bin/codex')
            rs=tools.discover('codex',str(root/'absent'),env={'PATH':str(root/'bin')})
            self.assertEqual(len(rs),1);self.assertEqual(tools.validate_codex(rs[0])['status'],'BLOCKED')
    def test_path_can_find_selected_family_after_old(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);a=binary(r/'a/codex','0.140.0');b=binary(r/'b/codex')
            rs=tools.discover('codex',env={'PATH':str(a.parent)+os.pathsep+str(b.parent)},home=r)
            chosen,checked=tools.choose_codex(rs)
            self.assertEqual(chosen['path'],str(b));self.assertEqual(len(checked),2)
    def test_wrong_version_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            p=binary(Path(d)/'v_155','0.156.0');before=p.read_bytes()
            self.assertEqual(tools.validate_codex(rec(p))['status'],'BLOCKED');self.assertEqual(before,p.read_bytes())
    def test_missing_cli_feature_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            p=binary(Path(d)/'codex',flags='--model')
            self.assertEqual(tools.validate_codex(rec(p))['status'],'BLOCKED')
    def test_permission_failure_does_not_chmod(self):
        with tempfile.TemporaryDirectory() as d:
            p=binary(Path(d)/'codex');p.chmod(0o600)
            self.assertEqual(tools.validate_codex(rec(p))['status'],'BLOCKED');self.assertEqual(p.stat().st_mode&0o777,0o600)
    def test_no_auth_claim(self):
        with tempfile.TemporaryDirectory() as d:
            result=tools.validate_codex(rec(binary(Path(d)/'codex')))
            self.assertEqual(result['authentication'],'NOT_CHECKED');self.assertEqual(result['astra_access'],'NOT_CHECKED')
    def test_help_timeout_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            p=binary(Path(d)/'codex')
            def run(cmd,**kwargs):return {'returncode':None,'output':'timeout','command':cmd}
            self.assertEqual(tools.validate_codex(rec(p),runner=run)['status'],'BLOCKED')
    def test_saved_selection_no_credentials(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);p=binary(r/'codex');record=tools.validate_codex(rec(p));out=r/'selection.json'
            tools.save_selection(out,{'codex':record})
            self.assertEqual(tools.read_selection(out)['tools']['codex']['path'],str(p))
            self.assertNotIn('OPENAI_API_KEY',out.read_text())
    def test_saved_hash_change_blocks_before_execution(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);p=binary(r/'codex');old=tools.validate_codex(rec(p));saved={'tools':{'codex':old}}
            p.write_text(p.read_text()+'\n# changed\n')
            rs=tools.discover('codex',saved=saved,env={'PATH':''})
            def forbidden(*a,**k):raise AssertionError('Changed binary should not run')
            self.assertEqual(tools.validate_codex(rs[0],runner=forbidden)['status'],'BLOCKED')
    def test_selected_symlink_identity(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);p=binary(r/'actual');link=r/'codex';link.symlink_to(p)
            result=tools.validate_codex(rec(link));self.assertEqual(result['path'],str(link));self.assertEqual(result['real_path'],str(p))
    def test_download_scan_never_executes(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);p=r/'codex-v_155';p.write_text('not an executable')
            with patch('subprocess.run',side_effect=AssertionError('must not execute')):
                result=tools.discover_downloads([r])
            self.assertEqual(len(result),1);self.assertFalse(result[0]['executed'])
    def test_download_scan_is_bounded(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d)
            for i in range(20):(r/f'codex-{i}').write_text('x')
            self.assertLessEqual(len(tools.discover_downloads([r],max_entries=3)),3)

class SireumReuseTests(unittest.TestCase):
    def setup_sireum(self,d,jar=True):
        r=Path(d)/'Existing Sireum';p=binary(r/'bin/sireum')
        (r/'bin/build.cmd').write_text('source build')
        if jar:(r/'bin/sireum.jar').write_bytes(b'FAKE JAR')
        return r,p
    def test_home_discovery(self):
        with tempfile.TemporaryDirectory() as d:
            root,p=self.setup_sireum(d)
            rs=tools.discover('sireum',env={'PATH':'','SIREUM_HOME':str(root)})
            self.assertEqual(rs[0]['path'],str(p));self.assertEqual(rs[0]['source'],'environment_SIREUM_HOME')
    def test_no_default_sireum_execution(self):
        with tempfile.TemporaryDirectory() as d:
            root,p=self.setup_sireum(d)
            def forbidden(*a,**k):raise AssertionError('Sireum must not execute')
            result=tools.inspect_sireum(rec(p,'sireum'),runner=forbidden)
            self.assertEqual(result['probe'],'NOT_RUN');self.assertEqual(result['engineering_smoke_tests'],'NOT_RUN')
    def test_unbuilt_checkout_not_bootstrapped(self):
        with tempfile.TemporaryDirectory() as d:
            root,p=self.setup_sireum(d,jar=False)
            def forbidden(*a,**k):raise AssertionError('Unbuilt checkout must not execute')
            result=tools.inspect_sireum(rec(p,'sireum'),allow_probe=True,runner=forbidden)
            self.assertEqual(result['status'],'PRESERVE_NEEDS_BOOTSTRAP_REVIEW');self.assertFalse((root/'bin/sireum.jar').exists())
    def test_sireum_probe_still_needs_real_checks(self):
        with tempfile.TemporaryDirectory() as d:
            root,p=self.setup_sireum(d)
            def run(cmd,**kwargs):return {'command':cmd,'returncode':0,'output':'Sireum 4.x' if '--version' in cmd else 'HAMR sysml codegen'}
            result=tools.inspect_sireum(rec(p,'sireum'),allow_probe=True,runner=run)
            self.assertEqual(result['status'],'CLI_PROBED_PROJECT_VALIDATION_REQUIRED');self.assertEqual(result['engineering_smoke_tests'],'NOT_RUN')
    def test_changed_jar_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            root,p=self.setup_sireum(d);record=tools.inspect_sireum(rec(p,'sireum'))
            (root/'bin/sireum.jar').write_text('changed')
            rs=tools.discover('sireum',saved={'tools':{'sireum':record}},env={'PATH':''})
            self.assertEqual(tools.inspect_sireum(rs[0])['status'],'BLOCKED')
    def test_child_environment_preserves_exact_selection(self):
        selected={'codex':{'path':'/local/codex-v_155'},'sireum':{'path':'/local/Sireum/bin/sireum','home':'/local/Sireum'}}
        env=tools.environment_for(selected,{'PATH':'original','SIREUM_HOME':'old'})
        self.assertEqual(env['CODEX_BIN'],'/local/codex-v_155');self.assertEqual(env['SIREUM_HOME'],'/local/Sireum');self.assertEqual(env['PATH'],'original')
    def test_probe_env_strips_tokens(self):
        e=tools.clean_env({'OPENAI_API_KEY':'secret','PATH':'path'})
        self.assertNotIn('OPENAI_API_KEY',e);self.assertEqual(e['PATH'],'path')

class PreparationTests(unittest.TestCase):
    def quiet(self,args):
        with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):return prepare.main(args)
    def test_existing_binary_reused_without_npm(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=binary(root/'standalone-v_155');prefix=root/'state'
            with patch.object(prepare,'install_codex',side_effect=AssertionError('must reuse, not install')):
                code=self.quiet(['--codex',str(p),'--install-codex','--prefix',str(prefix),'--apply'])
            self.assertEqual(code,0);data=tools.read_selection(prefix/'tool-selection.json')
            self.assertEqual(data['tools']['codex']['path'],str(p))
    def test_incompatible_not_reinstalled(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=binary(root/'codex','0.140.0');before=p.read_bytes()
            with patch.object(prepare,'install_codex',side_effect=AssertionError('must not replace')):
                code=self.quiet(['--codex',str(p),'--install-codex','--prefix',str(root/'state'),'--apply'])
            self.assertEqual(code,2);self.assertEqual(p.read_bytes(),before)
    def test_plan_only_does_not_execute(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=binary(root/'codex')
            with patch('subprocess.run',side_effect=AssertionError('plan must not run tools')):
                code=self.quiet(['--codex',str(p),'--install-codex','--prefix',str(root/'state')])
            self.assertEqual(code,0);self.assertFalse((root/'state').exists())
    def test_repeat_reuse_keeps_binary(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=binary(root/'codex');args=['--codex',str(p),'--prefix',str(root/'state'),'--apply'];before=p.stat().st_mtime_ns
            self.assertEqual(self.quiet(args),0);self.assertEqual(self.quiet(args),0)
            self.assertEqual(p.stat().st_mtime_ns,before)
    def test_refresh_requires_explicit_pull(self):self.assertEqual(self.quiet(['--refresh-reference']),2)
    def test_fresh_requires_install(self):self.assertEqual(self.quiet(['--fresh-codex']),2)
    def test_local_image_not_pulled(self):
        calls=[]
        def run(cmd,**kwargs):calls.append(cmd);return subprocess.CompletedProcess(cmd,0,json.dumps([{'Id':'sha256:test'}]),'')
        with patch.object(prepare.shutil,'which',return_value='/fake/docker'):
            result=prepare.reference_image('image',runner=run)
        self.assertEqual(result['action'],'REUSED_LOCAL_IMAGE');self.assertEqual(len(calls),1)
    def test_daemon_failure_not_missing_image(self):
        def run(cmd,**kwargs):return subprocess.CompletedProcess(cmd,1,'','permission denied')
        with patch.object(prepare.shutil,'which',return_value='/fake/docker'):
            with self.assertRaises(ValueError):prepare.reference_image('image',runner=run)
    def test_missing_image_pulled_once(self):
        calls=[]
        def run(cmd,**kwargs):
            calls.append(cmd)
            if cmd[1:3]==['image','inspect'] and len(calls)==1:return subprocess.CompletedProcess(cmd,1,'','No such image: image')
            return subprocess.CompletedProcess(cmd,0,'[]','')
        with patch.object(prepare.shutil,'which',return_value='/fake/docker'):
            result=prepare.reference_image('image',runner=run)
        self.assertEqual(result['action'],'PULLED_MISSING_IMAGE');self.assertEqual(sum(c[1]=='pull' for c in calls),1)
    def test_inspection_is_not_full_validation(self):
        with tempfile.TemporaryDirectory() as d:
            p=binary(Path(d)/'codex')
            result=launcher.inspect(None,str(p),selection_file=Path(d)/'missing.json')
            self.assertEqual(result['model_calls'],0);self.assertFalse(result['installations_performed'])
    def test_preflight_explicit_path(self):
        with tempfile.TemporaryDirectory() as d:
            p=binary(Path(d)/'binary')
            result=preflight.inventory(False,codex=str(p),selection_file=Path(d)/'missing.json')
            self.assertEqual(result['tools']['codex']['path'],str(p));self.assertEqual(result['tools']['codex']['probe'],'NOT_RUN')
    def test_install_plan_never_uses_latest_tag(self):
        src=(ROOT/'scripts/prepare_tools.py').read_text()
        self.assertNotIn('dist-tags.latest',src);self.assertNotIn('@openai/codex@latest',src)
    def test_goal_pin_and_child_environment_linkage(self):
        text=(ROOT/'CODEX_START_PROMPT.txt').read_text();self.assertIn('v_155',text);self.assertIn('CODEX_BIN',text)
        text=(ROOT/'start.py').read_text();self.assertIn("'selected_tools':selected_tools",text);self.assertIn('env=child_env',text)

if __name__=='__main__':unittest.main()
