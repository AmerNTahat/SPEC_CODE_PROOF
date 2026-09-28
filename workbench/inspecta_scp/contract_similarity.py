"""Post-graph contract feature cosine for review prioritization, never proof.
Preserves operators/literals and assume/guarantee distinctions. Formatting and
compiler attribute metadata do not contribute to the score. No embedding claim.
"""
from .vendor.local_compare import cosine_counts


def contract_features(value):
    tokens=[];count=0
    def expression(x):
        if isinstance(x,dict):
            for key,v in x.items():
                if key in {'attr','descriptor','pos','posOpt','opPosOpt','uriFrag'}:continue
                if isinstance(v,(dict,list)):expression(v)
                else:tokens.append(key+':'+str(v))
        elif isinstance(x,list):
            for v in x:expression(v)
    def visit(x):
        nonlocal count
        if isinstance(x,dict):
            if x.get('type') in {'GclAssume','GclGuarantee'}:
                count+=1;tokens.append('obligation:'+x['type']);expression(x['exp']);return
            for v in x.values():visit(v)
        elif isinstance(x,list):
            for v in x:visit(v)
    visit(value['models'])
    return tokens,count


def compare_contract_features(left,right,graph):
    result={'status':'NOT_RUN','cosine_similarity':None,'cosine_distance':None,
        'representation':'Parsed assume/guarantee expression feature counts; not semantic embeddings',
        'scope':'Advisory similarity after structural equivalence; never proves contract equivalence or authorizes acceptance',
        'threshold_applied':False,'limitations':['Unordered features can hide relational differences',
            'Variable names remain significant in this advisory representation',
            'Helper definitions, state semantics and assumption discharge require separate checks']}
    if graph['status']!='PASS':return {**result,'reason':'Directed architecture graph did not pass'}
    a,ac=contract_features(left);b,bc=contract_features(right);score=cosine_counts(a,b)
    return {**result,'status':'UNDEFINED' if score is None else 'ADVISORY',
        'cosine_similarity':score,'cosine_distance':None if score is None else 1-score,
        'left_obligations':ac,'right_obligations':bc}
