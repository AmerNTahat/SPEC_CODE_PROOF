#!/usr/bin/env python3
"""Plan (default) or clone approved public source repositories into a separate review directory."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys

SOURCES={
    "INSPECTA-Spec-Code-Proof-Copilot":"https://github.com/loonwerks/INSPECTA-Spec-Code-Proof-Copilot.git",
    "sysmlv2-models":"https://github.com/santoslab/sysmlv2-models.git",
    "sysml-aadl-libraries":"https://github.com/santoslab/sysml-aadl-libraries.git",
    "isolette-artifacts":"https://github.com/santoslab/isolette-artifacts.git",
    "INSPECTA-models":"https://github.com/loonwerks/INSPECTA-models.git",
    "HAMR-agent-configuration-experiments":"https://github.com/santoslab/HAMR-agent-configuration-experiments.git",
    "hamr-tutorials":"https://github.com/santoslab/hamr-tutorials.git",
}

def run(git: str, args: list[str], timeout: int=300) -> str:
    result=subprocess.run([git,*args],capture_output=True,text=True,timeout=timeout,check=False)
    if result.returncode:
        raise RuntimeError(f"Git operation failed with status {result.returncode}; inspect the local checkout/network permissions.")
    return result.stdout.strip()

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--destination',type=Path,required=True)
    p.add_argument('--only',nargs='+',choices=sorted(SOURCES),help='Acquire only named repositories; default all listed sources.')
    p.add_argument('--apply',action='store_true',help='Permit network clones into new directories. Existing clones are inspected, never reset or updated.')
    args=p.parse_args(); selected={k:v for k,v in SOURCES.items() if not args.only or k in args.only}; raw_dest=args.destination.expanduser()
    if raw_dest.is_symlink():
        print('BLOCKED: destination may not be a symlink.',file=sys.stderr); return 2
    dest=raw_dest.resolve()
    if not args.apply:
        print(json.dumps({'mode':'PLAN_ONLY','destination':str(dest),'sources':selected,'changes_performed':False},indent=2)); return 0
    git=shutil.which('git')
    if not git:
        print('BLOCKED: git not installed; resolve via approved host setup.',file=sys.stderr); return 2
    if dest.is_symlink():
        print('BLOCKED: destination may not be a symlink.',file=sys.stderr); return 2
    dest.mkdir(parents=True,exist_ok=True)
    records=[]
    try:
        for name,url in selected.items():
            target=dest/name
            if target.is_symlink(): raise RuntimeError('Refusing source symlink.')
            if not target.exists():
                run(git,['clone','--depth','1','--no-tags','--',url,str(target)])
            else:
                if not (target/'.git').exists(): raise RuntimeError(f'{name} exists but is not an ordinary checkout.')
                origin=run(git,['-C',str(target),'remote','get-url','origin'],30)
                if origin.rstrip('/').removesuffix('.git') != url.removesuffix('.git'):
                    raise RuntimeError(f'{name} has a different origin; existing directory preserved.')
            records.append({'repository':url,'path':str(target),'commit':run(git,['-C',str(target),'rev-parse','HEAD'],30),
                            'dirty':bool(run(git,['-C',str(target),'status','--porcelain'],30))})
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        receipt=dest/f'source-receipt-{stamp}.json'
        value={'observed_at':stamp,'sources':records,'note':'Source acquisition only. Scripts/submodules/dependencies not executed; no claims of validation or source isolation.'}
        with receipt.open('x') as f: json.dump(value,f,indent=2); f.write('\n')
        print(json.dumps({'receipt':str(receipt),'sources':records},indent=2))
    except (OSError,RuntimeError,subprocess.TimeoutExpired) as exc:
        print(f'Source preparation stopped: {exc}',file=sys.stderr); return 1
    return 0
if __name__=='__main__': raise SystemExit(main())
