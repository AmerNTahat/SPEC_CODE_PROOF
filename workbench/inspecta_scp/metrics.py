"""Fixed reviewed units and one metrics calculation shared by CLI/UI/exports."""
import csv
import json
import math
import os
from pathlib import Path
import tempfile
import time

from .approvals import Approvals
from .config import PolicyError, digest, relative_file
from .requirements import Requirements
from .storage import sha_file


def calculate(targets, verified, accepted, wall_seconds, total_tokens, cost_usd):
    if targets is not None and (not targets or len(set(targets)) != len(targets)):
        raise PolicyError('Registry targets must be nonempty and unique')
    if len(set(verified)) != len(verified) or len(set(accepted)) != len(accepted):
        raise PolicyError('Duplicate measured unit')
    if not set(accepted) <= set(verified) or not set(verified) <= set(targets or []):
        raise PolicyError('Accepted/verified units must belong to the fixed registry')
    for value in (wall_seconds,total_tokens,cost_usd):
        if value is not None and (type(value) not in (int,float) or not math.isfinite(value) or value < 0):
            raise PolicyError('Measurements must be nonnegative, finite or unknown')
    n=len(verified)
    return {'registered_count':len(targets) if targets else None,'verified_count':n,'accepted_count':len(accepted),
            'coverage':n/len(targets) if targets else None,'wall_seconds':wall_seconds,'total_tokens':total_tokens,'cost_usd':cost_usd,
            'verified_per_minute':n/(wall_seconds/60) if wall_seconds and targets else None,
            'tokens_per_verified_unit':total_tokens/n if n and total_tokens is not None else None,
            'dollars_per_verified_unit':cost_usd/n if n and cost_usd is not None else None}


class Metrics:
    def __init__(self,controller):self.controller=controller;self.store=controller.store;self.approvals=Approvals(self.store)

    def propose(self,value):
        if not isinstance(value,dict) or set(value)-{'definition_id'}!={'benchmark_id','ledger_id','snapshot_id','units'}:
            raise PolicyError('Registry needs benchmark_id, ledger_id, snapshot_id and units')
        if not isinstance(value['benchmark_id'],str) or not value['benchmark_id'].strip() or not value['units']:
            raise PolicyError('Named benchmark and nonempty fixed unit inventory required')
        if value.get('definition_id'):
            from .unit_definitions import UnitDefinitions
            UnitDefinitions(self.store).approved(value['definition_id'])
        ledger=Requirements(self.store).approved(value['ledger_id'])
        obligations={o['id'] for o in ledger['record']['obligations']}
        snapshot=self.store.read_record('architecture_snapshot',value['snapshot_id'])
        ids=set();members=set();requirement_members=set()
        for unit in value['units']:
            typed='unit_kind' in unit
            if set(unit)-({'unit_kind','assumption_element_ids'} if typed else set())!={'id','obligation_ids','formal_element_ids','implementation_files','formal_gate_ids'}:
                raise PolicyError('Each unit needs exact source, formal and implementation mappings')
            structural=unit.get('unit_kind')=='structural-conformance'
            if typed:
                if not value.get('definition_id') or unit['unit_kind'] not in {'structural-conformance','behavioral-contract'}:
                    raise PolicyError('Typed units require an approved definition and recognized kind')
                if len(unit['obligation_ids'])!=1 or set(unit['obligation_ids']) & requirement_members:
                    raise PolicyError('Count one atomic requirement once across all unit kinds')
                requirement_members.update(unit['obligation_ids'])
                if not isinstance(unit.get('assumption_element_ids'),list) or len(set(unit['assumption_element_ids']))!=len(unit['assumption_element_ids']):
                    raise PolicyError('Declare unique assumption mappings, including an explicit empty list')
                for assumption in unit['assumption_element_ids']:
                    if snapshot['elements'].get(assumption,{}).get('kind')!='GclAssume':
                        raise PolicyError('Assumption mapping must resolve to an actual assumption')
            if not isinstance(unit['id'],str) or not unit['id'].strip() or unit['id'] in ids:raise PolicyError('Duplicate/empty unit ID')
            ids.add(unit['id'])
            if not unit['obligation_ids'] or len(set(unit['obligation_ids']))!=len(unit['obligation_ids']) or not set(unit['obligation_ids'])<=obligations:
                raise PolicyError('Unit obligations must resolve to the reviewed ledger')
            if not unit['formal_element_ids'] or len(set(unit['formal_element_ids']))!=len(unit['formal_element_ids']):raise PolicyError('Nonempty unique formal targets required')
            for element in unit['formal_element_ids']:
                kinds={'component','port','connection'} if structural else {'GclGuarantee'}
                if element in members or snapshot['elements'].get(element,{}).get('kind') not in kinds:
                    raise PolicyError('Formal target missing, not a guarantee, or counted by multiple units')
                members.add(element)
            expected=['architecture_capture'] if structural else ['configured_formal_verification']
            if unit['formal_gate_ids']!=expected:raise PolicyError('Unit requires its trusted typed verification gate')
            if typed:
                obligation=next(o for o in ledger['record']['obligations'] if o['id']==unit['obligation_ids'][0])
                if not set(unit['formal_element_ids'])<=set(obligation['mapped_elements']):
                    raise PolicyError('Unit targets must belong to its reviewed requirement mapping')
                if structural and obligation['representation'] not in {'architecture','timing','deployment'}:
                    raise PolicyError('Structural unit requires a structural requirement')
                if not structural and obligation['representation']!='behavior_contract':
                    raise PolicyError('Behavioral unit requires a behavioral requirement')
            if not unit['implementation_files'] or len(set(unit['implementation_files']))!=len(unit['implementation_files']):raise PolicyError('Implementation source mapping required')
            for path in unit['implementation_files']:relative_file(path)
        return self.store.record('unit_registry',{'record':value,'status':'DRAFT_REQUIRES_REVIEW'})

    def request_review(self,registry_id):
        registry=self.store.read_record('unit_registry',registry_id)
        return self.approvals.request('approve_registry',{'registry_id':registry_id,'registry_digest':digest(registry)})

    def approved(self,registry_id):
        registry=self.store.read_record('unit_registry',registry_id)
        Requirements(self.store).approved(registry['record']['ledger_id'])
        if registry['record'].get('definition_id'):
            from .unit_definitions import UnitDefinitions
            UnitDefinitions(self.store).approved(registry['record']['definition_id'])
        subject={'registry_id':registry_id,'registry_digest':digest(registry)}
        request=self.approvals.request('approve_registry',subject)
        self.approvals.require(request['id'],'approve_registry',subject)
        return registry

    def _structural_unit_conforms(self, run, gate, unit, registry):
        """Compare exact resolved elements with the reviewed reference inventory."""
        if gate.get('status')!='PASS' or not gate.get('snapshot_id') or not gate.get('evidence'):
            return False
        try:
            actual=self.store.read_record('architecture_snapshot',gate['snapshot_id'])
            reference=self.store.read_record('architecture_snapshot',registry['record']['snapshot_id'])
            if actual.get('normalization')!=reference.get('normalization') or actual.get('tool_identity')!=reference.get('tool_identity'):return False
            reference_run=self.controller.status(reference['run_id'])
            if not reference_run.get('evidence_current_for_source') or not reference_run.get('policy_current'):return False
            manifest=json.loads((self.store.root/'runs'/run['id']/'input-workspace-manifest.json').read_text())
            if actual['run_id']!=run['id'] or actual['config_hash']!=run['config_hash'] or actual['input_manifest_sha256']!=digest(manifest):return False
            evidence=self.store.load_object(gate['evidence'])
            if evidence.get('snapshot_id')!=actual['id'] or evidence.get('run_id')!=run['id']:return False
            return all(key in reference['elements'] and actual['elements'].get(key)==reference['elements'][key] for key in unit['formal_element_ids'])
        except (PolicyError,OSError,ValueError,TypeError,KeyError):return False

    def _formal_unit_verified(self, run, gate, unit):
        """Reject labels and dangling references; bind every obligation to this run."""
        if gate.get('status') != 'PASS' or not isinstance(gate.get('evidence'), dict):
            return False
        try:
            manifest = json.loads((self.store.root / 'runs' / run['id'] / 'input-workspace-manifest.json').read_text())
            binding = {'run_id': run['id'], 'config_sha256': run['config_hash'],
                       'input_manifest_sha256': digest(manifest)}
            evidence = self.store.load_object(gate['evidence'])
            if any(evidence.get(k) != v for k, v in binding.items()):
                return False
            records = evidence.get('unit_checks', {}).get(unit['id'], [])
            resolved = {r['element_id']: r for r in records}
            if len(resolved) != len(records) or set(resolved) != set(unit['formal_element_ids']):
                return False
            for element, record in resolved.items():
                if record.get('status') != 'PASS' or not isinstance(record.get('evidence_ref'), dict):
                    return False
                obligation = self.store.load_object(record['evidence_ref'])
                expected = {**binding, 'element_id': element, 'unit_id': unit['id'],
                            'gate': 'configured_formal_verification', 'status': 'PASS'}
                if any(obligation.get(k) != v for k, v in expected.items()):
                    return False
            return True
        except (PolicyError, OSError, ValueError, TypeError, KeyError, AttributeError):
            return False

    def report(self,run_id):
        run=self.controller.status(run_id);events=self.store.events(run_id)
        registry_id=run['config'].get('unit_registry')
        targets=None;units=[];verified=[];accepted=[];structural_targets=[];conforming=[]
        registry=None;problems=[]
        if registry_id:
            try:registry=self.approved(registry_id)
            except PolicyError as exc:problems.append(str(exc))
        else:problems.append('No reviewed unit registry; denominator/coverage remain unknown')
        gates={g['gate']:g for g in (run.get('result') or {}).get('gates',[])}
        current=run.get('evidence_current_for_source',False) and run.get('policy_current',False)
        if registry:
            if any(u.get('unit_kind')=='behavioral-contract' for u in registry['record']['units']):
                problems.append('Requirement-linked behavioral units require an assumption-discharge adapter; none is implemented')
            targets=[u['id'] for u in registry['record']['units'] if u.get('unit_kind')!='structural-conformance'] or None
            structural_targets=[u['id'] for u in registry['record']['units'] if u.get('unit_kind')=='structural-conformance']
            for unit in registry['record']['units']:
                if unit.get('unit_kind')=='structural-conformance':
                    conforms=current and self._structural_unit_conforms(run,gates.get('architecture_capture',{}),unit,registry)
                    if conforms:conforming.append(unit['id'])
                    units.append({**unit,'verified':False,'accepted':False,'current':current,'structural_conforms':conforms,
                        'scope':'Exact reviewed resolved-element conformance; not behavioral proof or requirement-fidelity acceptance'})
                    continue
                checks=[]
                for gate_id in unit['formal_gate_ids']:
                    gate=gates.get(gate_id,{})
                    checks.append(self._formal_unit_verified(run, gate, unit))
                # A typed assume/guarantee definition additionally requires a
                # trusted assumption-discharge adapter, currently unavailable.
                is_verified=current and bool(checks) and all(checks) and 'unit_kind' not in unit
                if is_verified:verified.append(unit['id'])
                # Acceptance needs unit-specific independent validation as well;
                # current adapters do not establish it, so no units are inferred accepted.
                units.append({**unit,'verified':is_verified,'accepted':False,'current':current,
                    'scope':'Actual unit-specific formal obligations required; parser or mapped labels do not count'})
        terminal=run['state'] in {'CHECKED','BLOCKED','FAILED','CANCELLED','BUDGET_EXHAUSTED'}
        end=events[-1]['timestamp'] if terminal else time.time()
        wall=max(0,end-run['created'])
        total=None if run['usage_unknown'] else run['used_tokens']
        calculated=calculate(targets,verified,accepted,wall,total,None)
        return {**calculated,'run_id':run_id,'config_hash':run['config_hash'],'registry_id':registry_id,
            'measurement_kind':'recorded_application_run','unit_results':units,'verified_ids':verified,'accepted_ids':accepted,
            'structural_registered_count':len(structural_targets) if registry else None,
            'structural_conforming_count':len(conforming),'structural_conforming_ids':conforming,
            'structural_coverage':len(conforming)/len(structural_targets) if structural_targets else None,
            'requirement_registered_count':len(registry['record']['units']) if registry else None,
            'evidence_current':current,'end_to_end_success':False,'problems':problems,
            'repair_attempts':sum(r['run_id']==run_id for r in self.store.records('repair_candidate')),
            'scope':'Current trusted run evidence; no reconstructed historical 42-unit denominator or inferred billing',
            'run_state':run['state'],'budget':run['config']['budget']}

    def export(self,run_id,output,plots=True):
        output=Path(output).absolute()
        if output.exists() or any(p.is_symlink() for p in [output,*output.parents]):raise PolicyError('Use a new safe report directory')
        report=self.report(run_id)
        output.mkdir(parents=True)
        (output/'metrics.json').write_text(json.dumps(report,indent=2)+'\n')
        scalar={k:v for k,v in report.items() if not isinstance(v,(dict,list))}
        with (output/'metrics.csv').open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(scalar));writer.writeheader();writer.writerow(scalar)
        figures=[]
        if plots:
            os.environ.setdefault('MPLCONFIGDIR',str(Path(tempfile.gettempdir())/'inspecta-matplotlib'))
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            matplotlib.rcParams['svg.hashsalt']='inspecta-metrics-v1'
            for field,label in [('coverage','Verified fraction of registered units'),('verified_per_minute','Verified units / wall minute'),
                                ('total_tokens','Aggregate model tokens'),('tokens_per_verified_unit','Tokens / verified unit'),
                                ('cost_usd','Recorded billing (USD)'),('dollars_per_verified_unit','USD / verified unit')]:
                fig,ax=plt.subplots(figsize=(6,4));value=report[field]
                if value is None:
                    ax.text(.5,.5,'Undefined / not established',ha='center',va='center',transform=ax.transAxes)
                    ax.set_ylim(0,1)
                else:
                    ax.bar([0],[value]);ax.set_ylim(0,max(1,value*1.2))
                ax.set_xticks([0],[run_id[:12]]);ax.set_ylabel(label)
                fig.text(.02,.02,'RECORDED CHECKS — no engineering acceptance inferred',fontsize=8)
                fig.tight_layout(rect=[0,.06,1,1])
                for extension in ('png','svg','pdf'):
                    filename=field+'.'+extension
                    fig.savefig(output/filename,metadata={'Date':None} if extension=='svg' else {'CreationDate':None,'ModDate':None} if extension=='pdf' else {})
                    figures.append(filename)
                plt.close(fig)
        manifest={'run_id':run_id,'config_hash':report['config_hash'],'registry_id':report['registry_id'],
            'scope':report['scope'],'files':{p.name:sha_file(p) for p in output.iterdir() if p.is_file()}}
        (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        return {'output':str(output),'figures':figures,'report':report,'manifest_sha256':sha_file(output/'manifest.json')}
