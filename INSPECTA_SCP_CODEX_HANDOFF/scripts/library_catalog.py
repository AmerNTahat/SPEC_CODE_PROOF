#!/usr/bin/env python3
"""Read-only rulebook source catalog; this does NOT approve/import rules into the live app."""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path

BLOCKED={'.git','eva-results','eval_results','verification-profiles','truth-values'}
def catalog(root: Path) -> dict:
    root=root.resolve()
    if not root.is_dir(): raise ValueError('Rulebook directory is missing')
    files=[]; rules={}; skipped=[]
    for p in sorted(root.rglob('*')):
        rel=p.relative_to(root)
        if p.is_symlink() or any(x in BLOCKED or 'snapshot' in x or 'clean-profile' in x for x in rel.parts):
            skipped.append(rel.as_posix()); continue
        if not p.is_file() or p.suffix.lower() not in ['.md','.txt','.json']: continue
        text=p.read_text(encoding='utf-8',errors='replace')
        ids=sorted(set(re.findall(r'\bMR-[A-Z0-9]+(?:-[A-Z0-9]+)*\b',text)))
        item={'path':rel.as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rule_ids':ids,
              'status':'SOURCE_ONLY_PENDING_REVIEW','bytes':p.stat().st_size}
        files.append(item)
        for rid in ids: rules.setdefault(rid,[]).append(rel.as_posix())
    return {'format':'scp-library-source-catalog-v2','root':str(root),'files':files,'rule_occurrences':rules,
            'repeated_ids':{k:v for k,v in rules.items() if len(v)>1},'skipped':skipped,
            'notes':'Repeated IDs may be shared views or conflicts. Review actual records; no merge/approval was performed.',
            'model_calls':0,'files_modified':0}
def main()->int:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--root',type=Path,required=True); p.add_argument('--output',type=Path)
    a=p.parse_args()
    try:
        result=catalog(a.root); text=json.dumps(result,indent=2)+'\n'
        if a.output:
            a.output.parent.mkdir(parents=True,exist_ok=True)
            with a.output.open('x',encoding='utf-8') as f:f.write(text)
        else: print(text)
        return 0
    except (OSError,ValueError) as exc: print(f'BLOCKED: {exc}',file=sys.stderr); return 2
if __name__=='__main__':raise SystemExit(main())
