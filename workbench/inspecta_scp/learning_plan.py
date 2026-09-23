"""Reviewed within-system development holdouts, distinct from final transfer splits."""
from .approvals import Approvals
from .config import PolicyError,digest
from .sources import Sources


class LearningPlan:
    def __init__(self,store):self.store=store;self.sources=Sources(store);self.approvals=Approvals(store)

    def propose(self,context_ids,training,validation,epsilon=0.1):
        if type(epsilon) not in (int,float) or not 0 <= epsilon <= 0.3:raise PolicyError('Cosine distance epsilon must be between 0 and 0.3')
        if not isinstance(context_ids,list) or len(set(context_ids))!=len(context_ids):raise PolicyError('Select distinct context documents')
        context=[]
        for key in context_ids:
            doc=self.store.read_record('context_document',key);source=self.sources.view(doc['source_id'])
            if source['freshness']!='CURRENT' or source['role']=='evaluator':raise PolicyError('Context must be current non-evaluator material')
            context.append(doc)
        def passages(items):
            if not isinstance(items,list) or not items or len(items)>100:raise PolicyError('Select training and validation examples')
            result=[]
            for item in items:
                if set(item)!={'source_id','start','end','label'} or not isinstance(item['label'],str) or not item['label'].strip():raise PolicyError('Each component needs a label, source and exact line range')
                source=self.sources.view(item['source_id'],start=item['start'],end=item['end'])
                if source['freshness']!='CURRENT' or source['role']=='evaluator' or not source['text'].strip():raise PolicyError('Example must be current, nonempty and not an evaluator reference')
                result.append({**item,'source_sha256':source['sha256'],'text_sha256':digest(source['text']),
                               'normalized_text_sha256':digest(' '.join(source['text'].split()))})
            return result
        train=passages(training);valid=passages(validation)
        for left in train:
            for right in valid:
                if left['normalized_text_sha256']==right['normalized_text_sha256']:raise PolicyError('Training and validation contain identical text')
                if left['source_sha256']==right['source_sha256'] and max(left['start'],right['start'])<=min(left['end'],right['end']):raise PolicyError('Training and validation passages overlap')
        valid_hashes={x['source_sha256'] for x in valid}
        if any(self.sources.view(d['source_id'])['sha256'] in valid_hashes for d in context):raise PolicyError('Context includes a held-out validation source; select a guidebook or training-only material')
        record=self.store.record('learning_plan',{'context_ids':context_ids,'training':train,'validation':valid,
            'retrieval':{'metric':'lexical_token_count_cosine_distance','epsilon':epsilon,'maximum':0.3,'comparison':'distance <= epsilon'},
            'validation_protocol':'within_system_component_holdout','final_transfer_claim':False,
            'scope':'Human-declared component split; no inferred semantic independence or final transfer claim'})
        approval=self.approvals.request('approve_learning_plan',{'plan_id':record['id'],'plan_digest':digest(record),
            'training_components':[x['label'] for x in train],'validation_components':[x['label'] for x in valid],
            'context_documents':[d['name'] for d in context],'epsilon':epsilon})
        return {**record,'approval':approval}

    def fresh(self,plan_id):
        record=self.store.read_record('learning_plan',plan_id)
        for item in record['training']+record['validation']:
            source=self.sources.view(item['source_id'],start=item['start'],end=item['end'])
            if source['freshness']!='CURRENT' or source['sha256']!=item['source_sha256'] or digest(source['text'])!=item['text_sha256']:
                raise PolicyError('Learning split changed; review a new plan')
        for key in record['context_ids']:
            doc=self.store.read_record('context_document',key)
            if self.sources.view(doc['source_id'])['freshness']!='CURRENT':raise PolicyError('Context changed; review a new plan')
        return record

    def training_context(self,plan_id):
        record=self.fresh(plan_id)
        requests=[a for a in self.store.records('approval') if a['action']=='approve_learning_plan' and a['subject'].get('plan_id')==plan_id]
        if len(requests)!=1:raise PolicyError('Exact split approval required')
        self.approvals.require(requests[0]['id'],'approve_learning_plan',requests[0]['subject'])
        if requests[0]['subject']['plan_digest']!=digest(record):raise PolicyError('Split identity changed')
        examples=[{'label':p['label'],'source_id':p['source_id'],'start':p['start'],'end':p['end'],
            'text':self.sources.view(p['source_id'],start=p['start'],end=p['end'])['text']} for p in record['training']]
        context=[]
        for key in record['context_ids']:
            doc=self.store.read_record('context_document',key)
            context.append({'name':doc['name'],'source_id':doc['source_id'],'text':self.sources.view(doc['source_id'])['text']})
        return {'plan_id':plan_id,'examples':examples,'context':context,'retrieval':record['retrieval'],
                'validation_material_exported':False}
