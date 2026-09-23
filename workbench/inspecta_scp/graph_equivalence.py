"""Bounded exact directed attributed multigraph isomorphism, independent of names.

This establishes only the explicitly represented structural projection. It does not
establish contract, payload-type or implementation equivalence.
"""
from collections import Counter, defaultdict
import json
import time
from .config import PolicyError

VERSION = 'hamr-directed-structure-v2'


def graph_from_air(value):
    if not value.get('models'):raise PolicyError('No instantiated models to compare')
    nodes={}; edges=[]; pending=[];connection_names={};reference_links=[];port_owners={};endpoint_checks=[]
    def add(key,attributes):
        if key in nodes:raise PolicyError('Duplicate graph identity: '+key)
        nodes[key]=attributes
    def name(obj):return '::'.join(obj['name'])
    def endpoint_key(endpoint,prefix):
        feature=endpoint.get('feature',{})
        owner=prefix+name(endpoint['component'])
        target=prefix+name(feature['value']) if feature.get('type')=='Some' else owner
        if feature.get('type')=='Some':endpoint_checks.append((target,owner))
        return target
    def props(items,owner,prefix):
        # Properties remain semantically named (standardized property keys),
        # but reference-valued properties are edges, not spelling comparisons.
        literal=[]
        property_name=None
        def transform(x,path=()):
            if isinstance(x,dict):
                if x.get('type')=='ReferenceProp':
                    if len(path)!=2 or path[0]!='propertyValues':
                        raise PolicyError('Nested reference property requires an explicit relation adapter')
                    pending.append((owner,prefix+name(x['value']),'property-reference:'+property_name))
                    return {'type':'ReferenceProp'}
                return {k:transform(v,path+(k,)) for k,v in x.items()}
            if isinstance(x,list):return [transform(v,path+(i,)) for i,v in enumerate(x)]
            return x
        for item in items:
            if item.get('appliesTo'):raise PolicyError('Property appliesTo requires an explicit graph adapter')
            property_name=name(item['name']);literal.append(transform(item))
        return sorted(literal,key=lambda x:json.dumps(x,sort_keys=True))
    def component(c,prefix,parent=None):
        key=prefix+name(c['identifier'])
        if c.get('modes') or c.get('flows'):raise PolicyError('Modes/flows require an explicit graph adapter')
        add(key,{'kind':'component','category':c['category'],'properties':props(c['properties'],key,prefix)})
        if parent:edges.append((parent,key,'contains-component'))
        for f in c['features']:
            if f.get('type')!='FeatureEnd':raise PolicyError('Unsupported graph feature')
            fk=prefix+name(f['identifier']);add(fk,{'kind':'port','category':f['category'],'direction':f['direction'],'properties':props(f['properties'],fk,prefix)})
            port_owners[fk]=key
            edges.append((key,fk,'owns-port'))
        for i,conn in enumerate(c['connections']):
            if conn.get('connectionInstances'):raise PolicyError('Separate connection-instance records require an explicit graph adapter')
            if conn['isBiDirectional'] or len(conn['src'])!=1 or len(conn['dst'])!=1:
                raise PolicyError('Bidirectional or multi-endpoint connections require an explicit graph adapter')
            ck=key+'#connection:'+str(i)
            alias=prefix+name(conn['name'])
            if alias in connection_names:raise PolicyError('Duplicate declared connection name')
            connection_names[alias]=ck
            add(ck,{'kind':'connection','category':conn['kind'],'bidirectional':conn['isBiDirectional'],'properties':props(conn['properties'],ck,prefix)})
            edges.append((key,ck,'owns-connection'))
            for label in ['src','dst']:
                for endpoint in conn[label]:
                    target=endpoint_key(endpoint,prefix)
                    pending.append((target,ck,'source') if label=='src' else (ck,target,'destination'))
        for i,conn in enumerate(c.get('connectionInstances',[])):
            if conn.get('type')!='ConnectionInstance':raise PolicyError('Unsupported resolved connection record')
            ik=key+'#resolved-connection:'+str(i)
            add(ik,{'kind':'resolved-connection','category':conn['kind'],'properties':props(conn['properties'],ik,prefix)})
            edges.append((key,ik,'owns-resolved-connection'))
            pending.append((endpoint_key(conn['src'],prefix),ik,'resolved-source'))
            pending.append((ik,endpoint_key(conn['dst'],prefix),'resolved-destination'))
            for j,ref in enumerate(conn['connectionRefs']):
                label='path-segment:'+str(j)+':parent='+str(ref['isParent'])
                reference_links.append((ik,prefix+name(ref['name']),label))
                pending.append((ik,prefix+name(ref['context']),'path-context:'+str(j)))
        for child in c['subComponents']:component(child,prefix,key)
    # Model order and model/root names do not color nodes. Prefixes only ensure
    # identity separation across independently exported instances.
    for i,model in enumerate(value['models'].values()):
        if model.get('type')!='Aadl' or not model.get('components'):raise PolicyError('Unsupported or empty architecture representation')
        prefix=str(i)+'/'
        root=prefix+'#model';add(root,{'kind':'model'})
        for c in model['components']:component(c,prefix,root)
    for a,b,label in pending:
        if a not in nodes or b not in nodes:raise PolicyError('Unresolved graph endpoint')
        edges.append((a,b,label))
    for a,b,label in reference_links:
        if b not in connection_names:raise PolicyError('Unresolved connection path segment')
        edges.append((a,connection_names[b],label))
    for target,owner in endpoint_checks:
        if port_owners.get(target)!=owner:raise PolicyError('Endpoint feature and component ownership disagree')
    return {'nodes':nodes,'edges':edges}


def isomorphic(left,right,max_states=100000,seconds=5):
    """Return an independently checkable bijection, failure, or bounded UNKNOWN."""
    started=time.monotonic();states=0
    ln,rn=left['nodes'],right['nodes'];le=Counter(map(tuple,left['edges']));re=Counter(map(tuple,right['edges']))
    base={'version':VERSION,'left_vertices':len(ln),'right_vertices':len(rn),
          'left_edges':sum(le.values()),'right_edges':sum(re.values()),'names_compared':False,
          'left_roles':dict(Counter(str(v.get('kind'))+':'+str(v.get('category',{}).get('value','')) for v in ln.values())),
          'right_roles':dict(Counter(str(v.get('kind'))+':'+str(v.get('category',{}).get('value','')) for v in rn.values()))}
    def out(status,reason,mapping=None):return {**base,'status':status,'reason':reason,'mapping':mapping,'search_states':states}
    if len(ln)!=len(rn) or sum(le.values())!=sum(re.values()):return out('FAIL','Different vertex or directed-edge counts')
    def signature(nodes,edges):
        degrees=defaultdict(Counter)
        for (a,b,label),count in edges.items():
            if a not in nodes or b not in nodes:raise PolicyError('Graph endpoint missing')
            degrees[a]['out:'+label]+=count;degrees[b]['in:'+label]+=count
        return {k:json.dumps([v,sorted(degrees[k].items())],sort_keys=True) for k,v in nodes.items()}
    ls,rs=signature(ln,le),signature(rn,re)
    if Counter(ls.values())!=Counter(rs.values()):return out('FAIL','Typed roles, properties or directed degrees differ')
    domains={k:[v for v in rn if rs[v]==ls[k]] for k in ln}
    labels={e[2] for e in le}|{e[2] for e in re};mapping={};used=set()
    def compatible(a,b):
        for label in labels:
            if le[a,a,label]!=re[b,b,label]:return False
            for x,y in mapping.items():
                if le[a,x,label]!=re[b,y,label] or le[x,a,label]!=re[y,b,label]:return False
        return True
    def search():
        nonlocal states
        states+=1
        if states>max_states or time.monotonic()-started>seconds:raise TimeoutError
        if len(mapping)==len(ln):return dict(mapping)
        choices=[(a,[b for b in domains[a] if b not in used and compatible(a,b)]) for a in ln if a not in mapping]
        a,candidates=min(choices,key=lambda x:len(x[1]))
        for b in candidates:
            mapping[a]=b;used.add(b);answer=search()
            if answer is not None:return answer
            del mapping[a];used.remove(b)
        return None
    try:witness=search()
    except (TimeoutError,RecursionError):return out('UNKNOWN','Graph search bound reached; no equivalence inferred')
    if witness is None:return out('FAIL','No consistent directed attributed graph bijection')
    if Counter((witness[a],witness[b],label) for a,b,label in left['edges'])!=re:raise PolicyError('Graph witness failed independent edge check')
    return out('PASS','One bijection preserves every typed vertex and directed edge including multiplicity',witness)


def compare_architectures(left,right):
    try:result=isomorphic(graph_from_air(left),graph_from_air(right))
    except (PolicyError,KeyError,TypeError,ValueError) as exc:result={'status':'UNKNOWN','reason':str(exc),'version':VERSION,'mapping':None}
    return {**result,'scope':'Names/order ignored; containment, component categories, port directions, wiring and supported properties checked',
            'not_established':['payload type equivalence','GUMBO/requirement semantics','implementation/proof/test acceptance'],
            'whole_system_acceptance':False}
