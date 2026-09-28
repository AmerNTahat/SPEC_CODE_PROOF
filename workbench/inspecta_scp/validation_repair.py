"""Visible, bounded development repair guidance; no evaluator content to models."""
import json
from .config import PolicyError
from .knowledge import Knowledge

ERROR_FAMILIES = {
    'tool_environment': ('not found', 'no such file', 'rustup', 'cargo', 'sdk', 'permission denied'),
    'scheduling': ('frame period', 'used budget', 'schedule', 'execution time'),
    'syntax_types': ('parse', 'syntax', 'type check', 'unresolved', 'instantiat'),
    'contracts_proof': ('logika', 'verus', 'guarantee', 'assume', 'unsat', 'proof'),
    'implementation_tests': ('test', 'panic', 'assert', 'compile'),
}


def classify_errors(diagnostics):
    text=json.dumps([d for d in diagnostics if d.get('status')!='PASS']).lower()
    return [name for name, words in ERROR_FAMILIES.items() if any(w in text for w in words)] or ['unclassified']


class ValidationRepair:
    def __init__(self, controller):self.controller=controller;self.store=controller.store

    def policy(self):
        revisions=self.store.records('repair_policy_revision')
        return max(revisions,key=lambda r:r['revision']) if revisions else {'revision':0,'attempts_before_human':3}

    def set_human_limit(self,limit,expected_limit,consent):
        if type(limit) is not int or not 1<=limit<=20 or not isinstance(consent,str) or not consent.strip():
            raise PolicyError('A bounded repair checkpoint and explicit consent are required')
        self.store.db.execute('BEGIN IMMEDIATE')
        try:
            current=self.policy()
            if current['attempts_before_human']!=expected_limit:
                raise PolicyError('Repair policy changed; inspect before amending')
            result=self.store.record('repair_policy_revision',{'revision':current['revision']+1,
                'attempts_before_human':limit,'previous_limit':expected_limit,'consent':consent,
                'preserved':'Existing attempts, run cap, campaign time/tokens and requirement approvals are unchanged'})
            self.store.db.execute('COMMIT')
            return result
        except BaseException:
            self.store.db.execute('ROLLBACK')
            raise

    def lineage(self, task_id):
        ids=set()
        while task_id:
            if task_id in ids:raise PolicyError('Cyclic development task lineage')
            ids.add(task_id)
            task_id=self.store.read_record('development_task',task_id).get('predecessor_task_id')
        return ids

    def family(self,task_id):
        """Share repair accounting across amendments and sibling branches."""
        ancestors=self.lineage(task_id)
        root=next(x for x in ancestors if not self.store.read_record('development_task',x).get('predecessor_task_id'))
        family={root};tasks=self.store.records('development_task')
        while True:
            expanded=family|{x['id'] for x in tasks if x.get('predecessor_task_id') in family}
            if expanded==family:return family
            family=expanded

    def attempts(self, task_id):
        lineage=self.family(task_id)
        executed={x['context_id'] for x in self.store.records('development_attempt_receipt')}
        return [x for x in self.store.records('development_generation_context') if x['task_id'] in lineage and x.get('development_retry') and ('attempt_id' not in x or x['id'] in executed)]

    def state(self, task_id):
        lineage=self.family(task_id)
        attempts=self.attempts(task_id)
        feedback=[x for x in self.store.records('development_human_guidance') if x['task_id'] in lineage]
        acknowledged=max([x['attempts_acknowledged'] for x in feedback]+[0])
        task=self.store.read_record('development_task',task_id)
        cap=self.controller.status(task['baseline_run_id'])['config']['budget']['repairs_per_run']
        count=len(attempts);round_count=count-acknowledged;limit=self.policy()['attempts_before_human']
        return {'total_repair_attempts':count,'round_repair_attempts':round_count,'repair_limit_before_human':limit,
            'run_repair_limit':cap,'human_guidance_required':round_count>=limit,'run_limit_reached':count>=cap,
            'latest_guidance':next((x for x in feedback if x['attempts_acknowledged']==acknowledged),None)}

    def diagnostics(self, result):
        if not result.get('generated_run_id'):return [{'gate':'model_response','status':'UNKNOWN','reason':result.get('reason','No checked generated model')}]
        run=self.controller.status(result['generated_run_id'])
        diagnostics=[]
        for gate in (run.get('result') or {}).get('gates',[]):
            item={k:gate.get(k) for k in ('gate','status','reason')}
            if gate.get('evidence'):
                evidence=self.store.load_object(gate['evidence'])
                item['tool_output']={k:str(evidence.get(k,''))[:12000] for k in ('stdout','stderr')}
            diagnostics.append(item)
        return diagnostics

    def report(self, result_id):
        result=self.store.read_record('development_result',result_id)
        task=self.store.read_record('development_task',result['task_id'])
        diagnostics=self.diagnostics(result);families=classify_errors(diagnostics)
        rules=Knowledge(self.store).draft_release(task['candidate_ids'])['rules'] if task['candidate_ids'] else []
        ranked=[]
        for rule in rules:
            r=rule['record'];text=json.dumps({k:r.get(k) for k in ('trigger','repair_gate','stack_layers','principle')}).lower()
            matches=[f for f in families if any(w in text for w in ERROR_FAMILIES.get(f,()))]
            ranked.append({'candidate_id':rule['id'],'rule_id':r['id'],'principle':r['principle'],
                'repair_guidance':r['repair_gate'],'matched_error_families':matches,
                'selection_reason':'Diagnostic keyword match; Astra must check prerequisites and exclusions' if matches else 'Selected task rule; relevance requires review'})
        ranked.sort(key=lambda r:(not bool(r['matched_error_families']),r['rule_id']))
        state=self.state(task['id'])
        # Human report may state graph status, but it never exports witnesses to repair context.
        comparison=self.store.read_record('development_golden_comparison',result['comparison_id']) if result.get('comparison_id') else {}
        return self.store.record('development_failure_report',{'result_id':result_id,'task_id':task['id'],
            'diagnostics':diagnostics,'error_families':families,'rules_consulted':ranked,
            'reported_rule_applications':result.get('generation_annotations',[]),
            'application_evidence_scope':'Model annotations are not independent proof of rule use',
            'architecture_status':comparison.get('architecture_status','NOT_RUN'),
            'repair_state':state,'question':str(state['repair_limit_before_human'])+' repair attempts have been made. Do you have a suggestion, or should this case remain stopped?' if state['human_guidance_required'] and result['status'] in ('NOT_VALIDATED','BLOCKED') else None,
            'whole_system_acceptance':False})

    def guidance(self, result_id, suggestion, reviewer, expected_attempts):
        result=self.store.read_record('development_result',result_id)
        if result['status'] not in ('NOT_VALIDATED','BLOCKED'):raise PolicyError('Select an unsuccessful result')
        if not isinstance(suggestion,str) or not suggestion.strip() or len(suggestion.encode())>16000 or not isinstance(reviewer,str) or not reviewer.strip():
            raise PolicyError('Provide a human suggestion and reviewer')
        state=self.state(result['task_id'])
        if type(expected_attempts) is not int or state['total_repair_attempts']!=expected_attempts:raise PolicyError('Repair history changed; inspect the current report')
        if not state['human_guidance_required']:raise PolicyError('Human continuation is available after the configured repair checkpoint')
        if state['run_limit_reached']:raise PolicyError('Run repair allowance exhausted; guidance cannot increase it')
        # No model response or agent annotation can grant this explicit UI/CLI action.
        return self.store.record('development_human_guidance',{'task_id':result['task_id'],'result_id':result_id,
            'suggestion':suggestion.strip(),'reviewer':reviewer.strip(),'attempts_acknowledged':expected_attempts,
            'authorization':'Continue up to '+str(state['repair_limit_before_human'])+' more repairs within existing run and campaign limits',
            'requirements_and_release_unchanged':True})
