"""Scoped bundle acceptance and honest partial coverage; never publishes a rule."""
from collections import Counter
import uuid
import re
from pathlib import Path
from .storage import safe_child, sha_file
from .config import PolicyError, digest, GATES
from .approvals import Approvals

SUGGESTED_CHECK = {
    'id': 'ISOLETTE-INVALID-RANGE-CONSUMPTION', 'status': 'NOT_VERIFIED',
    'reason': 'Boundary ordering is assumed; MRI9 allows unspecified internal bounds during interface failure.',
    'source': 'FAA AR-08-32 EA-OI-6 (A-11), REQ-MRI-8/9 (A-17)',
    'steps': ['Trace connections, initialization, dispatch order and mode/failure sampling.',
              'Check healthy copying under the approved environmental assumption.',
              'Check whether unspecified bounds reach heat control with NORMAL mode.',
              'Use supported HAMR system checks, Verus and targeted GUMBOX; record unsupported timing checks explicitly.',
              'If a counterexample exists, review a conforming ordered fallback or invalid-value guard, then repeat affected checks.'],
    'scope': 'Suggested check, not an executed system proof or demonstrated tool limitation.'}


class ScopedRulebooks:
    def __init__(self, controller):
        self.controller=controller;self.store=controller.store;self.approvals=Approvals(self.store)

    def create(self, result_id, title, gates):
        if not isinstance(title,str) or not title.strip():raise PolicyError('Name the exact qualification scope')
        if not isinstance(gates,list) or not gates or len(set(gates))!=len(gates) or not set(gates)<=GATES-{'review'}:
            raise PolicyError('Select unique executed-check types; review is a separate decision')
        result=self.store.read_record('development_result',result_id)
        task=self.store.read_record('development_task',result['task_id'])
        if not result.get('generated_run_id') or not task.get('candidate_ids'):
            raise PolicyError('A generated development result with an exact supplied rule bundle is required')
        from .knowledge import Knowledge
        Knowledge(self.store).draft_release(task['candidate_ids'])
        scope=self.store.record('scoped_rulebook',{'result_id':result_id,'task_id':task['id'],
            'candidate_ids':sorted(task['candidate_ids']),'title':title.strip(),'gates':sorted(gates),
            'interpretation':'Human acceptance of this supplied rule bundle for these checks on this example only; no independent causal-use, behavioral or transfer claim beyond the selected checks.'})
        return self.inspect(scope['id'])

    def inspect(self, scope_id):
        scope=self.store.read_record('scoped_rulebook',scope_id)
        result=self.store.read_record('development_result',scope['result_id'])
        task=self.store.read_record('development_task',scope['task_id'])
        rules=[self.store.read_record('candidate_rule',key) for key in scope['candidate_ids']]
        blockers=[];run={};run_tool=None;cap=None;requirements=[];requirement_total=None
        if sorted(task.get('candidate_ids',[]))!=scope['candidate_ids']:blockers.append('Rule bundle binding changed')
        try:
            run=self.controller.status(result['generated_run_id'])
            if run.get('config',{}).get('sireum'):
                from .capability_scope import CapabilityScope
                run_tool=CapabilityScope(self.controller).tool(run['id'])
            if not run.get('evidence_current_for_source') or not run.get('policy_current'):
                blockers.append('Model, tool or executed evidence is stale')
        except (PolicyError,OSError,ValueError) as exc:blockers.append(str(exc))
        assumptions=[]
        folder=self.store.root/'runs'/result['generated_run_id']
        manifest_path=folder/'input-workspace-manifest.json'
        if manifest_path.is_file():
            import json
            try:
                manifest=json.loads(manifest_path.read_text())
                for name, expected in manifest['files'].items():
                    path=safe_child(folder/'candidate',name)
                    if sha_file(path)!=expected:raise PolicyError('Checked input snapshot changed: '+name)
                    if path.suffix=='.sysml':
                        assumptions += [{'file':name,'clause':m.group(0),'classification':'Assume clause, including compute-case guards; not automatically an environmental premise'} for m in re.finditer(r'\bassume\s+[^;]+;',path.read_text())]
            except (PolicyError,OSError,ValueError,KeyError) as exc:blockers.append(str(exc))
        current=not blockers
        declared=set(scope['gates'])|set(run.get('config',{}).get('required_gates',[]))-{'review'}
        declared.update(g for r in rules for g in r['record'].get('validation_gate_ids',[]) if g!='review')
        actual={g['gate']:g for g in (run.get('result') or {}).get('gates',[])}
        checks=[]
        for name in sorted(declared):
            gate=actual.get(name,{});status=gate.get('status','NOT_RUN');reason=gate.get('reason','No executed check recorded')
            if status=='PASS':
                try:
                    if not gate.get('evidence'):raise PolicyError('No executed evidence object')
                    self.store.load_object(gate['evidence'])
                    status='VERIFIED' if current else 'STALE'
                except (PolicyError,OSError,ValueError) as exc:status='STALE';reason=str(exc)
            elif status=='FAIL':status='FAILED'
            elif status not in {'NOT_RUN','UNKNOWN'}:status='NOT_VERIFIED'
            checks.append({'check':name,'status':status,'reason':reason,'in_scope':name in scope['gates'],
                'next_action':'Retain current evidence' if status=='VERIFIED' else 'Run/recheck this gate; diagnose failures before repair. Unknown does not mean unsupported.',
                'evidence':gate.get('evidence')})
        in_scope=[g for g in checks if g['in_scope']]
        for g in in_scope:
            if g['status']!='VERIFIED':blockers.append(g['check']+': '+g['status'])
        # Tool exclusions are imported only from a current, approved capability inventory.
        if task.get('capability_scope_id'):
            try:
                from .capability_scope import CapabilityScope, approval_effect
                service=CapabilityScope(self.controller)
                cap=self.store.read_record('capability_scope',task['capability_scope_id'])
                subject={'scope_id':cap['id'],'scope_digest':digest(cap),'effect':approval_effect(cap)}
                approvals=[a for a in self.store.records('approval') if a['action']=='approve_capability_scope' and a['subject']==subject]
                effective=len(approvals)==1 and self.approvals.get(approvals[0]['id'])['status']=='APPROVED'
                effective=effective and service.tool(cap['tool_run_id'])['identity_digest']==cap['tool']['identity_digest']
                effective=effective and run_tool is not None and run_tool['identity_digest']==cap['tool']['identity_digest']
                effective=effective and cap['preparation_id']==task.get('prepared_requirements_id')
                prepared=self.store.read_record('prepared_requirements',cap['preparation_id'])
                effective=effective and prepared['english_sha256']==cap['english_sha256']
                for row in cap['items']:
                    for evidence_run in row['evidence_run_ids']:
                        effective=effective and service.tool(evidence_run)['identity_digest']==cap['tool']['identity_digest']
                if 'plan_id' in prepared:
                    from .data_preparation import DataPreparation
                    DataPreparation(self.controller).approved(prepared['id'],prepared['plan_id'],prepared['role'])
                for item in cap['items']:
                    status='NOT_VERIFIED'
                    if effective and item['status']=='NOT_SUPPORTED_TOOL_VERSION':status='TOOL_LIMITATION'
                    elif effective and item['status']=='OUT_OF_SCOPE_REFERENCE':status='OUTSIDE_REVIEWED_SCOPE'
                    elif not effective:status='AWAITING_SCOPE_REVIEW'
                    requirements.append({'id':item['requirement_id'],'status':status,'reason':item['reason'],'next_action':item['revisit_condition']})
                requirement_total=len(requirements)
                cap={'record':cap,'effective':effective}
            except (PolicyError,OSError,ValueError) as exc:blockers.append('Capability inventory: '+str(exc))
        snapshot={'scope':scope,'task':task,'result':result,'rules':rules,
            'config_hash':run.get('config_hash'),'run_result':run.get('result'),
            'checks':checks,'requirements':requirements,'capability':cap,'blockers':blockers,'assumptions':assumptions}
        fingerprint=digest(snapshot)
        matches=[]
        for request in self.store.records('approval'):
            if request['action']!='approve_scoped_rulebooks':continue
            review=self.store.read_record('scoped_rulebook_batch',request['subject']['batch_id'])
            if any(x['scope_id']==scope_id and x['fingerprint']==fingerprint for x in review['selection']):
                matches.append(self.approvals.get(request['id']))
        accepted=not blockers and any(a['status']=='APPROVED' for a in matches)
        passed=sum(g['status']=='VERIFIED' for g in in_scope)
        return {**scope,'example':task.get('target_file',run.get('config',{}).get('model_file')),
            'rule_revisions':[{'candidate_id':r['id'],'rule_id':r['record']['id'],'revision':r['record']['revision']} for r in rules],
            'fingerprint':fingerprint,'eligible':not blockers,'status':'ACCEPTED_CURRENT_SCOPE' if accepted else ('AWAITING_HUMAN_REVIEW' if not blockers else ('PARTIAL_SUCCESS' if passed else 'CHECKS_INCOMPLETE')),
            'blockers':blockers,'checks':checks,'requirements':requirements,'assumption_clauses':assumptions,
            'english_reference':task.get('prepared_requirements_id'),'english_digest':digest(task.get('requirements','')), 
            'scores':{'passed_scoped_checks':passed,'required_scoped_checks':len(in_scope),'scoped_check_fraction':passed/len(in_scope),
                'verified_requirements':0 if requirement_total is not None else None,'total_declared_requirements':requirement_total,
                'qualification_requirement_denominator':sum(r['status'] not in {'TOOL_LIMITATION','OUTSIDE_REVIEWED_SCOPE'} for r in requirements) if requirement_total is not None else None,
                'excluded_requirements':sum(r['status'] in {'TOOL_LIMITATION','OUTSIDE_REVIEWED_SCOPE'} for r in requirements),
                'requirement_count_note':'No requirement-level proof is inferred from gate success. Missing mapped inventory remains unknown.',
                'requirement_status_counts':dict(Counter(r['status'] for r in requirements)),
                'check_status_counts':dict(Counter(g['status'] for g in checks))},
            'assumptions_note':'Acceptance remains conditional on assumptions in the bound English/model contracts. Review the exact result and any approved environmental premise; this action does not discharge assumptions.',
            'approval_records':matches,'rule_transfer_status':'TRANSFER_IN_PROGRESS','publishes_rules':False,'whole_system_acceptance':False}

    def prepare_batch(self, scope_ids, comment):
        if not isinstance(scope_ids,list) or not scope_ids or len(scope_ids)>100 or len(set(scope_ids))!=len(scope_ids):raise PolicyError('Select unique eligible scopes')
        if not isinstance(comment,str) or not comment.strip():raise PolicyError('Record a scope-review comment')
        selection=[]
        for key in sorted(scope_ids):
            item=self.inspect(key)
            if not item['eligible'] or item['status']=='ACCEPTED_CURRENT_SCOPE':raise PolicyError('Selected scope is not eligible for new approval: '+key)
            selection.append({'scope_id':key,'fingerprint':item['fingerprint'],'title':item['title'],
                'rule_revisions':item['rule_revisions'],'example':item['example'],'checks':item['checks'],
                'requirements':item['requirements'],'assumptions_note':item['assumptions_note'],'assumption_clauses':item['assumption_clauses'],'english_reference':item['english_reference'],'english_digest':item['english_digest']})
        batch=self.store.record('scoped_rulebook_batch',{'selection':selection,'comment':comment.strip(),'review_nonce':uuid.uuid4().hex,
            'effect':'Accept only displayed rule revisions/examples/check scopes; no release, transfer or whole-system approval'})
        approval=self.approvals.request('approve_scoped_rulebooks',{'batch_id':batch['id'],'batch_digest':digest(batch)})
        return {**batch,'approval':approval}

    def validate_batch(self, subject):
        batch=self.store.read_record('scoped_rulebook_batch',subject['batch_id'])
        if digest(batch)!=subject['batch_digest']:raise PolicyError('Bulk selection changed')
        for selected in batch['selection']:
            current=self.inspect(selected['scope_id'])
            if not current['eligible'] or current['fingerprint']!=selected['fingerprint']:
                raise PolicyError('Scope/evidence changed; inspect and prepare a new bulk review')

    def catalog(self):
        tasks={t['id']:t for t in self.store.records('development_task')}
        options=[{'result_id':r['id'],'example':tasks[r['task_id']].get('target_file','Unnamed'),
                  'candidate_count':len(tasks[r['task_id']]['candidate_ids']),'status':r['status']}
                 for r in self.store.records('development_result') if r.get('generated_run_id') and tasks.get(r['task_id'],{}).get('candidate_ids')]
        scopes=[self.inspect(s['id']) for s in self.store.records('scoped_rulebook')]
        return {'scopes':scopes,'result_options':options,'gate_options':sorted(GATES-{'review'}),
            'suggested_validation_checks':[SUGGESTED_CHECK],
            'counts':dict(Counter(s['status'] for s in scopes)),
            'coverage_notice':'Scores count checks within each declared scope, not proof subgoals. Scopes may overlap; do not sum them as distinct requirements.'}
