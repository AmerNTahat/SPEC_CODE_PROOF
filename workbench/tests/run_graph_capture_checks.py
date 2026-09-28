"""Offline tests of graph comparison on the actual saved live HAMR captures.
Mutations are explicit evaluator fixtures, not live generated models or proofs.
"""
import copy
import json
from pathlib import Path
from inspecta_scp.controller import Controller
from inspecta_scp.development import Development
from inspecta_scp.graph_equivalence import compare_architectures,graph_from_air


def main():
    root=Path('reports/demo');c=Controller('.scp-workbench/app');checks=[]
    for target in ['producer-consumer','isolette']:
        original=json.loads((root/(target+'-refined-rule-validation.json')).read_text())
        result=Development(c).compare_graph(original['result']['id'])
        (root/(target+'-graph-assessment.json')).write_text(json.dumps(result,indent=2)+'\n')
        checks.append({'case':target+' real saved comparison','status':result['graph']['status'],'assessment_id':result['id']})
        if target!='producer-consumer':continue
        g=next(x for x in original['reference_run']['result']['gates'] if x['gate']=='architecture_capture')
        value=c.store.load_object(c.store.read_record('architecture_snapshot',g['snapshot_id'])['normalized'])
        vertices=graph_from_air(value)['nodes'];names={tuple(k.split('/',1)[1].split('::')) for k in vertices if '/#' not in k and '#connection:' not in k}
        def rename(x):
            if isinstance(x,dict):
                if x.get('type')=='Name' and tuple(x.get('name',[])) in names:
                    x['name']=['renamed_'+part for part in x['name']]
                else:
                    for v in x.values():rename(v)
            elif isinstance(x,list):
                for v in x:rename(v)
        renamed=copy.deepcopy(value);rename(renamed)
        answer=compare_architectures(value,renamed);assert answer['status']=='PASS',answer
        checks.append({'case':'Consistent component/port/endpoint/binding renaming','status':'PASS','result':answer})
        reversed_wire=copy.deepcopy(value)
        connection=next(iter(reversed_wire['models'].values()))['components'][0]['connections'][0]
        connection['src'],connection['dst']=connection['dst'],connection['src']
        answer=compare_architectures(value,reversed_wire);assert answer['status']=='FAIL',answer
        checks.append({'case':'Reversed actual connection rejected','status':'PASS','result':answer})
        wrong_path=copy.deepcopy(value)
        connection=next(iter(wrong_path['models'].values()))['components'][0]['connectionInstances'][0]
        connection['connectionRefs'].reverse()
        answer=compare_architectures(value,wrong_path);assert answer['status']=='FAIL',answer
        checks.append({'case':'Reversed resolved connection path rejected','status':'PASS','result':answer})
        wrong_binding=copy.deepcopy(value)
        def replace_binding(x):
            if isinstance(x,dict):
                if x.get('type')=='ReferenceProp':x['value']['name'][-1]='prod'
                else:
                    for v in x.values():replace_binding(v)
            elif isinstance(x,list):
                for v in x:replace_binding(v)
        replace_binding(wrong_binding)
        answer=compare_architectures(value,wrong_binding);assert answer['status']=='FAIL',answer
        checks.append({'case':'Incorrect processor binding rejected','status':'PASS','result':answer})
    out={'status':'PASS','scope':'Offline checks on actual saved AIR plus explicit mutated evaluator fixtures; no new model/tool runs','model_calls':0,'checks':checks}
    Path('reports/build/graph-capture-checks.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'status':'PASS','checks':[(x['case'],x['status']) for x in checks]}));c.close()

if __name__=='__main__':main()
