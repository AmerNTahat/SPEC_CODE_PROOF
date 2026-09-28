"""Human acceptance of one checked golden scope, separate from reusable-rule release."""
from .approvals import Approvals
from .config import PolicyError,digest


class BehaviorAcceptance:
    def __init__(self,controller):
        self.controller=controller;self.store=controller.store;self.approvals=Approvals(self.store)

    def evidence(self,result_id):
        result=self.store.read_record('development_result',result_id)
        task=self.store.read_record('development_task',result['task_id'])
        generated=self.controller.status(result['generated_run_id'])
        reference=self.controller.status(result['reference_run_id'])
        blockers=[]
        for name,run in [('Generated',generated),('Golden',reference)]:
            if not run.get('evidence_current_for_source') or not run.get('policy_current'):
                blockers.append(name+' evidence is stale or its policy changed')
        # Human review below supplies the review decision, never a missing proof.
        gates=set(generated['config']['required_gates'])-{'review'}
        gates.update({'parse_type','configured_formal_verification','independent_requirements_tests'})
        results={g['gate']:g for g in (generated.get('result') or {}).get('gates',[])}
        for gate in sorted(gates):
            g=results.get(gate,{})
            if g.get('status')!='PASS' or not g.get('evidence'):
                blockers.append(gate+': '+g.get('status','NOT_RUN'))
        # A current directed graph check supplies reference correspondence only.
        from .development import Development
        try:
            graph=Development(self.controller).compare_graph(result_id)
            if graph['graph']['status']!='PASS':blockers.append('Golden architecture comparison did not pass')
            graph_id=graph['id']
        except PolicyError as exc:
            graph_id=None;blockers.append(str(exc))
        scope=None
        if task.get('capability_scope_id'):
            from .capability_scope import CapabilityScope
            try:
                scope=CapabilityScope(self.controller).bind(task['capability_scope_id'],task.get('prepared_requirements_id'),generated['config'])
            except PolicyError as exc:blockers.append(str(exc))
        return {'result_id':result_id,'task_id':task['id'],'generated_run_id':generated['id'],
            'reference_run_id':reference['id'],'generated_evidence_digest':digest(generated.get('result')),
            'reference_evidence_digest':digest(reference.get('result')),'graph_assessment_id':graph_id,
            'required_checks':sorted(gates),'capability_scope_id':task.get('capability_scope_id'),
            'excluded_requirements':[r for r in (scope or {}).get('targets',[]) if not r['mandatory_in_scoped_validation']],
            'blockers':blockers,'rule_transfer_required':False,
            'acceptance_scope':'This generated model against this reviewed golden scope only; no full-PDF claim and no reusable-rule publication.'}

    def prepare(self,result_id):
        evidence=self.evidence(result_id)
        record=self.store.record('behavior_acceptance_review',evidence)
        self.approvals.request('accept_golden_behavior',{'review_id':record['id'],'review_digest':digest(record)})
        return self.inspect(record['id'])

    def inspect(self,key):
        record=self.store.read_record('behavior_acceptance_review',key)
        approval=self.approvals.request('accept_golden_behavior',{'review_id':key,'review_digest':digest(record)})
        current=self.evidence(record['result_id'])
        unchanged=digest(current)==digest({k:v for k,v in record.items() if k!='id'})
        ready=unchanged and not current['blockers']
        return {**record,'approval':approval,'checks_current':unchanged,'ready_for_review':ready,
            'current_blockers':current['blockers']+([] if unchanged else ['Evidence changed; prepare a new review']),
            'status':'ACCEPTED_GOLDEN_SCOPE' if ready and approval['status']=='APPROVED' else ('READY_FOR_HUMAN_REVIEW' if ready else 'CHECKS_INCOMPLETE'),
            'whole_system_acceptance':False,'publishes_rules':False}
