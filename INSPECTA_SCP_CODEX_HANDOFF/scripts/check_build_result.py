#!/usr/bin/env python3
"""Check a post-build receipt's file identities. Not independent proof or code trust."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

def check(repo:Path)->dict:
    repo=repo.resolve();p=repo/'.scp-workbench'/'BUILD_RESULT.json'
    if not p.is_file():return {'ok':False,'errors':['BUILD_RESULT.json not present; build/demo not yet certified by the implementation workflow.']}
    data=json.loads(p.read_text());errors=[]
    if data.get('status')!='ready':errors.append('Build status is not ready: '+str(data.get('status')))
    if data.get('live_demo_status')!='completed':errors.append('Live demo has not completed')
    evidence=data.get('evidence',[])
    if not evidence:errors.append('No evidence references')
    for item in evidence:
        path=repo/item['path']
        try:
            path.resolve().relative_to(repo)
            if path.is_symlink() or not path.is_file():raise ValueError('Missing/unsafe evidence')
            if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Stale evidence hash')
        except (OSError,ValueError) as exc:errors.append(item['path']+': '+str(exc))
    exe=data.get('cli_executable')
    if not exe:errors.append('No CLI executable')
    else:
        try:
            ep=repo/exe;ep.resolve().relative_to(repo)
            if not ep.is_file():errors.append('CLI executable not found')
        except ValueError:errors.append('CLI executable must be within repository')
    return {'ok':not errors,'errors':errors,'status':data.get('status'),'live_demo_status':data.get('live_demo_status'),
            'scope':'Checks receipt/linked-file identities, not independent truth of engineering claims or authenticity of signer.'}
def main()->int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path,required=True);a=p.parse_args()
    try:r=check(a.repo);print(json.dumps(r,indent=2));return 0 if r['ok'] else 1
    except (OSError,ValueError,KeyError) as exc:print(f'BLOCKED: {exc}',file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
