"""Explain deployment patterns from resolved AIR; never infer behavior from layout."""
import re
from collections import Counter


def structural_patterns(normalized):
    """Evaluate the optional one-thread-per-process design profile, per AIR root.

    Root labels identify evidence only. Counts and ownership checks ignore names.
    This is not a universal AADL restriction or a replacement for graph bijection.
    """
    results=[]
    for root,model in normalized.get('models',{}).items():
        counts=Counter();processes=[];contracts=[];violations=[];unknown=[]
        def visit(node,parent_category=None):
            category=node.get('category',{}).get('value')
            path='::'.join(node.get('identifier',{}).get('name',[]))
            children=node.get('subComponents')
            if not category or not isinstance(children,list):
                unknown.append(path);return
            counts[category]+=1
            if category=='Process':
                threads=[x for x in children if x.get('category',{}).get('value')=='Thread']
                other=[x for x in children if x.get('category',{}).get('value') not in {'Thread','Data'}]
                processes.append({'owner':path,'direct_threads':len(threads),'other_execution_children':len(other)})
                if len(threads)!=1 or other:
                    violations.append({'rule':'one-thread-per-process','owner':path,'direct_threads':len(threads),'other_execution_children':len(other)})
            if category=='Thread' and parent_category!='Process':
                violations.append({'rule':'thread-owned-by-process','owner':path,'parent_category':parent_category})
            for annex in node.get('annexes',[]):
                if str(annex.get('name','')).lower()=='gumbo' or annex.get('clause',{}).get('type')=='GclSubclause':
                    contracts.append({'owner':path,'owner_category':category})
            for child in children:visit(child,category)
        for component in model.get('components',[]):visit(component)
        results.append({'root':root,'component_counts':dict(counts),'processes':processes,
            'one_thread_per_process':{'status':'UNKNOWN' if unknown else 'FAIL' if violations else 'UNKNOWN' if not processes else 'PASS',
                'violations':violations,'unresolved_components':unknown},
            'gumbo_owners':contracts,'gumbo_owner_categories':dict(Counter(x['owner_category'] for x in contracts))})
    return {'profile':'one-thread-per-process-v1','roots':results,
        'scope':'Diagnostic design profile. Apply only where explicitly selected/approved; multiple threads per process are otherwise legal.',
        'gumbo_scope':'Resolved contract ownership only; absence of a contract is not proof of a missing requirement. Compare with English allocation.',
        'behavioral_acceptance':False}


def source_outline(text):
    # Lexical presentation observation only; the Sireum parser/AIR is authoritative.
    masked=re.sub(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"',lambda m:'\n'*m.group().count('\n')+' ',text)
    declarations=[{'name':m.group(1),'base':m.group(2),'line':masked[:m.start()].count('\n')+1}
        for m in re.finditer(r'\bpart\s+def\s+([A-Za-z_]\w*)\s*:>\s*([A-Za-z_]\w*(?:::\w+)*)',masked)]
    return {'declarations':declarations,'category_order':[x['base'].split('::')[-1] for x in declarations],
        'status':'ADVISORY','scope':'Lexical outline of direct part definitions; not a full SysML parser or equivalence gate. Declaration order is a style preference unless separately approved.'}
