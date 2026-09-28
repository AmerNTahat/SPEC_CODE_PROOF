#!/usr/bin/env python3
"""Reuse suitable selected tools; install Codex only when missing AND explicitly authorized.

No Sireum installation or paid calls. KSU selected-profile smoke tests and targeted
missing-dependency installation remain implementation milestone M01.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

sys.path.insert(0,str(Path(__file__).resolve().parent))
import tool_selection as tools

def execute(cmd:list[str], *, env:dict|None=None, timeout:int=120)->subprocess.CompletedProcess:
    return subprocess.run(cmd, env=tools.clean_env(env), capture_output=True, text=True,
                          timeout=timeout, check=False)

def install_codex(prefix:Path, expected:str, runner=execute)->dict:
    if hasattr(os,'geteuid') and os.geteuid()==0:
        raise ValueError('Do not install user-local tools as root. Reuse/probes do not require root.')
    if not shutil.which('node') or not shutil.which('npm'):
        raise ValueError('Node/npm required only for a NEW npm installation. Supply --codex PATH to reuse the downloaded standalone binary without Node/npm.')
    # No latest query: resolve only the explicitly selected family or exact release.
    if not re.fullmatch(r'\d+\.\d+\.(?:\d+|\*)',expected):
        raise ValueError('Fresh npm installation needs an exact x.y.z version or x.y.* family; no latest tag.')
    reply=runner(['npm','view',f'@openai/codex@{expected}','version','--json','--registry=https://registry.npmjs.org/'])
    if reply.returncode!=0: raise ValueError('Cannot resolve requested Codex version: '+reply.stderr[-2000:])
    versions=json.loads(reply.stdout)
    if isinstance(versions,str): versions=[versions]
    if not isinstance(versions,list):raise ValueError('Unexpected npm version result')
    versions=[v for v in versions if isinstance(v,str) and re.fullmatch(r'\d+\.\d+\.\d+',v) and tools.version_matches(v,expected)]
    if not versions:raise ValueError('Requested version unavailable. Do not substitute latest or another family.')
    version=max(versions,key=lambda v:tuple(map(int,v.split('.'))))
    target=prefix/'codex'/version
    if target.exists():
        raise ValueError('Managed target already exists but was not adopted. Inspect it; refusing overwrite: '+str(target))
    target.mkdir(parents=True,exist_ok=False)
    reply=runner(['npm','install','--prefix',str(target),'--registry=https://registry.npmjs.org/',
                  '--no-audit','--no-fund','--save-exact',f'@openai/codex@{version}'],timeout=600)
    if reply.returncode!=0:raise ValueError('Installation failed; partial directory preserved for diagnosis: '+str(target)+'\n'+reply.stderr[-2000:])
    record=tools.path_record('codex',str(target/'node_modules/.bin/codex'),'explicit_new_install',os.environ)
    result=tools.validate_codex(record,expected)
    if result['status']!='REUSE_CLI_READY': raise ValueError(result.get('reason','New CLI failed validation'))
    return result

def reference_image(image:str, refresh:bool=False, runner=execute)->dict:
    if not shutil.which('docker'):raise ValueError('Docker unavailable; install only when selected worker profile requires it.')
    inspect=runner(['docker','image','inspect',image],timeout=30)
    if inspect.returncode==0 and not refresh:
        return {'action':'REUSED_LOCAL_IMAGE','image':image,'identity':json.loads(inspect.stdout),
                'smoke_tests':'NOT_RUN','note':'Image identity only, not engineering readiness.'}
    if inspect.returncode!=0 and not refresh:
        # Differentiate absent image from daemon/permission errors without guessing from stderr.
        listed=runner(['docker','image','ls','--format','{{.ID}}'],timeout=30)
        if listed.returncode!=0:raise ValueError('Docker daemon/permission check failed; not evidence of a missing image. '+listed.stderr[-2000:])
        if not any(marker in inspect.stderr.lower() for marker in ('no such image','no such object')):
            raise ValueError('Image inspect failed for an unclassified reason; no automatic pull: '+inspect.stderr[-2000:])
    pulled=runner(['docker','pull',image],timeout=900)
    if pulled.returncode!=0:raise ValueError('Reference pull failed: '+pulled.stderr[-2000:])
    inspected=runner(['docker','image','inspect',image],timeout=30)
    if inspected.returncode!=0:raise ValueError('Pulled image identity could not be recorded')
    return {'action':'EXPLICIT_REFRESH' if refresh else 'PULLED_MISSING_IMAGE', 'image':image,
            'identity':json.loads(inspected.stdout),'smoke_tests':'NOT_RUN'}

def main(argv:list[str]|None=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--apply',action='store_true',help='Permit local probes and selection receipt; installation still requires --install-codex.')
    p.add_argument('--install-codex',action='store_true',help='Install only if no reusable/broken candidate was discovered. Existing selection wins.')
    p.add_argument('--fresh-codex',action='store_true',help='Explicitly request a separate Codex installation; never overwrites an existing target.')
    p.add_argument('--codex',help='Exact standalone executable; also accepts CODEX_BIN. Highest precedence.')
    p.add_argument('--codex-version',default=tools.DEFAULT_CODEX_VERSION,help='Expected actual CLI version, default 0.155.* for user-selected v_155.')
    p.add_argument('--sireum',help='Existing Sireum launcher; also accepts SIREUM_BIN.')
    p.add_argument('--sireum-home',help='Existing installation root (contains bin/sireum); also accepts SIREUM_HOME.')
    p.add_argument('--probe-sireum',action='store_true',help='With --apply, explicitly permit Sireum version/HAMR-help execution; dependencies may initialize. Unbuilt checkouts are preserved, not executed.')
    p.add_argument('--search-dir',action='append',type=Path,default=[],help='Bounded candidate-only scan; never executes discovered downloads.')
    p.add_argument('--prefix',type=Path,default=Path.home()/'.local/share/inspecta-scp-handoff')
    p.add_argument('--tool-selection',type=Path,help='Saved selection file; default under prefix.')
    p.add_argument('--pull-reference',action='store_true',help='Reuse local reference image; pull only when absent.')
    p.add_argument('--refresh-reference',action='store_true',help='Explicitly refresh reference tag, preserving recorded old identity.')
    p.add_argument('--reference-image',default='jasonbelt/microkit_provers:latest')
    a=p.parse_args(argv)
    try:
        if a.fresh_codex and not a.install_codex:raise ValueError('--fresh-codex also requires --install-codex')
        if a.fresh_codex and a.codex:raise ValueError('Choose --codex for reuse OR --fresh-codex for a separate installation, not both')
        if a.refresh_reference and not a.pull_reference:raise ValueError('--refresh-reference also requires --pull-reference')
        prefix=a.prefix.expanduser().absolute(); selection=(a.tool_selection or tools.selection_path(prefix)).expanduser().absolute()
        saved=tools.read_selection(selection)
        codex=tools.discover('codex',a.codex,saved=saved,prefix=prefix)
        sireum=tools.discover('sireum',a.sireum,sireum_home=a.sireum_home,saved=saved,prefix=prefix)
        plan={'policy':'REUSE_FIRST','apply':a.apply,'codex_expected_version':a.codex_version,
              'codex_candidates':codex,'sireum_candidates':sireum,
              'download_candidates':tools.discover_downloads(a.search_dir),
              'reference_policy':'reuse local; pull only absent' if not a.refresh_reference else 'explicit refresh',
              'sireum_probe_authorized':bool(a.apply and a.probe_sireum),
              'notes':['No automatic latest upgrade. No npm needed for existing standalone Codex.',
                       'Sireum and other KSU dependencies are assessed per selected project; install only missing/incompatible approved pieces.',
                       'No Sireum installer, model call, login or worker execution is performed by this helper.']}
        if not a.apply:
            print(json.dumps({**plan,'status':'PLAN_ONLY','installations_performed':False},indent=2));return 0
        selected={};checks=[];installed=False
        if codex and not a.fresh_codex:
            c,checks=tools.choose_codex(codex,a.codex_version)
            if not c:
                print(json.dumps({'status':'BLOCKED','codex_checks':checks},indent=2))
                raise ValueError('Existing/selected Codex failed requirements. Preserve it; supply the intended v_155 path or review the failure. --install-codex does not silently replace it.')
            selected['codex']=c
        elif a.install_codex:
            c=install_codex(prefix,a.codex_version);selected['codex']=c;installed=True
        elif a.codex or os.environ.get('CODEX_BIN'):
            raise ValueError('Explicit Codex could not be resolved')
        if sireum:
            s=tools.inspect_sireum(sireum[0],allow_probe=a.probe_sireum)
            if s['status']=='BLOCKED':
                print(json.dumps({'status':'BLOCKED','sireum':s},indent=2));raise ValueError(s['reason'])
            selected['sireum']=s
        image=reference_image(a.reference_image,a.refresh_reference) if a.pull_reference else None
        if selected:tools.save_selection(selection,selected,a.codex_version)
        report={'status':'PREPARATION_RECORDED','tools':selected,'codex_checks':checks,
                'selection_file':str(selection) if selected else None,'reference_image':image,
                'installations_performed':installed,'model_calls':0,'toolchain_compatibility':'NOT_VALIDATED',
                'next':'Run start.py with these selections. M01 must perform real KSU smoke tests and lock verified identities.'}
        receipts=prefix/'receipts';receipts.mkdir(parents=True,exist_ok=True)
        receipt=receipts/('reuse-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]+'.json')
        with receipt.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2);f.write('\n')
        report['receipt']=str(receipt)
        print(json.dumps(report,indent=2));return 0
    except (ValueError,OSError,subprocess.SubprocessError,json.JSONDecodeError) as exc:
        print('BLOCKED: '+str(exc),file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
