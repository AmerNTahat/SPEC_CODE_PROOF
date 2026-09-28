#!/usr/bin/env python3
"""Reuse-first discovery and capability probes. No package-manager calls or model calls.

Explicit paths > explicit environment > saved selection > PATH > known user-local
locations. Discovered Downloads candidates are NEVER executed automatically.
A fingerprint records identity, not publisher authenticity or engineering validity.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Any, Mapping

DEFAULT_CODEX_VERSION = '0.155.*'  # User's selected v_155 family; not a claim about global latest.
DEFAULT_LABEL = 'v_155'
SECRET_NAMES = ('OPENAI_API_KEY', 'CODEX_API_KEY', 'ANTHROPIC_API_KEY', 'GITHUB_TOKEN', 'GH_TOKEN')

def clean_env(env: Mapping[str, str] | None = None) -> dict[str, str]:
    result = dict(os.environ if env is None else env)
    for key in SECRET_NAMES:
        result.pop(key, None)
    return result

def selection_path(prefix: Path | None = None) -> Path:
    return (prefix or Path.home()/'.local/share/inspecta-scp-handoff')/'tool-selection.json'

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def read_selection(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    if path.is_symlink():
        raise ValueError('Tool-selection file must not be a symlink: '+str(path))
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('record_type') != 'LOCAL_TOOL_SELECTION':
        raise ValueError('Not a local tool-selection record: '+str(path))
    return data

def path_record(name: str, value: str, source: str, env: Mapping[str, str]) -> dict[str, Any]:
    p = Path(value).expanduser()
    if not p.is_file():
        # A bare command may be resolved, but an explicit invalid path must not silently fall back.
        found = shutil.which(value, path=env.get('PATH', '')) if not any(c in value for c in ('/', '\\')) else None
        if found:
            p = Path(found)
    p = p.absolute()  # Preserve launcher/symlink path; real path is a separate identity.
    return {'tool': name, 'path': str(p), 'real_path': str(p.resolve()), 'source': source,
            'exists': p.is_file(), 'executable': p.is_file() and os.access(p, os.X_OK),
            'status': 'DISCOVERED_NOT_VALIDATED', 'probe': 'NOT_RUN'}

def _from_path(name: str, env: Mapping[str, str]) -> list[str]:
    found = []
    for folder in env.get('PATH', '').split(os.pathsep):
        if not folder:  # Never discover executables from an implicit cwd.
            continue
        for suffix in (('', '.exe', '.cmd', '.bat') if os.name == 'nt' else ('',)):
            p = Path(folder).expanduser()/f'{name}{suffix}'
            if p.is_file() and os.access(p, os.X_OK):
                found.append(str(p.absolute()))
    return found

def discover(name: str, explicit: str | None = None, *, sireum_home: str | None = None,
             saved: dict | None = None, env: Mapping[str, str] | None = None,
             home: Path | None = None, prefix: Path | None = None) -> list[dict[str, Any]]:
    """Strong selections return only that path, including when broken. No quiet fallback."""
    e = dict(os.environ if env is None else env)
    h = home or Path.home()
    if explicit:
        return [path_record(name, explicit, 'explicit_cli', e)]
    if name == 'sireum' and sireum_home:
        return [path_record(name, str(Path(sireum_home).expanduser()/'bin'/('sireum.bat' if os.name=='nt' else 'sireum')), 'explicit_sireum_home', e)]
    key = 'CODEX_BIN' if name == 'codex' else 'SIREUM_BIN'
    if e.get(key):
        return [path_record(name, e[key], 'environment_'+key, e)]
    if name == 'sireum' and e.get('SIREUM_HOME'):
        return [path_record(name, str(Path(e['SIREUM_HOME']).expanduser()/'bin'/('sireum.bat' if os.name=='nt' else 'sireum')), 'environment_SIREUM_HOME', e)]
    old = (saved or {}).get('tools', {}).get(name)
    if old and old.get('path'):
        record = path_record(name, old['path'], 'saved_selection', e)
        record['expected_sha256'] = old.get('sha256')
        if name == 'sireum':
            record['expected_jar_sha256'] = old.get('jar_sha256')
        return [record]
    candidates = [(p, 'PATH') for p in _from_path(name, e)]
    base = prefix or h/'.local/share/inspecta-scp-handoff'
    if name == 'codex':
        for p in (h/'.local/bin/codex', h/'bin/codex'):
            if p.is_file(): candidates.append((str(p), 'user_local'))
        if (base/'codex').exists():
            for p in sorted((base/'codex').glob('*/node_modules/.bin/codex'), reverse=True):
                if p.is_file(): candidates.append((str(p), 'managed_user_local'))
    else:
        roots = [h/'Applications/Sireum', h/'Sireum', h/'provers/Sireum']
        if e.get('PROVERS_DIR'): roots.insert(0, Path(e['PROVERS_DIR']).expanduser()/'Sireum')
        for root in roots:
            for p in (root/'bin/sireum', root/'bin/sireum.bat'):
                if p.is_file(): candidates.append((str(p), 'known_sireum_home'))
    records, seen = [], set()
    for value, source in candidates:
        record = path_record(name, value, source, e)
        if record['real_path'] not in seen:
            seen.add(record['real_path']); records.append(record)
    return records

def discover_downloads(roots: list[Path], max_entries: int = 2000) -> list[dict[str, str]]:
    """Only explicitly requested directories, shallow/bounded scan; never execute results."""
    found, inspected = [], 0
    for root in roots:
        root = root.expanduser().resolve()
        if not root.is_dir():
            continue
        folders = [root]
        for depth in range(3):
            children = []
            for folder in folders:
                try:
                    for p in folder.iterdir():
                        inspected += 1
                        if inspected > max_entries: return found
                        if p.is_symlink(): continue
                        if p.is_dir() and depth < 2: children.append(p)
                        if p.is_file() and any(x in p.name.lower() for x in ('codex', 'sireum')):
                            found.append({'path': str(p), 'status': 'CANDIDATE_ONLY_SELECT_EXPLICITLY', 'executed': False})
                except PermissionError:
                    continue
            folders = children
    return found

def probe_command(command: list[str], *, env: Mapping[str, str] | None = None, timeout: int = 15) -> dict:
    """Run bounded local --help/version probes outside the user's project directory."""
    try:
        with tempfile.TemporaryDirectory(prefix='scp-tool-probe-') as cwd:
            r = subprocess.run(command, cwd=cwd, env=clean_env(env), capture_output=True,
                               text=True, errors='replace', timeout=timeout, check=False)
        return {'command': command, 'returncode': r.returncode, 'output': (r.stdout+r.stderr)[:16000]}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {'command': command, 'returncode': None, 'output': str(exc), 'error': type(exc).__name__}

def parsed_codex_version(text: str) -> str | None:
    match = re.search(r'(?<![\d.])(\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?)(?![\d.])', text)
    return match.group(1) if match else None

def version_matches(actual: str | None, expected: str) -> bool:
    if actual is None: return False
    # Default family does not quietly admit alpha/beta builds.
    if '-' in actual and '-' not in expected: return False
    return fnmatch.fnmatchcase(actual, expected)

def validate_codex(record: dict, expected: str = DEFAULT_CODEX_VERSION, *,
                   runner=probe_command, env: Mapping[str, str] | None = None) -> dict:
    r = dict(record)
    if not r['exists'] or not r['executable']:
        return {**r, 'status':'BLOCKED', 'reason':'Selected executable is missing/not executable; no automatic replacement.'}
    r['sha256'] = digest(Path(r['real_path']))
    if r.get('expected_sha256') and r['expected_sha256'] != r['sha256']:
        return {**r, 'status':'BLOCKED', 'reason':'Saved executable changed. Review and explicitly select the new identity.'}
    version = runner([r['path'], '--version'], env=env)
    actual = parsed_codex_version(version['output'])
    r.update(version=actual, version_output=version['output'].strip(), expected_version=expected,
             probes=[version], probe='COMPLETED')
    if version['returncode'] != 0 or not version_matches(actual, expected):
        return {**r, 'status':'BLOCKED', 'reason':f'Expected user-selected Codex {expected}; actual output {version["output"].strip()!r}. No download or substitution.'}
    required = [(['--help'], ['--sandbox','--model','--ask-for-approval','--cd','--config']),
                (['exec','--help'], ['--json','--output-last-message','--sandbox','--model','--cd','--config'])]
    for args, flags in required:
        output = runner([r['path'], *args], env=env); r['probes'].append(output)
        missing = [flag for flag in flags if flag not in output['output']]
        if output['returncode'] != 0 or missing:
            return {**r, 'status':'BLOCKED', 'reason':'Required CLI help/flags unavailable: '+', '.join(missing)+'. Inspect this binary; do not reinstall automatically.'}
    return {**r, 'status':'REUSE_CLI_READY', 'reason':'Requested version and required CLI surface passed local probes.',
            'authentication':'NOT_CHECKED', 'astra_access':'NOT_CHECKED', 'engineering_smoke_tests':'NOT_RUN'}

def choose_codex(records: list[dict], expected: str=DEFAULT_CODEX_VERSION, **kwargs) -> tuple[dict | None, list[dict]]:
    checked=[]
    for record in records:
        r=validate_codex(record, expected, **kwargs); checked.append(r)
        if r['status']=='REUSE_CLI_READY': return r, checked
    return None, checked

def inspect_sireum(record: dict, *, allow_probe: bool=False, runner=probe_command,
                   env: Mapping[str, str] | None=None) -> dict:
    r=dict(record); path=Path(r['real_path'])
    root = path.parent.parent if path.parent.name == 'bin' else None
    r['home'] = str(root) if root else None
    jar = root/'bin/sireum.jar' if root else None
    build = root/'bin/build.cmd' if root else None
    r.update(jar_present=bool(jar and jar.is_file()), source_checkout_present=bool(build and build.is_file()),
             engineering_smoke_tests='NOT_RUN', required_action='Run selected-project KSU smoke checks; reuse if they pass.')
    if not r['exists'] or not r['executable']:
        return {**r, 'status':'BLOCKED', 'reason':'Preserve the requested home/path. Resolve missing launcher/permissions; do not replace it.'}
    r['sha256']=digest(path)
    if jar and jar.is_file(): r['jar_sha256']=digest(jar)
    for expected, actual in [('expected_sha256','sha256'), ('expected_jar_sha256','jar_sha256')]:
        if r.get(expected) and r[expected] != r.get(actual):
            return {**r,'status':'BLOCKED','reason':'Saved Sireum identity changed; review before reuse.'}
    if root and not r['jar_present']:
        return {**r, 'status':'PRESERVE_NEEDS_BOOTSTRAP_REVIEW', 'probe':'NOT_RUN',
                'reason':'No bin/sireum.jar. Do not invoke a potentially auto-bootstrapping launcher or replace this checkout.'}
    if not allow_probe:
        return {**r, 'status':'REUSE_CANDIDATE_NEEDS_SMOKE_TESTS', 'probe':'NOT_RUN'}
    e=dict(os.environ if env is None else env)
    if root: e['SIREUM_HOME']=str(root)
    probes=[runner([r['path'],'--version'], env=e), runner([r['path'],'hamr','--help'], env=e)]
    r.update(probes=probes, probe='COMPLETED', version_output=probes[0]['output'].strip())
    if any(p['returncode'] != 0 for p in probes) or 'sysml' not in probes[1]['output'].lower():
        return {**r, 'status':'BLOCKED', 'reason':'CLI/HAMR probe failed. Diagnose; preserve existing installation.'}
    return {**r,'status':'CLI_PROBED_PROJECT_VALIDATION_REQUIRED',
            'reason':'Version and HAMR help checked; SysML, Logika, solver and target smoke tests still required.'}

def save_selection(path: Path, tools: dict[str, dict], expected_version: str=DEFAULT_CODEX_VERSION) -> dict:
    previous=read_selection(path) if path.exists() else {}
    data={'record_type':'LOCAL_TOOL_SELECTION','record_version':'2.1',
          'updated_at':datetime.now(timezone.utc).isoformat(),
          'policy':'REUSE_EXISTING_FIRST_NO_AUTOMATIC_UPGRADE','codex_user_label':DEFAULT_LABEL,
          'codex_expected_version':expected_version,
          'tools':{**previous.get('tools', {}), **tools},
          'notes':['Not an engineering compatibility lock or a trusted-publisher signature.',
                   'Missing/incompatible tools are not permission to replace installed binaries.',
                   'No credentials or user authentication files are stored.']}
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.is_symlink(): raise ValueError('Refusing symlink selection file')
    fd,tmp=tempfile.mkstemp(prefix='.selection-',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(data,f,indent=2); f.write('\n')
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
    return data

def environment_for(tools: dict[str, dict], env: Mapping[str,str] | None=None) -> dict[str,str]:
    e=dict(os.environ if env is None else env)
    if tools.get('codex', {}).get('path'): e['CODEX_BIN']=tools['codex']['path']
    sireum=tools.get('sireum', {})
    if sireum.get('path'):
        e['SIREUM_BIN']=sireum['path']
        if sireum.get('home'): e['SIREUM_HOME']=sireum['home']
        else: e.pop('SIREUM_HOME', None)  # Do not mismatch an explicit standalone launcher and ambient home.
    # These are child-process changes only. No global PATH/shell files are edited.
    return e
