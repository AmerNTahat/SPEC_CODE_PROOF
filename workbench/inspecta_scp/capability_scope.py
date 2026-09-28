"""Reviewed, version-bound requirement deferrals; never convert missing proof to PASS."""
from pathlib import Path
from .approvals import Approvals
from .config import PolicyError,digest
from .storage import sha_file

STATUSES={'REQUIRED','NOT_SUPPORTED_TOOL_VERSION','NEEDS_MODELING','IMPLEMENTATION_FAILURE','UNASSESSED','OUT_OF_SCOPE_REFERENCE'}


def approval_effect(record):
    if any(r['status']=='OUT_OF_SCOPE_REFERENCE' for r in record['items']):
        return 'Exclude reviewed unsupported-tool and reference-coverage targets only from scoped qualification; retain separate counts, no passing credit and no whole-system acceptance. Reference omission does not establish a tool limitation. Reassess after a reference or tool change.'
    return 'Exclude only explicitly unsupported targets from this version-specific target list; retain them as deferred, never passed. Upgrade requires reassessment. This does not waive full-system acceptance gates.'


class CapabilityScope:
    def __init__(self,controller):
        self.controller=controller;self.store=controller.store;self.approvals=Approvals(self.store)

    def tool(self,run_id):
        run=self.controller.status(run_id)
        if not run.get('evidence_current_for_source') or not run.get('policy_current'):
            raise PolicyError('Current executed capability evidence required')
        evidence=[self.store.load_object(g['evidence']) for g in (run.get('result') or {}).get('gates',[]) if g.get('evidence')]
        identities=[e['tool_identity'] for e in evidence if e.get('tool_identity')]
        if not identities:raise PolicyError('Run has no executed tool identity')
        identity=identities[0];home=Path(run['config']['sireum']).parent.parent
        files={'bin/sireum':identity['launcher_sha256'],**identity.get('runtime_files',{})}
        if identity.get('jar_sha256'):files['bin/sireum.jar']=identity['jar_sha256']
        for name,sha in files.items():
            if not (home/name).is_file() or sha_file(home/name)!=sha:raise PolicyError('Tool changed; reassess capability scope')
        return {'home':str(home),'files':files,'identity_digest':digest(files)}

    def propose(self,preparation_id,tool_run_id,items):
        prepared=self.store.read_record('prepared_requirements',preparation_id)
        tool=self.tool(tool_run_id)
        if not isinstance(items,list) or not 1<=len(items)<=256:raise PolicyError('A bounded, explicit requirement inventory is required')
        seen=set();normalized=[]
        for item in items:
            if not isinstance(item,dict) or set(item)!={'requirement_id','source_excerpt','status','reason','evidence_run_ids','alternative_encoding_review','revisit_condition'}:
                raise PolicyError('Each target needs exact source, status, reason, evidence, alternative-encoding review and revisit condition')
            key=item['requirement_id']
            if not isinstance(key,str) or not key.strip() or key in seen:raise PolicyError('Unique requirement IDs required')
            seen.add(key)
            if not isinstance(item['source_excerpt'],str) or not item['source_excerpt'].strip() or item['source_excerpt'] not in prepared['english']:
                raise PolicyError('Requirement excerpt must occur in the preserved English revision')
            if item['status'] not in STATUSES:raise PolicyError('Unknown capability classification')
            if any(not isinstance(item[k],str) or not item[k].strip() for k in ['reason','alternative_encoding_review','revisit_condition']):
                raise PolicyError('Explain capability evidence, alternative encodings and reconsideration conditions')
            runs=item['evidence_run_ids']
            if not isinstance(runs,list) or not runs or len(set(runs))!=len(runs):raise PolicyError('Executed evidence run IDs required')
            for run in runs:
                if self.tool(run)['identity_digest']!=tool['identity_digest']:raise PolicyError('Evidence belongs to a different tool version')
            normalized.append(dict(item))
        record=self.store.record('capability_scope',{'preparation_id':preparation_id,'english_sha256':prepared['english_sha256'],
            'tool_run_id':tool_run_id,'tool':tool,'items':normalized,'whole_system_acceptance':False,
            'scope':'Reviewed version-scoped target inventory only; classification is not proof. Original English remains intact; unsupported targets remain in total coverage.'})
        approval=self.approvals.request('approve_capability_scope',{'scope_id':record['id'],'scope_digest':digest(record),
            'effect':approval_effect(record)})
        return {**record,'approval':approval}

    def inspect(self,key):
        record=self.store.read_record('capability_scope',key)
        approval=self.approvals.request('approve_capability_scope',{'scope_id':key,'scope_digest':digest(record),
            'effect':approval_effect(record)})
        current=True;reason=None
        try:
            if self.tool(record['tool_run_id'])!=record['tool']:raise PolicyError('Tool identity changed')
            for row in record['items']:
                for run_id in row['evidence_run_ids']:
                    if self.tool(run_id)['identity_digest']!=record['tool']['identity_digest']:
                        raise PolicyError('Supporting capability evidence changed')
            prepared=self.store.read_record('prepared_requirements',record['preparation_id'])
            if prepared['english_sha256']!=record['english_sha256']:raise PolicyError('English identity changed')
            if 'plan_id' in prepared:
                from .data_preparation import DataPreparation
                DataPreparation(self.controller).approved(prepared['id'],prepared['plan_id'],prepared['role'])
        except (PolicyError,OSError) as exc:current=False;reason=str(exc)
        effective=current and approval['status']=='APPROVED'
        rows=[{**r,'mandatory_in_scoped_validation':not(effective and r['status'] in {'NOT_SUPPORTED_TOOL_VERSION','OUT_OF_SCOPE_REFERENCE'}),
               'result':'DEFERRED_UNSUPPORTED' if effective and r['status']=='NOT_SUPPORTED_TOOL_VERSION' else ('EXCLUDED_REFERENCE_SCOPE' if effective and r['status']=='OUT_OF_SCOPE_REFERENCE' else 'NOT_VERIFIED')} for r in record['items']]
        return {**record,'approval':approval,'current':current,'invalid_reason':reason,'effective':effective,'targets':rows,
                'total_targets':len(rows),'mandatory_targets':sum(r['mandatory_in_scoped_validation'] for r in rows),
                'deferred_targets':sum(r['result']=='DEFERRED_UNSUPPORTED' for r in rows),'reference_excluded_targets':sum(r['result']=='EXCLUDED_REFERENCE_SCOPE' for r in rows),
                'qualification_denominator':sum(r['mandatory_in_scoped_validation'] for r in rows),
                'excluded_targets_are_failures':False,'verified_targets':0,
                'inventory_completeness':'Human-reviewed inventory; English semantic completeness not automatically established'}

    def catalog(self):return [self.inspect(r['id']) for r in self.store.records('capability_scope')]

    def bind(self,key,preparation_id,config):
        scope=self.inspect(key)
        if not scope['effective']:raise PolicyError('Capability scope needs current review and evidence')
        if scope['preparation_id']!=preparation_id:raise PolicyError('Capability scope belongs to different English')
        exe=Path(config.get('sireum') or '')
        if str(exe.parent.parent)!=scope['tool']['home'] or config.get('sireum_sha256')!=scope['tool']['files']['bin/sireum']:
            raise PolicyError('Capability scope belongs to a different selected tool; reassess after upgrade')
        return scope
