#!/usr/bin/env python3
"""Validate normalized measurement records and export local DASC-style plots.
This is NOT a HAMR verifier or raw-log parser. It trusts declared normalized gate records;
the Workbench must establish their provenance/currentness using trusted adapters.
"""
from __future__ import annotations
import argparse, csv, html, json, math, sys
from pathlib import Path

def number(x, field:str):
    if x is None:return None
    if isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or x<0:raise ValueError(f'Invalid {field}')
    return x

def calculate(run:dict)->dict:
    if run.get('measurement_kind') not in ['live','historical','synthetic']:raise ValueError('measurement_kind is required')
    targets=run['target_unit_ids']
    if not targets or len(set(targets))!=len(targets):raise ValueError('Target IDs must be nonempty and unique')
    records=run.get('unit_results',[])
    ids=[x['unit_id'] for x in records]
    if len(set(ids))!=len(ids) or not set(ids)<=set(targets):raise ValueError('Duplicate or unregistered unit results')
    verified=[];accepted=[]
    for unit in records:
        formal=unit.get('formal_gates',[])
        current=unit.get('artifact_revision')==run.get('artifact_revision') and unit.get('evidence_current') is True
        if current and formal and all(g.get('status')=='PASS' and g.get('evidence_ref') for g in formal):
            verified.append(unit['unit_id'])
            extras=unit.get('acceptance_gates',[])
            if extras and all(g.get('status')=='PASS' and g.get('evidence_ref') for g in extras):accepted.append(unit['unit_id'])
    wall=number(run.get('wall_seconds'),'wall_seconds')
    usage=run.get('usage',{})
    inp=number(usage.get('input_total'),'input_total');cached=number(usage.get('cached_input'),'cached_input');out=number(usage.get('output_total'),'output_total')
    if inp is not None and cached is not None and cached>inp:raise ValueError('Cached input cannot exceed total input')
    total=inp+out if inp is not None and out is not None else None
    cost=number(run.get('cost_usd'),'cost_usd');n=len(verified)
    project=run.get('project_gates',[])
    success=len(accepted)==len(targets) and bool(project) and all(g.get('status')=='PASS' and g.get('evidence_ref') for g in project)
    return {'run_id':run['run_id'],'measurement_kind':run['measurement_kind'],'benchmark_id':run['benchmark_id'],
        'policy_id':run['policy_id'],'target_count':len(targets),'verified_count':n,'accepted_count':len(accepted),
        'verified_ids':sorted(verified),'coverage':n/len(targets),'wall_seconds':wall,'total_tokens':total,
        'cached_input_tokens':cached,'uncached_input_tokens':inp-cached if inp is not None and cached is not None else None,
        'output_tokens':out,'cost_usd':cost,'verified_per_minute':n/(wall/60) if wall else None,
        'tokens_per_verified_unit':total/n if n and total is not None else None,
        'dollars_per_verified_unit':cost/n if n and cost is not None else None,'end_to_end_success':success,
        'scope':'Normalized-record accounting only. Not independent engineering verification.'}

def comparable(a:dict,b:dict)->bool:
    keys=['benchmark_id','policy_id','model_profile','toolchain_profile','operation','budget_policy']
    return all(a.get(k) is not None and a.get(k)==b.get(k) for k in keys) and set(a['target_unit_ids'])==set(b['target_unit_ids']) and a['measurement_kind']==b['measurement_kind']

def export(runs:list[dict],output:Path,plots:bool=True)->dict:
    output=output.resolve()
    if output.exists() and any(output.iterdir()):raise ValueError('Use a new/empty output directory; existing evidence is not overwritten')
    output.mkdir(parents=True,exist_ok=True)
    metrics=[calculate(r) for r in runs]
    (output/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
    (output/'source-records.json').write_text(json.dumps(runs,indent=2)+'\n')
    columns=[k for k in metrics[0] if k!='verified_ids']
    with (output/'metrics.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=columns,extrasaction='ignore');writer.writeheader();writer.writerows(metrics)
    figures=[]
    if plots:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        for field,title,ylabel in [
            ('coverage','Verification coverage','Fraction of registered units'),
            ('verified_per_minute','Verified throughput','Units per wall-clock minute'),
            ('total_tokens','Context-processed tokens','Tokens (input total + output total)'),
            ('tokens_per_verified_unit','Tokens per verified unit','Tokens / verified unit'),
            ('cost_usd','Total run cost','USD under recorded pricing basis'),
            ('dollars_per_verified_unit','Dollars per verified unit','USD / verified unit')]:
            fig,ax=plt.subplots(figsize=(8,4.8));xs=list(range(len(metrics)))
            vals=[m[field] for m in metrics]
            ax.bar([i for i,v in enumerate(vals) if v is not None],[v for v in vals if v is not None])
            ax.set_xticks(xs,[m['run_id'] for m in metrics],rotation=15,ha='right')
            for i,v in enumerate(vals):
                if v is None:ax.text(i,0,'Undefined / missing',rotation=90,ha='center',va='bottom')
            ax.set_ylabel(ylabel);ax.set_title(title);ax.grid(axis='y',alpha=.25)
            kinds='/'.join(sorted({m['measurement_kind'].upper() for m in metrics}))
            fig.text(.01,.01,kinds+' DATA — normalized-record visualization, not proof verification',fontsize=8)
            fig.tight_layout(rect=[0,.04,1,1])
            for ext in ['png','svg']:fig.savefig(output/f'{field}.{ext}',dpi=160)
            plt.close(fig);figures.append(field+'.png')
    compatible=all(comparable(runs[0],r) for r in runs[1:])
    body=['<h1>SCP evaluation report</h1>','<p>Measurement kinds: '+html.escape(', '.join(sorted({m['measurement_kind'] for m in metrics})))+'</p>',
          '<p>Comparability metadata: '+('matched' if compatible else 'NOT MATCHED — no savings inference')+'. Partial verified subsets still require identity-aware interpretation.</p>',
          '<p>These calculations do not establish correctness of contracts or raw verifier output. See source records and evidence.</p>']
    for m in metrics:
        body.append('<section><h2>'+html.escape(m['run_id'])+'</h2>')
        for k,v in m.items():body.append('<p><strong>'+html.escape(k)+':</strong> '+html.escape(str(v))+'</p>')
        body.append('</section>')
    body += [f'<figure><img style="max-width:100%" src="{x}" alt="{html.escape(x)}"></figure>' for x in figures]
    body.append('<p><a href="metrics.json">Metrics</a> | <a href="source-records.json">Source records</a> | <a href="metrics.csv">CSV</a></p>')
    (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>SCP evaluation</title><style>body{font:16px system-ui;max-width:1000px;margin:40px auto;padding:20px}section{border-top:1px solid #ccc}</style>'+''.join(body))
    return {'output':str(output),'records':len(metrics),'figures':len(figures),'measurement_kinds':sorted({m['measurement_kind'] for m in metrics}),'comparability_metadata_matched':compatible}

def main()->int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--no-plots',action='store_true');a=p.parse_args()
    try:
        data=json.loads(a.input.read_text());runs=data if isinstance(data,list) else data['runs']
        if not runs:raise ValueError('No runs supplied')
        print(json.dumps(export(runs,a.output,not a.no_plots),indent=2));return 0
    except (OSError,ValueError,KeyError,ImportError,TypeError) as exc:print(f'BLOCKED: {exc}',file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
