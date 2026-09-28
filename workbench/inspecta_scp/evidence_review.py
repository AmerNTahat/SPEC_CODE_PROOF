"""Human-reviewed qualification; evidence is never improved by an exclusion."""
import re
import uuid
from .config import PolicyError, digest, GATES
from .approvals import Approvals
from .scoped_rulebooks import ScopedRulebooks

FORMAL='configured_formal_verification'
SEMANTIC_DISTANCE_CEILING=0.3
CATEGORIES={
 'semantic_similarity':'Semantic similarity', 'parse_type':'Parse / type', 'architecture_capture':'Architecture export',
 'architecture':'Architecture comparison', 'hamr_codegen':'HAMR generation',
 'integration_constraints':'Integration / system checks', FORMAL:'Formal verification',
 'configured_build':'Build', 'requirements_coverage':'Requirement mapping',
 'independent_requirements_tests':'Independent requirement tests',
 'verus':'Code-level Verus', 'gumbox':'GUMBOX tests', 'r2u2':'R2U2 monitoring', 'qemu':'QEMU simulation'}
REASONS={'TOOL_LIMITATION','GOLDEN_COVERAGE','DEFERRAL'}


def score_evidence(key, evidence):
    """Counts describe the evidence's unit, never silently English requirements."""
    result={'passed':None,'total':None,'unit':'not reported','items':[], 'observation':None}
    if key=='integration_constraints' and evidence.get('integration_results'):
        rows=evidence['integration_results']
        result.update(passed=sum(r.get('smt2QueryResult',{}).get('value')=='Unsat' for r in rows),total=len(rows),unit='connection claims')
        result['items']=[{'id':str(i)+'-'+digest(r)[:12],'contract':str(r.get('claim','Connection claim')),
                          'status':{'Unsat':'PASS','Sat':'FAIL'}.get(r.get('smt2QueryResult',{}).get('value'),'UNKNOWN')} for i,r in enumerate(rows)]
    # Only adapter-produced, individually mapped obligations can qualify a partial formal gate.
    # There is deliberately no UI endpoint for uploading success counts.
    rows=evidence.get('mapped_obligations')
    if isinstance(rows,list) and rows:
        seen=set();items=[]
        for row in rows:
            if not isinstance(row,dict) or not all(isinstance(row.get(k),str) and row[k].strip() for k in ('id','requirement','contract','status')) or row['id'] in seen or row['status'] not in {'PASS','FAIL','UNKNOWN','NOT_RUN'}:
                raise PolicyError('Malformed or duplicate mapped obligation evidence')
            seen.add(row['id']);items.append(row)
        result.update(items=items,passed=sum(r['status']=='PASS' for r in items),total=len(items),unit='mapped obligations')
    elif key=='verus':
        counts=re.findall(r'verification results::\s*(\d+) verified,\s*(\d+) errors',evidence.get('stdout',''))
        if len(counts)==1:
            p,f=map(int,counts[0]);result.update(passed=p,total=p+f,unit='Verus verification units (not English requirements)')
    elif key=='gumbox':
        counts=re.findall(r'test result:.*?(\d+) passed; (\d+) failed; (\d+) ignored',evidence.get('stdout',''))
        if counts:
            p,f,i=map(sum,zip(*(tuple(map(int,x)) for x in counts)))
            result.update(passed=p,total=p+f+i,unit='test cases',ignored=i)
    elif key in {'r2u2','qemu'}:
        # Future trusted adapters must supply explicit observation provenance, not only exit 0.
        verdicts=evidence.get('property_verdicts')
        if key=='r2u2' and isinstance(verdicts,list) and verdicts:
            if any(not isinstance(v,dict) or not isinstance(v.get('id'),str) or not v['id'] or v.get('status') not in {'PASS','FAIL','UNKNOWN'} for v in verdicts) or len({v['id'] for v in verdicts})!=len(verdicts):
                raise PolicyError('Malformed monitor property verdicts')
            result.update(passed=sum(v['status']=='PASS' for v in verdicts),total=len(verdicts),unit='monitored properties over recorded trace',items=verdicts,
                inconclusive=sum(v['status']=='UNKNOWN' for v in verdicts))
        observation=evidence.get('observation')
        if isinstance(observation,dict):
            result['observation']=observation
            complete=observation.get('completed') is True
            monitored=observation.get('monitor_active') is True
            duration=observation.get('duration_seconds')
            window=type(duration) in (int,float) and 0<duration<float('inf')
            anomalies=observation.get('anomalies')
            if complete and monitored and window and type(anomalies) is int and anomalies>=0 and observation.get('scenario') and observation.get('clock') in {'simulated','wall'}:
                if key=='qemu':result.update(passed=int(anomalies==0),total=1,unit='completed monitored observation window')
                result['observation_verdict']=('No monitored anomaly detected' if anomalies==0 else 'Monitored anomalies detected')+f" during {duration} seconds ({observation['clock']}) under {observation['scenario']}"
            else:result['observation_verdict']='Observation incomplete or monitoring/window not established; no anomaly-free claim'
    return result


class EvidenceReview:
    def __init__(self,controller):
        self.controller=controller;self.store=controller.store;self.approvals=Approvals(self.store)

    def propose(self,result_id,policy='partial',note='',require_semantic=True):
        if policy not in {'partial','all'}:raise PolicyError('Choose partial or all-checks policy')
        result=self.store.read_record('development_result',result_id)
        run=self.controller.status(result['generated_run_id'])
        gates=set(run['config']['required_gates'])-{'review'}
        task=self.store.read_record('development_task',result['task_id'])
        for key in task['candidate_ids']:
            gates.update(self.store.read_record('candidate_rule',key)['record'].get('validation_gate_ids',[]))
        gates.discard('review');gates.add(FORMAL)
        scope=ScopedRulebooks(self.controller).create(result_id,'Qualification review: '+task.get('target_file','example'),sorted(gates & GATES))
        record=self.store.record('evidence_review',{'scope_id':scope['id'],'policy':policy,'note':str(note),'declared_gates':sorted(gates),'require_semantic':require_semantic,
            'provenance':'Controller suggestion from declared run/rule gates; no model call or automatic exclusions',
            'nonce':uuid.uuid4().hex})
        return self.inspect(record['id'])

    def _approval(self,action,subject):
        return [self.approvals.get(a['id']) for a in self.store.records('approval') if a['action']==action and a['subject']==subject]

    def inspect(self,key):
        review=self.store.read_record('evidence_review',key)
        scope=ScopedRulebooks(self.controller).inspect(review['scope_id'])
        result=self.store.read_record('development_result',scope['result_id'])
        try:run=self.controller.status(result['generated_run_id']);run_error=None
        except (PolicyError,OSError) as exc:run={};run_error=str(exc)
        gates={g['gate']:g for g in (run.get('result') or {}).get('gates',[])}
        base={g['check']:g for g in scope['checks']}
        rows=[]
        for gate,label in {**CATEGORIES,**{g:g for g in review.get('declared_gates',[]) if g not in CATEGORIES}}.items():
            raw=gates.get(gate,{})
            status=base.get(gate,{}).get('status',raw.get('status','NOT_CONFIGURED' if gate in {'verus','gumbox','r2u2','qemu'} else 'NOT_RUN'))
            evidence={};error=None
            try:
                if raw.get('evidence'):evidence=self.store.load_object(raw['evidence'])
                scored=score_evidence(gate,evidence)
            except (PolicyError,OSError,ValueError) as exc:error=str(exc);scored=score_evidence(gate,{})
            if raw.get('status')=='PASS' and (not raw.get('evidence') or error):status='STALE'
            if run_error or not run.get('evidence_current_for_source') or not run.get('policy_current'):status='STALE' if raw else status
            if any('stale' in b.lower() or 'changed' in b.lower() for b in scope['blockers']):status='STALE' if raw else status
            if status=='PASS':status='VERIFIED'
            if status=='FAIL':status='FAILED'
            if scored['total'] is None and status in {'VERIFIED','FAILED'} and gate not in {'r2u2','qemu'}:
                scored.update(passed=int(status=='VERIFIED'),total=1,unit='executed gate verdict; obligation count not reported')
            row={'id':gate,'label':label,'status':status,'required':gate in review.get('declared_gates',scope['gates']),
                 'reason':error or base.get(gate,{}).get('reason',raw.get('reason','No bound executed adapter result')),
                 'evidence':raw.get('evidence'),'details':evidence,'score':scored,'formal':gate in {FORMAL,'verus'}}
            rows.append(row)
        if review.get('engineering_job_id'):
            from .engineering_progress import EngineeringProgress
            job=self.store.read_record('engineering_execution_job',review['engineering_job_id'])
            bound=EngineeringProgress(self.controller).inspect(job)
            valid=bound['current'] and bound['state']=='COMPLETE' and job['model_run_id']==result['generated_run_id']
            formal_items=[];verus_items=[];test_items=[]
            for component in bound['components']:
                crate=component['component']
                formal_items += [{'id':crate+'/'+name,'requirement':'Generated contract '+name,'contract':name,
                    'status':'PASS' if valid and component['verus_status']=='PASS' else 'UNKNOWN'} for name in component['declared_contracts']]
                verus_items.append({'id':crate,'requirement':'Component verification','contract':crate,
                    'status':'PASS' if valid and component['verus_status']=='PASS' else 'FAIL' if valid and component['verus_status']=='FAIL' else 'UNKNOWN'})
                test_items += [{'id':crate+'/'+case['name'],'requirement':'Generated GUMBOX contract test','contract':case['name'],
                    'status':'PASS' if valid and case['status']=='ok' else 'FAIL' if valid and case['status']=='FAILED' else 'UNKNOWN'} for case in component['gumbo_tests']['cases']]
            for name,items,unit in [(FORMAL,formal_items,'named generated contract obligations'),('verus',verus_items,'component proof results'),('gumbox',test_items,'GUMBOX test cases')]:
                row=next(r for r in rows if r['id']==name)
                row.update(required=True,status=('VERIFIED' if items and all(x['status']=='PASS' for x in items) else 'FAILED') if valid else 'STALE',
                    reason='Bound current Rust implementation evidence. Formal obligations remain conditional on component requires clauses; no physical timing or integration claim.',
                    evidence={'engineering_job_id':job['id']},details=bound,
                    score={'passed':sum(x['status']=='PASS' for x in items),'total':len(items),'unit':unit,'items':items})
        semantic=next(r for r in rows if r['id']=='semantic_similarity')
        policy=review.get('semantic_policy')
        semantic.update(required=bool(review.get('require_semantic') or policy),status='NOT_CONFIGURED',reason='Choose the comparison threshold; retrieval epsilon is separate.')
        if policy:
            try:
                from pathlib import Path
                from .storage import sha_file
                if not 0<=policy['max_distance']<=SEMANTIC_DISTANCE_CEILING:raise PolicyError('Semantic distance exceeds the authorized 0.3 ceiling')
                assessment=self.store.read_record('development_graph_assessment',policy['assessment_id'])
                if assessment['result_id']!=scope['result_id']:raise PolicyError('Semantic assessment belongs to another result')
                for filename,field in [('graph_equivalence.py','checker_sha256'),('contract_similarity.py','similarity_checker_sha256')]:
                    if sha_file(Path(__file__).with_name(filename))!=assessment[field]:raise PolicyError('Comparison implementation changed; recheck')
                if len(assessment['snapshot_ids'])!=2:raise PolicyError('Two architecture snapshots required')
                for run_id,snapshot_id in zip([result['reference_run_id'],result['generated_run_id']],assessment['snapshot_ids']):
                    checked=self.controller.status(run_id)
                    if not checked.get('evidence_current_for_source') or not checked.get('policy_current'):raise PolicyError('Comparison source/evidence changed')
                    if checked['config'].get('sireum'):
                        from .capability_scope import CapabilityScope
                        CapabilityScope(self.controller).tool(run_id)
                    capture=next((g for g in checked['result']['gates'] if g['gate']=='architecture_capture' and g['status']=='PASS'),None)
                    if not capture or capture.get('snapshot_id')!=snapshot_id:raise PolicyError('Architecture evidence binding changed')
                    snapshot=self.store.read_record('architecture_snapshot',snapshot_id)
                    if snapshot['run_id']!=run_id or snapshot['config_hash']!=checked['config_hash']:raise PolicyError('Snapshot identity changed')
                    self.store.load_object(snapshot['normalized'])
                if assessment.get('approved_adaptation'):
                    from .approved_comparison import approved_scope
                    approved_scope(self.store,assessment['approved_adaptation']['approval_id'])
                    if sha_file(Path(__file__).with_name('approved_comparison.py'))!=assessment['approved_adaptation']['checker_sha256']:
                        raise PolicyError('Approved comparison checker changed; recheck')
                similarity=assessment['similarity_assistance'];distance=similarity.get('cosine_distance')
                passed=assessment['graph']['status']=='PASS' and distance is not None and distance<=policy['max_distance']
                semantic.update(status='VERIFIED' if passed else ('FAILED' if distance is not None else 'UNKNOWN'),
                    reason='Post-graph contract-feature cosine distance must be <= '+str(policy['max_distance'])+'; similarity is not semantic-equivalence proof.',
                    details=assessment,evidence={'assessment_id':assessment['id']},
                    score={'passed':int(passed),'total':1,'unit':'configured similarity criterion','items':[],
                           'cosine_similarity':similarity.get('cosine_similarity'),'cosine_distance':distance,'max_distance':policy['max_distance'],
                           'representation':similarity['representation']})
            except (PolicyError,OSError,KeyError,ValueError) as exc:semantic.update(status='STALE',reason=str(exc))
        evidence_fingerprint=digest({'scope_fingerprint':scope['fingerprint'],'rows':rows})
        exclusions=[]
        for e in self.store.records('evidence_exclusion'):
            if e['review_id']!=key:continue
            approvals=self._approval('approve_evidence_exclusion',{'exclusion_id':e['id'],'digest':digest(e)})
            approval=approvals[0] if approvals else None
            exclusions.append({**e,'approval':approval,'current':e['evidence_fingerprint']==evidence_fingerprint,
                'effective':e['evidence_fingerprint']==evidence_fingerprint and approval is not None and approval['status']=='APPROVED'})
        included=passed=excluded=0;blockers=[]
        for row in rows:
            targets=row['score']['items'] or [{'id':row['id'],'status':'PASS' if row['status']=='VERIFIED' else row['status']}]
            decisions=[]
            for t in targets:
                target=row['id']+':'+t['id'] if row['score']['items'] else row['id']
                approved=[e for e in exclusions if e['target']==target and e['effective']]
                outside=bool(approved)
                if row['required']:
                    excluded+=outside;included+=not outside
                    success=t['status']=='PASS' and row['status'] not in {'STALE','NOT_RUN','NOT_CONFIGURED','UNKNOWN'}
                    passed+=not outside and success
                    if not outside and not success:blockers.append(target+': '+t['status'])
                decisions.append({**t,'target':target,'excluded':outside,'exclusion_labels':['HUMAN_APPROVED_'+('DEFERRAL' if e['reason_code']=='DEFERRAL' else 'EXCLUSION_'+e['reason_code']) for e in approved]})
            row['obligations']=decisions
            row['included_passed']=sum(not t['excluded'] and t['status']=='PASS' and row['status'] not in {'STALE','UNKNOWN','NOT_RUN','NOT_CONFIGURED'} for t in decisions)
            row['included_total']=sum(not t['excluded'] for t in decisions)
        formal=next(r for r in rows if r['id']==FORMAL)
        if not formal['included_total'] or formal['included_passed']!=formal['included_total']:
            blockers.append('Formal verification is mandatory and needs nonempty passing included evidence')
        # Preserve all non-gate freshness blockers; an exclusion cannot waive invalid evidence.
        blockers+= [b for b in scope['blockers'] if not any(b.startswith(g+': ') for g in scope['gates'])]
        if run_error:blockers.append(run_error)
        fingerprint=digest({'review':review,'evidence':evidence_fingerprint,'exclusions':exclusions,'blockers':blockers})
        approvals=self._approval('accept_evidence_scope',{'review_id':key,'fingerprint':fingerprint})
        accepted=not blockers and any(a['status']=='APPROVED' for a in approvals)
        return {**review,'scope':scope,'rows':rows,'exclusions':exclusions,
            'recorded_comparison':self.store.read_record('development_golden_comparison',result['comparison_id']) if result.get('comparison_id') else None,
            'graph_assessments':[g for g in self.store.records('development_graph_assessment') if g['result_id']==result['id']],'evidence_fingerprint':evidence_fingerprint,'fingerprint':fingerprint,
            'blockers':blockers,'eligible':not blockers,'approvals':approvals,
            'approval_history':[self.approvals.get(a['id']) for a in self.store.records('approval') if a['action']=='accept_evidence_scope' and a['subject'].get('review_id')==key],
            'status':('ACCEPTED_HUMAN_REVIEWED_PARTIAL_SCOPE' if excluded else 'ACCEPTED_DECLARED_SCOPE') if accepted else 'PARTIAL_PROGRESS_NOT_ACCEPTED',
            'scores':{'included_passed':passed,'included_total':included,'excluded':excluded,'declared_total':included+excluded,
                'unit':'review targets (gates or explicitly mapped obligations); consult separate category scores; not an overall correctness percentage'},
            'decision_deferrals':[d for d in self.store.records('evidence_decision_deferral') if d['review_id']==key and d['evidence_fingerprint']==evidence_fingerprint],
            'candidate_retained':True,'publishes_rules':False,'transfer':'IN_PROGRESS'}

    def exclude(self,key,target,reason_code,reason,revisit):
        current=self.inspect(key)
        if current['policy']!='partial':raise PolicyError('All-checks policy does not permit exclusions; create a new partial review')
        row=next((r for r in current['rows'] if any(t['target']==target for t in r['obligations'])),None)
        if row is None or not row['required']:raise PolicyError('Choose a declared required target')
        if row['formal'] and not row['score']['items']:raise PolicyError('Cannot exclude an entire formal gate; mapped obligations are required')
        if reason_code not in REASONS or not all(isinstance(x,str) and x.strip() for x in (reason,revisit)):
            raise PolicyError('Record exclusion classification, evidence/reason and revisit condition')
        record=self.store.record('evidence_exclusion',{'review_id':key,'target':target,'reason_code':reason_code,'reason':reason.strip(),
            'revisit':revisit.strip(),'evidence_fingerprint':current['evidence_fingerprint'],'nonce':uuid.uuid4().hex})
        approval=self.approvals.request('approve_evidence_exclusion',{'exclusion_id':record['id'],'digest':digest(record)})
        return {**record,'approval':approval}

    def accept(self,key):
        review=self.inspect(key)
        if not review['eligible']:raise PolicyError('Included mandatory checks have not passed: '+'; '.join(review['blockers']))
        return self.approvals.request('accept_evidence_scope',{'review_id':key,'fingerprint':review['fingerprint']})

    def validate(self,action,subject):
        if action=='approve_evidence_exclusion':
            record=self.store.read_record('evidence_exclusion',subject['exclusion_id'])
            current=self.inspect(record['review_id'])
            if digest(record)!=subject['digest'] or current['evidence_fingerprint']!=record['evidence_fingerprint']:raise PolicyError('Evidence changed; propose a new exclusion')
        else:
            current=self.inspect(subject['review_id'])
            if not current['eligible'] or current['fingerprint']!=subject['fingerprint']:raise PolicyError('Scope or evidence changed; review again')

    def note(self,key,text,reviewer):
        self.store.read_record('evidence_review',key)
        if not all(isinstance(x,str) and x.strip() for x in (text,reviewer)):raise PolicyError('Note and reviewer required')
        return self.store.record('evidence_review_note',{'review_id':key,'text':text.strip(),'reviewer':reviewer.strip(),'nonce':uuid.uuid4().hex})

    def repair(self,key,target,campaign_id=None):
        review=self.inspect(key)
        if not any(t['target']==target for r in review['rows'] for t in r['obligations']):raise PolicyError('Unknown review target')
        from .validation_repair import ValidationRepair
        result_id=review['scope']['result_id']
        if campaign_id is None:return ValidationRepair(self.controller).report(result_id)
        from .development import Development
        # Existing controller checks exact task approval, shared attempt counts, time and tokens.
        # One attempt, followed by a fresh review, never automatic acceptance.
        result=Development(self.controller).generate_and_check(review['scope']['task_id'],campaign_id,result_id)
        return {'result':result,'review':self.propose(result['id'],review['policy']) if result.get('generated_run_id') else None,'next_action':'Inspect changed model and rerun results; suggest a new review. Old exclusions and acceptance do not carry forward.'}

    def propose_implementation(self,parent_result_id,job_id,reference_run_id,note):
        """Preserve historical generation; separately review a supervised implementation candidate."""
        from .engineering_progress import EngineeringProgress
        job=self.store.read_record('engineering_execution_job',job_id)
        bound=EngineeringProgress(self.controller).inspect(job)
        if not bound['current'] or bound['state']!='COMPLETE':raise PolicyError('Completed current engineering evidence required')
        parent=self.store.read_record('development_result',parent_result_id)
        self.controller.status(reference_run_id)
        comparison=self.store.record('development_golden_comparison',{'task_id':parent['task_id'],'lexical':None,
            'architecture_status':'NOT_RUN','architecture_differences':None,'scope':'Supervised implementation candidate; run fresh graph comparison before semantic acceptance'})
        candidate=self.store.record('development_result',{'task_id':parent['task_id'],'generated_run_id':job['model_run_id'],
            'reference_run_id':reference_run_id,'comparison_id':comparison['id'],'status':'SUPERVISED_CANDIDATE',
            'parent_result_id':parent_result_id,'engineering_job_id':job_id,'supervised_amendment':note,
            'scope':'Separate supervised repaired candidate; original rule bundle provenance retained, not proof of causal rule use or independent transfer.',
            'whole_system_acceptance':False,'model_calls':0})
        proposed=self.propose(candidate['id'],'partial',note)
        record=self.store.read_record('evidence_review',proposed['id'])
        bound_review=self.store.record('evidence_review',{**{k:v for k,v in record.items() if k!='id'},
            'engineering_job_id':job_id,'supersedes':record['id'],'nonce':uuid.uuid4().hex})
        return self.inspect(bound_review['id'])

    def set_semantic_policy(self,key,max_distance,reviewer,adaptation_approval_id=None):
        if type(max_distance) not in (int,float) or not 0<=max_distance<=SEMANTIC_DISTANCE_CEILING or not isinstance(reviewer,str) or not reviewer.strip():
            raise PolicyError('Comparison distance in [0,0.3] and reviewer required')
        old=self.store.read_record('evidence_review',key)
        scope=ScopedRulebooks(self.controller).inspect(old['scope_id'])
        if adaptation_approval_id is None and old.get('semantic_policy'):
            prior=self.store.read_record('development_graph_assessment',old['semantic_policy']['assessment_id'])
            adaptation_approval_id=(prior.get('approved_adaptation') or {}).get('approval_id')
        from .development import Development
        assessment=Development(self.controller).compare_graph(scope['result_id'],adaptation_approval_id)
        record=self.store.record('evidence_review',{**{k:v for k,v in old.items() if k!='id'},
            'semantic_policy':{'max_distance':max_distance,'reviewer':reviewer,'assessment_id':assessment['id']},
            'supersedes':key,'nonce':uuid.uuid4().hex})
        return self.inspect(record['id'])

    def quick_decision(self,key,targets,action,reviewer,expected_fingerprint,edits=None,accept=False):
        if type(accept) is not bool:raise PolicyError('Acceptance flag must be boolean')
        if action not in {'exclude','defer'} or not isinstance(targets,list) or not targets or len(targets)>100 or len(set(targets))!=len(targets):
            raise PolicyError('Select unique targets and exclude or defer')
        if not isinstance(reviewer,str) or not reviewer.strip():raise PolicyError('Reviewer required')
        if edits is not None and (not isinstance(edits,dict) or not set(edits)<=set(targets)):raise PolicyError('Edits must belong to selected targets')
        self.store.db.execute('BEGIN IMMEDIATE')
        try:
            current=self.inspect(key)
            if current['fingerprint']!=expected_fingerprint:raise PolicyError('Progress changed; refresh and review the selection again')
            selected=[]
            for target in targets:
                row=next((r for r in current['rows'] if any(t['target']==target for t in r['obligations'])),None)
                item=next((t for t in (row or {}).get('obligations',[]) if t['target']==target),None)
                if row is None or not row['required'] or item['excluded'] or item['status']=='PASS':raise PolicyError('Select unfinished included targets')
                proposed=(edits or {}).get(target) or {'reason_code':'DEFERRAL',
                    'reason':'Human-reviewed exclusion from this round: '+row['reason'],
                    'revisit':'Recheck in the next validation round; retain original evidence and unresolved work.'}
                selected.append((target,proposed))
            if action=='defer':
                if accept:raise PolicyError('Deferring a decision does not accept the scope')
                self.store.record('evidence_decision_deferral',{'review_id':key,'targets':targets,'reviewer':reviewer,
                    'evidence_fingerprint':current['evidence_fingerprint'],'nonce':uuid.uuid4().hex,
                    'effect':'Decision deferred; targets remain mandatory and no pass or exclusion is granted'})
            else:
                for target,proposed in selected:
                    e=self.exclude(key,target,proposed.get('reason_code'),proposed.get('reason'),proposed.get('revisit'))
                    a=e['approval'];self.approvals.decide(a['id'],a['subject_digest'],'APPROVED',reviewer,controller=self.controller)
                if accept:
                    a=self.accept(key);self.approvals.decide(a['id'],a['subject_digest'],'APPROVED',reviewer,controller=self.controller)
            self.store.db.execute('COMMIT')
        except BaseException:
            self.store.db.execute('ROLLBACK');raise
        return self.inspect(key)

    def catalog(self):
        from .engineering_progress import EngineeringProgress
        from .application_results import recorded_checks
        from .campaign import Campaign
        return {'application_checks':recorded_checks(self.store.root.parent.parent),'campaigns':[Campaign(self.store).status(a['id']) for a in self.store.records('campaign_authorization')],'engineering_decisions':[self.approvals.get(a['id']) for a in self.store.records('approval') if a['subject'].get('kind')=='engineering_proposal'],
                'system_verifications':EngineeringProgress(self.controller).system_catalog(),
                'runtime_observations':EngineeringProgress(self.controller).runtime_catalog(),'engineering_executions':EngineeringProgress(self.controller).catalog(),'reviews':[self.inspect(r['id']) for r in self.store.records('evidence_review')],
                'notes':self.store.records('evidence_review_note'),
                'notice':'Saved rulebooks retain every result and exclusion. Historical component reports do not qualify a different model. No aggregate correctness percentage.'}
