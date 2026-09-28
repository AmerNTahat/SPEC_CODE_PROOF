#!/usr/bin/env python3
"""Record/print a milestone update. Development reporting, not verification proof."""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, os, sys
from pathlib import Path

FIELDS=('achieved','in_progress','remaining','blockers')

def record(repo: Path, event: dict) -> dict:
    repo=repo.resolve(); out=repo/'reports'/'build'
    out.resolve().relative_to(repo)
    if any(p.is_symlink() for p in [repo/'reports',out]): raise ValueError('Unsafe report path')
    if event['state']=='completed' and not event.get('evidence'): raise ValueError('Completion requires evidence file references')
    evidence=[]
    for rel in event.get('evidence',[]):
        path=repo/rel; path.resolve().relative_to(repo)
        if not path.is_file() or path.is_symlink(): raise ValueError(f'Missing/unsafe evidence: {rel}')
        evidence.append({'path':path.relative_to(repo).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    result={**event,'evidence':evidence,'recorded_at':dt.datetime.now(dt.timezone.utc).isoformat(),
            'scope':'Development progress; evidence identity checked, claims not independently verified.'}
    lines=[f"## {event['milestone']} — {event['state']}"]
    for key in FIELDS:
        lines += ['',key.replace('_',' ').capitalize()+':'] + (event.get(key) or ['Not reported.'])
    lines+=['','Evidence:']+[x['path']+' — '+x['sha256'] for x in evidence]
    lines+=['','Budget:',event.get('budget','Usage not reported.'),'']
    text='\n'.join(lines)+'\n'
    out.mkdir(parents=True,exist_ok=True)
    lock=out/'.milestone.lock'
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    try:
        for path in [out/'milestones.jsonl',repo/'IMPLEMENTATION_PROGRESS.md']:
            if path.is_symlink(): raise ValueError('Report may not be a symlink')
        with (out/'milestones.jsonl').open('a',encoding='utf-8') as f: f.write(json.dumps(result)+'\n')
        with (repo/'IMPLEMENTATION_PROGRESS.md').open('a',encoding='utf-8') as f: f.write(text)
    finally: os.close(fd); lock.unlink()
    print(text); return result

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,required=True); p.add_argument('--milestone',required=True,choices=[f'M{i:02}' for i in range(9)])
    p.add_argument('--state',required=True,choices=['in_progress','completed','blocked','failed'])
    for k in FIELDS: p.add_argument('--'+k.replace('_','-'),dest=k,action='append',default=[])
    p.add_argument('--evidence',action='append',default=[]); p.add_argument('--budget',default='Usage not reported.')
    a=p.parse_args()
    try: record(a.repo,{k:v for k,v in vars(a).items() if k!='repo'}); return 0
    except (OSError,ValueError) as exc: print(f'BLOCKED: {exc}',file=sys.stderr); return 2
if __name__=='__main__': raise SystemExit(main())
