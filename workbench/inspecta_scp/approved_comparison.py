"""Apply only exact, human-reviewed candidate property additions to a graph projection."""
import copy,json
from pathlib import Path
from .approvals import Approvals
from .config import PolicyError
from .storage import sha_file
from .graph_equivalence import graph_from_air,isomorphic

def approved_scope(store,approval_id):
    approval=Approvals(store).get(approval_id);subject=approval['subject']
    if approval['action']!='approve_architecture' or approval['status']!='APPROVED' or subject.get('kind')!='engineering_proposal':
        raise PolicyError('Current exact architecture-adaptation approval required')
    if sha_file(subject['artifact'])!=subject['sha256']:raise PolicyError('Approved comparison proposal changed')
    return json.loads(subject['proposal'])

def compare(store,result,values,approval_id):
    proposals=approved_scope(store,approval_id);ancestor=result;ids=set()
    while ancestor['id'] not in ids:
        ids.add(ancestor['id'])
        if not ancestor.get('parent_result_id'):break
        ancestor=store.read_record('development_result',ancestor['parent_result_id'])
    matches=[p for p in proposals if p['result_id'] in ids]
    if len(matches)!=1:raise PolicyError('Adaptation approval does not cover this candidate lineage')
    graphs=[graph_from_air(v) for v in values];changes=matches[0]['exact_candidate_additions']
    for change in changes:
        attrs=graphs[1]['nodes'].get(change['node']);prop=change['property']
        if attrs is None or prop not in attrs.get('properties',[]):raise PolicyError('Approved exact property addition no longer matches')
        attrs['properties'].remove(prop)
    result=isomorphic(*graphs)
    return result,{'approval_id':approval_id,'checker_sha256':sha_file(Path(__file__)),
        'exact_candidate_additions':copy.deepcopy(changes),'scope':'Only approved implementation additions omitted from this comparison projection; raw strict comparison retained. No timing or behavioral waiver.'}
