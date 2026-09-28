#!/usr/bin/env python3
"""Plan/apply the two goal updates with content preconditions and recoverable originals.
No Git reset, commit, push, model call, or toolchain install. Apply is explicit.
"""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, sys, tempfile, uuid
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
TARGET = Path('SCP-extention-artificats/isolette_io_extnded')
NAMES = ('goal_learn.txt', 'goal_user.txt')

def digest(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None

def safe_target(repo: Path, rel: Path) -> Path:
    if rel.is_absolute() or '..' in rel.parts: raise ValueError('Unsafe target path')
    p = repo / rel
    p.resolve().relative_to(repo)
    q=p
    while q != repo:
        if q.is_symlink(): raise ValueError(f'Symlink target is not allowed: {q}')
        q=q.parent
    if p.exists() and not p.is_file(): raise ValueError(f'Not a file: {p}')
    return p

def plan(repo: Path, package: Path=PACKAGE) -> dict:
    repo=repo.resolve()
    if not repo.is_dir(): raise ValueError('Repository directory does not exist')
    if not (repo/'.git').exists(): raise ValueError('Expected a Git repository/worktree root')
    entries=[]
    for name in NAMES:
        src=package/'workflow_goals'/name
        if not src.is_file() or src.is_symlink(): raise ValueError(f'Missing/unsafe source: {src}')
        target=safe_target(repo,TARGET/name)
        entries.append({'name':name,'target':(TARGET/name).as_posix(),
                        'before_sha256':digest(target),'after_sha256':digest(src),
                        'action':'unchanged' if digest(target)==digest(src) else ('replace' if target.exists() else 'create')})
    return {'format':'scp-goal-install-plan-v2','repository':str(repo),'entries':entries,
            'warning':'Review the diff and local edits before explicitly applying. No other files are replaced.'}

def apply(repo: Path, approved: dict, package: Path=PACKAGE) -> dict:
    repo=repo.resolve()
    current=plan(repo,package)
    if approved.get('format')!=current['format'] or approved.get('repository')!=str(repo):
        raise ValueError('Plan does not match the repository')
    if approved.get('entries')!=current['entries']:
        raise ValueError('Files or source goals changed since planning; regenerate and approve the plan')
    changed=[x for x in current['entries'] if x['action']!='unchanged']
    if not changed: return {'status':'unchanged','changed':[]}
    backup=repo/'.scp-handoff'/'goal-backups'/uuid.uuid4().hex
    backup.resolve().relative_to(repo)
    if any(x.is_symlink() for x in [repo/'.scp-handoff',repo/'.scp-handoff'/'goal-backups']):
        raise ValueError('Backup root must not be a symlink')
    backup.mkdir(parents=True,exist_ok=False)
    replaced=[]
    try:
        # Validate all preconditions before replacing either file.
        for entry in changed:
            p=safe_target(repo,Path(entry['target']))
            if p.exists(): shutil.copy2(p,backup/entry['name'])
        for entry in changed:
            p=safe_target(repo,Path(entry['target']))
            if digest(p)!=entry['before_sha256']: raise ValueError('Concurrent edit detected')
            p.parent.mkdir(parents=True,exist_ok=True)
            fd,tmp=tempfile.mkstemp(prefix='.goal-',dir=p.parent)
            try:
                with os.fdopen(fd,'wb') as f: f.write((package/'workflow_goals'/entry['name']).read_bytes())
                os.chmod(tmp,p.stat().st_mode & 0o777 if p.exists() else 0o644)
                os.replace(tmp,p); replaced.append(entry)
            finally:
                if os.path.exists(tmp): os.unlink(tmp)
    except Exception:
        # Recovery only for our exact installed content; never overwrite another new edit.
        for entry in reversed(replaced):
            p=repo/entry['target']
            if digest(p)==entry['after_sha256']:
                saved=backup/entry['name']
                if saved.exists(): shutil.copy2(saved,p)
                else: p.unlink()
        raise
    receipt={'status':'applied','changed':changed,'backup_directory':str(backup),
             'scope':'Two workflow goals only; not an application installation or validation.'}
    (backup/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__); s=p.add_subparsers(dest='cmd',required=True)
    a=s.add_parser('plan'); a.add_argument('--repo',type=Path,required=True); a.add_argument('--output',type=Path,required=True)
    a=s.add_parser('apply'); a.add_argument('--repo',type=Path,required=True); a.add_argument('--plan',type=Path,required=True)
    args=p.parse_args()
    try:
        if args.cmd=='plan':
            result=plan(args.repo)
            args.output.parent.mkdir(parents=True,exist_ok=True)
            with args.output.open('x',encoding='utf-8') as f: json.dump(result,f,indent=2); f.write('\n')
        else: result=apply(args.repo,json.loads(args.plan.read_text()))
        print(json.dumps(result,indent=2)); return 0
    except (OSError,ValueError,KeyError) as exc: print(f'BLOCKED: {exc}',file=sys.stderr); return 2
if __name__=='__main__': raise SystemExit(main())
