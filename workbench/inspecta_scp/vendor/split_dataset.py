#!/usr/bin/env python3
"""Validate manual or propose seeded family/lineage-grouped task assignments.
Operates on reviewed task metadata; never moves files or discovers semantic independence.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, math, sys
from pathlib import Path
ROLES=('learning','development','final')
def canonical_hash(value: object)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def assign(manifest:dict,strategy:str='user_assigned',fractions:list[float]|None=None,seed:str='0')->dict:
    tasks=copy.deepcopy(manifest.get('tasks',[]))
    if not tasks:raise ValueError('Task registry is empty')
    ids=[t.get('id') for t in tasks]
    if any(not isinstance(i,str) or not i for i in ids) or len(set(ids))!=len(ids):raise ValueError('Unique task IDs are required')
    parent={i:i for i in ids}
    def find(x):
        while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def union(a,b):parent[find(a)]=find(b)
    seen={}
    for t in tasks:
        if not t.get('family_id') or not t.get('lineage_id'):raise ValueError(f"Missing family/lineage for {t['id']}; review metadata first")
        keys=[('family',t['family_id']),('lineage',t['lineage_id'])]+[('hash',h) for h in t.get('content_hashes',[])]
        for key in keys:
            if key in seen: union(t['id'],seen[key])
            else:seen[key]=t['id']
    groups={}
    for t in tasks:groups.setdefault(find(t['id']),[]).append(t)
    warnings=[]
    if strategy=='user_assigned':
        for group in groups.values():
            roles={t.get('role') for t in group}
            if not roles<=set(ROLES) or len(roles)!=1:raise ValueError('Missing assignments or related tasks cross dataset roles')
    elif strategy=='propose_grouped':
        if fractions is None or len(fractions)!=3 or any(not math.isfinite(x) or x<0 for x in fractions) or not math.isclose(sum(fractions),1,abs_tol=1e-9):
            raise ValueError('Supply explicit learning/development/final fractions summing to 1')
        order=sorted(groups.values(),key=lambda g:canonical_hash([seed,sorted(t['id'] for t in g)]))
        if len(order)<sum(x>0 for x in fractions):raise ValueError('Too few independent groups for requested nonempty roles')
        counts={r:0 for r in ROLES}; targets={r:len(tasks)*fractions[i] for i,r in enumerate(ROLES)}
        for group in order:
            role=max((r for i,r in enumerate(ROLES) if fractions[i]>0), key=lambda r:(targets[r]-counts[r],-ROLES.index(r)))
            for t in group:t['role']=role
            counts[role]+=len(group)
        if any(fractions[i]>0 and counts[r]==0 for i,r in enumerate(ROLES)):raise ValueError('Grouped proposal has an empty requested role; adjust grouping/fractions')
        warnings.append('Fractions are approximate because groups remain intact; inspect membership before approving.')
    else:raise ValueError('Unknown strategy')
    result={'format':'scp-dataset-assignment-v2','strategy':strategy,'seed':seed,'source_manifest_sha256':canonical_hash(manifest),
            'tasks':sorted(tasks,key=lambda t:t['id']),'groups':sorted([sorted(t['id'] for t in g) for g in groups.values()]),
            'approval_state':'PROPOSED','warnings':warnings,'source_files_moved':False,
            'scope':'Grouping follows provided metadata; no base-model pretraining independence claim.'}
    result['proposal_sha256']=canonical_hash(result)
    return result

def approve(proposal:dict,reviewer:str)->dict:
    p=copy.deepcopy(proposal); got=p.pop('proposal_sha256',None)
    if got!=canonical_hash(p):raise ValueError('Proposal changed or digest missing')
    if not reviewer.strip():raise ValueError('Reviewer identity/record is required')
    return {'format':'scp-dataset-approval-v2','proposal_sha256':got,'reviewer':reviewer,'decision':'APPROVED',
            'scope':'Explicit local review record, not a cryptographic identity attestation. Revalidate source hashes before every run.'}
def main()->int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--strategy',choices=['user_assigned','propose_grouped','approve'],default='user_assigned')
    p.add_argument('--fractions',nargs=3,type=float);p.add_argument('--seed',default='0');p.add_argument('--reviewer')
    a=p.parse_args()
    try:
        source=json.loads(a.input.read_text())
        result=approve(source,a.reviewer or '') if a.strategy=='approve' else assign(source,a.strategy,a.fractions,a.seed)
        a.output.parent.mkdir(parents=True,exist_ok=True)
        with a.output.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
        print(json.dumps({'output':str(a.output),'state':result.get('approval_state',result.get('decision'))},indent=2));return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:print(f'BLOCKED: {exc}',file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
