#!/usr/bin/env python3
"""Guided launcher for the INSPECTA/SCP Codex build handoff (Python 3.10+).
Does not contain the completed Workbench. Network/installation/model use needs explicit consent.
Default interactive flow inspects the repo, then offers preparation and Codex implementation.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, os, re, shutil, signal, subprocess, sys, threading, time, uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts'))
import tool_selection as toolsel

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def root_repo(path:Path)->Path:
    path=path.expanduser().resolve()
    if not path.is_dir():raise ValueError('Choose an existing repository. Clone it first or use scripts/fetch_sources.py after reviewing its help.')
    if not (path/'.git').exists():raise ValueError('Choose the Git repository/worktree root, not a parent directory or the handoff folder alone.')
    return path

def confirm(message:str,provided:bool=False)->None:
    if provided:return
    if not sys.stdin.isatty():raise ValueError('Explicit --yes is required in a non-interactive invocation')
    if input(message+' [yes/no]: ').strip().lower()!='yes':raise ValueError('Not authorized; no requested action performed')

def command_capture(cmd:list[str],timeout:int=20)->dict:
    try:
        r=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout)
        return {'returncode':r.returncode,'output':(r.stdout+r.stderr)[-5000:]}
    except (OSError,subprocess.TimeoutExpired) as exc:return {'returncode':None,'output':str(exc)}

def locate_codex(explicit:str|None, selection_file:Path|None=None)->str|None:
    # Discovery only. Launch performs version and capability checks on candidates.
    saved=toolsel.read_selection(selection_file or toolsel.selection_path())
    candidates=toolsel.discover('codex',explicit,saved=saved)
    return candidates[0]['path'] if candidates else None

def inspect(repo:Path|None,codex:str|None=None,sireum:str|None=None,
            sireum_home:str|None=None,selection_file:Path|None=None,search_dirs=None)->dict:
    saved=toolsel.read_selection(selection_file or toolsel.selection_path())
    codex_candidates=toolsel.discover('codex',codex,saved=saved)
    sireum_candidates=toolsel.discover('sireum',sireum,sireum_home=sireum_home,saved=saved)
    data={'python':sys.version.split()[0],'package':str(ROOT),
          'tools':{n:shutil.which(n) for n in ['git','node','npm','docker']},
          'codex':codex_candidates[0]['path'] if codex_candidates else None,
          'codex_candidates':codex_candidates,'sireum_candidates':sireum_candidates,
          'download_candidates':toolsel.discover_downloads(search_dirs or []),
          'policy':'REUSE_EXISTING_FIRST; user-selected Codex v_155 / 0.155.*',
          'model_calls':0,'installations_performed':False,
          'notes':['No downloaded candidate is executed during inspection.',
                   'Existing standalone Codex does not require Node/npm.',
                   'Actual KSU profile compatibility is established by M01 smoke tests, not PATH discovery.']}
    if repo:
        repo=root_repo(repo);data['repository']=str(repo)
        data['extension_present']=(repo/'SCP-extention-artificats/isolette_io_extnded').is_dir()
        data['git_status']=command_capture(['git','-C',str(repo),'status','--short'])
    return data

def stage(repo:Path)->Path:
    key=sha(ROOT/'CODEX_GOAL_INSPECTA_SCP_WORKBENCH.md')[:12]
    parent=repo/'.scp-handoff'
    if parent.is_symlink():raise ValueError('.scp-handoff may not be a symlink')
    folder=parent/('v2-'+key+'-'+uuid.uuid4().hex[:8]);folder.resolve().relative_to(repo)
    # Stage only distribution-manifest files, not newly created secrets/results in the source folder.
    entries=[]
    for line in (ROOT/'SHA256SUMS').read_text().splitlines():
        m=re.fullmatch(r'([a-f0-9]{64})  (.+)',line)
        if not m:raise ValueError('Invalid distribution manifest')
        digest,name=m.groups();rel=Path(name);source=ROOT/rel
        if rel.is_absolute() or '..' in rel.parts or source.is_symlink():raise ValueError('Unsafe distribution entry')
        source.resolve().relative_to(ROOT)
        if not source.is_file() or sha(source)!=digest:raise ValueError('Distribution changed: '+name)
        entries.append((rel,source))
    folder.mkdir(parents=True,exist_ok=False)
    for rel,source in entries:
        dest=folder/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
    shutil.copy2(ROOT/'SHA256SUMS',folder/'SHA256SUMS')
    return folder

def build_cmd(codex:str,repo:Path,model:str|None,prompt:str,batch:bool,output:Path)->list[str]:
    # OpenAI provider override avoids silently inheriting a third-party provider.
    common=['-C',str(repo),'--sandbox','workspace-write','-c','model_provider="openai"']
    if model:
        if not re.fullmatch(r'gpt-[A-Za-z0-9._-]+',model):raise ValueError('Use the actual available GPT/Astra model ID; no other providers/models are permitted')
        common+=['--model',model]
    if batch:return [codex,'exec',*common,'--json','--output-last-message',str(output),'-']
    return [codex,*common,'--ask-for-approval','on-request',prompt]

def launch_build(a)->int:
    repo=root_repo(a.repo)
    selection_file=(a.tool_selection or toolsel.selection_path()).expanduser().absolute()
    saved=toolsel.read_selection(selection_file)
    candidates=toolsel.discover('codex',a.codex,saved=saved)
    codex=candidates[0]['path'] if candidates else None
    prompt_plan={'repository':str(repo),'codex':codex,'mode':'batch' if a.batch else 'interactive',
                 'model':a.model or 'user-configured GPT/Astra; must be confirmed before launch',
                 'build_wall_limit_seconds':a.build_seconds,'engineering_demo_authorized':a.authorize_live_demo,
                 'scope':'Staged handoff then Codex implementation; not a completed installer/build guarantee.',
                 'installation_policy':'REUSE_EXISTING_FIRST_NO_AUTOMATIC_UPGRADES',
                 'codex_expected_version':a.codex_version,
                 'sireum_candidates':toolsel.discover('sireum',a.sireum,sireum_home=a.sireum_home,saved=saved)}
    print(json.dumps(prompt_plan,indent=2))
    if a.plan_only:return 0
    if not codex:raise ValueError('No Codex discovered. Supply --codex /absolute/path/to/your/v_155/binary or CODEX_BIN. Install only when no suitable binary is available.')
    if a.build_seconds<=0:raise ValueError('Build time limit must be positive')
    if not a.model and not a.gpt_profile_confirmed:
        raise ValueError('Supply --model with your actual available GPT/Astra ID, or explicitly confirm the configured GPT profile using --gpt-profile-confirmed. No model identity is guessed.')
    if a.batch and not a.model:raise ValueError('Batch mode requires an explicit available GPT model ID')
    selected_codex,checked=toolsel.choose_codex(candidates,a.codex_version)
    if not selected_codex:
        print(json.dumps({'codex_checks':checked},indent=2))
        raise ValueError('Existing Codex does not satisfy the selected version/CLI requirements. Preserve it and inspect the report; no auto-upgrade or substitution.')
    codex=selected_codex['path'];prompt_plan['codex']=codex
    selected_tools={'codex':selected_codex}
    sireum_candidates=toolsel.discover('sireum',a.sireum,sireum_home=a.sireum_home,saved=saved)
    if sireum_candidates:
        selected_sireum=toolsel.inspect_sireum(sireum_candidates[0],allow_probe=False)
        if selected_sireum['status']=='BLOCKED':raise ValueError(selected_sireum['reason'])
        selected_tools['sireum']=selected_sireum
    child_env=toolsel.environment_for(selected_tools)
    confirm('Allow Codex to modify this repository, use its authorized OpenAI model, and request needed installation permissions? Build token cost is not hard-capped by this launcher.',a.yes)
    staged=stage(repo);runid=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:6]
    output=repo/'.scp-handoff'/'build-runs'/runid;output.mkdir(parents=True,exist_ok=False)
    request={**prompt_plan,'staged_package':str(staged.relative_to(repo)),'build_id':runid,
             'build_token_enforcement':'NOT_IMPLEMENTED_BY_LAUNCHER','runtime_budget_defaults':'configs/learning.example.json and configs/user.example.json',
             'live_demo_policy':'Obtain bounded campaign and publication approvals before live runs; never infer unlimited authorization.',
             'selected_tools':selected_tools,
             'reuse_directive':'Use these exact discovered binaries. Reuse suitable existing KSU dependencies. Run capability smoke tests before adopting. Install missing items only; do not reinstall Codex via npm or replace SIREUM_HOME. Incompatibility requires diagnosis and approval.'}
    (output/'request.json').write_text(json.dumps(request,indent=2)+'\n')
    toolsel.save_selection(selection_file,selected_tools,a.codex_version)
    prompt=f'''Read {staged.relative_to(repo).as_posix()}/CODEX_START_PROMPT.txt and implement that handoff milestone by milestone. The package directory is {staged.relative_to(repo).as_posix()}. The build request is {str((output/'request.json').relative_to(repo))}. You are implementing software, NOT executing goal_learn immediately. Preserve local changes. IMPORTANT: the request.json selected_tools and child environment CODEX_BIN/SIREUM_BIN/SIREUM_HOME identify pre-existing tools to reuse. Keep the user-selected Codex v_155; do not chase latest or reinstall through npm. Run KSU capability tests and install only missing authorized components. Read {staged.relative_to(repo).as_posix()}/installation/REUSE_EXISTING_TOOLS.md. Print achieved / in progress / remaining / evidence / budget / blockers at every milestone. Use the staged report_milestone helper. Complete real application tests and the authorized live demo; if live authorization is absent, obtain it before paid research runs. Scope creation tests explicitly; continue existing projects otherwise. Do not claim completion from the bundled synthetic support demo. Finish with reports/demo/DEMO_REPORT.md and .scp-workbench/BUILD_RESULT.json.''' 
    cmd=build_cmd(codex,repo,a.model,prompt,a.batch,output/'last-message.txt')
    print('Starting Codex. Build records:',output,flush=True)
    started=time.monotonic();timed_out=threading.Event()
    if a.batch:
        with (output/'codex-events.jsonl').open('w',encoding='utf-8') as log,(output/'codex-stderr.log').open('w',encoding='utf-8') as err:
            proc=subprocess.Popen(cmd,cwd=repo,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,env=child_env,start_new_session=(os.name!='nt'))
            def expire():
                if proc.poll() is None:
                    timed_out.set()
                    try:
                        if os.name!='nt': os.killpg(proc.pid,signal.SIGTERM)
                        else: proc.terminate()
                    except ProcessLookupError: pass
                    def force_stop():
                        try:
                            if os.name!='nt': os.killpg(proc.pid,signal.SIGKILL)
                            elif proc.poll() is None: proc.kill()
                        except ProcessLookupError: pass
                    killer=threading.Timer(10,force_stop);killer.daemon=True;killer.start()
            timer=threading.Timer(a.build_seconds,expire);timer.start()
            try:
                proc.stdin.write(prompt);proc.stdin.close()
                for line in proc.stdout:
                    log.write(line);log.flush()
                    try:
                        ev=json.loads(line);item=ev.get('item',{})
                        if item.get('type')=='agent_message' and ev.get('type')=='item.completed':print(item.get('text',''),flush=True)
                    except (ValueError,TypeError):pass
                try:code=proc.wait(timeout=15)
                except subprocess.TimeoutExpired:proc.kill();code=proc.wait()
            except KeyboardInterrupt:
                proc.terminate();code=130
            finally:timer.cancel()
    else:
        proc=subprocess.Popen(cmd,cwd=repo,env=child_env)
        try:code=proc.wait(timeout=a.build_seconds)
        except subprocess.TimeoutExpired:
            timed_out.set();proc.terminate()
            try:code=proc.wait(timeout=10)
            except subprocess.TimeoutExpired:proc.kill();code=proc.wait()
        except KeyboardInterrupt:
            proc.terminate();code=130
    result={'codex_exit_code':code,'wall_seconds':time.monotonic()-started,'deadline_exceeded':timed_out.is_set(),
            'note':'CLI completion is not evidence that the Workbench or live demo passed. See milestone and build result records.'}
    (output/'launcher-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    print('Next: python3 start.py status --repo '+str(repo))
    return 124 if timed_out.is_set() else code

def main(argv=None)->int:
    if sys.version_info<(3,10):print('Python 3.10+ is required',file=sys.stderr);return 2
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='cmd',required=True)
    s=sub.add_parser('inspect');s.add_argument('--repo',type=Path);s.add_argument('--codex');s.add_argument('--sireum');s.add_argument('--sireum-home');s.add_argument('--tool-selection',type=Path);s.add_argument('--search-dir',action='append',type=Path,default=[])
    for name in ['start','build']:
        s=sub.add_parser(name);s.add_argument('--repo',type=Path,required=True);s.add_argument('--codex');s.add_argument('--model')
        s.add_argument('--sireum');s.add_argument('--sireum-home');s.add_argument('--tool-selection',type=Path)
        s.add_argument('--codex-version',default=toolsel.DEFAULT_CODEX_VERSION)
        s.add_argument('--gpt-profile-confirmed',action='store_true');s.add_argument('--batch',action='store_true')
        s.add_argument('--build-seconds',type=int,default=7200);s.add_argument('--authorize-live-demo',action='store_true')
        s.add_argument('--yes',action='store_true');s.add_argument('--plan-only',action='store_true')
    s=sub.add_parser('prepare',add_help=False,help='Reuse-first tools; start.py prepare --help for options');s.add_argument('arguments',nargs=argparse.REMAINDER)
    s=sub.add_parser('status');s.add_argument('--repo',type=Path,required=True)
    s=sub.add_parser('support-demo');s.add_argument('--output',type=Path,required=True);s.add_argument('--no-plots',action='store_true')
    s=sub.add_parser('app');s.add_argument('--repo',type=Path,required=True);s.add_argument('arguments',nargs=argparse.REMAINDER)
    s=sub.add_parser('test');s.add_argument('--schemas',action='store_true')
    values=list(argv if argv is not None else sys.argv[1:])
    if not values:p.print_help();return 0
    if values[0].startswith('--') and values[0] not in ['--help','-h']:values.insert(0,'start')
    if values and values[0]=='prepare':
        return subprocess.call([sys.executable,'-B',str(ROOT/'scripts/prepare_tools.py'),*values[1:]])
    a=p.parse_args(values)
    try:
        if a.cmd=='inspect':print(json.dumps(inspect(a.repo,a.codex,a.sireum,a.sireum_home,a.tool_selection,a.search_dir),indent=2));return 0
        if a.cmd in ['start','build']:
            if a.cmd=='start' and not a.plan_only:
                print(json.dumps(inspect(a.repo,a.codex,a.sireum,a.sireum_home,a.tool_selection),indent=2))
                if sys.stdin.isatty() and not a.model and not a.gpt_profile_confirmed:
                    choice=input('Enter your actual available GPT/Astra model ID (or type configured to explicitly confirm your configured GPT profile): ').strip()
                    if choice=='configured':a.gpt_profile_confirmed=True
                    else:a.model=choice
            return launch_build(a)
        if a.cmd=='status':
            repo=root_repo(a.repo);progress=repo/'IMPLEMENTATION_PROGRESS.md'
            print(progress.read_text()[-20000:] if progress.exists() else 'No implementation milestone report yet.')
            return subprocess.call([sys.executable,str(ROOT/'scripts/check_build_result.py'),'--repo',str(repo)])
        if a.cmd=='support-demo':
            cmd=[sys.executable,str(ROOT/'scripts/evaluation_tools.py'),'--input',str(ROOT/'demos/synthetic-runs.json'),'--output',str(a.output)]
            if a.no_plots:cmd.append('--no-plots')
            print('SYNTHETIC support demo only. No model calls, no HAMR execution, no actual proof claims.',flush=True)
            return subprocess.call(cmd)
        if a.cmd=='test':
            env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
            result=subprocess.call([sys.executable,'-B','-m','unittest','discover','-s',str(ROOT/'tests'),'-v'],env=env)
            if result==0 and a.schemas:result=subprocess.call([sys.executable,'-B',str(ROOT/'scripts/validate_contracts.py')],env=env)
            return result
        if a.cmd=='app':
            repo=root_repo(a.repo);receipt=repo/'.scp-workbench/BUILD_RESULT.json'
            if not receipt.is_file():raise ValueError('Workbench is not installed yet; run start/build and inspect its report first.')
            data=json.loads(receipt.read_text());exe=repo/data['cli_executable'];exe.resolve().relative_to(repo)
            if not exe.is_file():raise ValueError('Recorded Workbench executable is missing')
            rest=a.arguments[1:] if a.arguments[:1]==['--'] else a.arguments
            if not rest:rest=['--help']
            print('Launching the recorded local Workbench executable:',exe,flush=True)
            return subprocess.call([str(exe),*rest],cwd=repo)
        return 2
    except (OSError,ValueError,KeyError,subprocess.SubprocessError) as exc:print(f'BLOCKED: {exc}',file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
