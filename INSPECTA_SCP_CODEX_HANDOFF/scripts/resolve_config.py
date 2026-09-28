#!/usr/bin/env python3
"""Resolve explicit run overrides without executing a model or claiming readiness.
Starter resolver to integrate into the single Workbench service. Never reads defaults from prose.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def merge(base:dict,updates:dict)->dict:
    result=copy.deepcopy(base)
    for k,v in updates.items():
        result[k]=merge(result[k],v) if isinstance(v,dict) and isinstance(result.get(k),dict) else copy.deepcopy(v)
    return result

def resolve(defaults:dict,profile:dict|None=None,overrides:dict|None=None)->dict:
    config=merge(merge(defaults,profile or {}),overrides or {})
    budget=config['budget']
    for key in ['wall_seconds','aggregate_model_tokens']:
        if not isinstance(budget[key],int) or isinstance(budget[key],bool) or budget[key]<=0:raise ValueError(f'{key} must be a positive integer')
    for key in ['repairs_per_issue','repairs_per_run']:
        if budget[key]<0:raise ValueError('Repair limits cannot be negative')
    if not 0<=budget['final_validation_time_reserve']<1:raise ValueError('Invalid final validation reserve')
    op=config.get('task_operation','auto')
    if op=='create-system' and not config.get('creation_authorized',False):raise ValueError('Creation needs explicit authorization')
    if config.get('online_embedding_fallback'):raise ValueError('No automatic online embeddings')
    if config.get('model',{}).get('family')!='gpt':raise ValueError('GPT-only model policy')
    a=config.get('learning_materials');b=config.get('development_validation')
    if a and b:
        pa=Path(a).expanduser().resolve();pb=Path(b).expanduser().resolve()
        if pa==pb or pa in pb.parents or pb in pa.parents:raise ValueError('Learning/development directories overlap')
    missing=[k for k in ['project_config','toolchain_lock'] if not config.get(k)]
    if not config.get('model',{}).get('resolved_model_id'):missing.append('model.resolved_model_id')
    if config.get('mode')=='user' and not config.get('rule_release'):missing.append('rule_release')
    # This helper cannot prove source/authorization/tool readiness: always leave a draft for controller preflight.
    config['readiness']='draft'
    encoded=json.dumps(config,sort_keys=True,separators=(',',':')).encode()
    return {'format':'scp-resolved-request-v2','config':config,'config_sha256':hashlib.sha256(encoded).hexdigest(),
            'precedence':['defaults','saved_profile','explicit_overrides','controller_preflight_pending'],
            'missing_values':missing,'execution_readiness':'NOT_ASSESSED','model_calls':0}
def main()->int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mode',choices=['learning','user'],required=True)
    p.add_argument('--profile',type=Path);p.add_argument('--overrides',type=Path);p.add_argument('--time-limit-seconds',type=int);p.add_argument('--token-limit',type=int)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    try:
        defaults=json.loads((ROOT/'configs'/f'{a.mode}.example.json').read_text())
        overrides=json.loads(a.overrides.read_text()) if a.overrides else {}
        if a.time_limit_seconds is not None: overrides.setdefault('budget',{})['wall_seconds']=a.time_limit_seconds
        if a.token_limit is not None:overrides.setdefault('budget',{})['aggregate_model_tokens']=a.token_limit
        result=resolve(defaults,json.loads(a.profile.read_text()) if a.profile else {},overrides)
        a.output.parent.mkdir(parents=True,exist_ok=True)
        with a.output.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
        print(json.dumps({'output':str(a.output),'config_sha256':result['config_sha256'],'readiness':'DRAFT'},indent=2));return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:print(f'BLOCKED: {exc}',file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
