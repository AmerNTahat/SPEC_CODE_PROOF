"""Count human-curated golden defect repairs separately from unchanged-reference passes."""
import json
import re
from pathlib import Path
from .config import PolicyError, digest
from .storage import sha_file


class GoldenDefects:
    def __init__(self, controller):
        self.controller = controller
        self.store = controller.store

    def register(self, *, title, target, requirement_ids, comment, consent, citations,
                 artifacts, model_report, verification_report, contradiction_report, component, open_obligations, environmental_assumptions=None):
        if not all(isinstance(x, str) and x.strip() for x in (title, target, comment, consent, component)):
            raise PolicyError('Golden defect curation requires human consent, comment and exact target')
        if not requirement_ids or not citations or not artifacts:
            raise PolicyError('Cite the contradiction, English basis and repaired artifacts')
        environmental_assumptions = environmental_assumptions or []
        for assumption in environmental_assumptions:
            required = ('id', 'boundary', 'predicate', 'source_citation', 'human_consent', 'allocation', 'mapping_status')
            if any(not isinstance(assumption.get(k), str) or not assumption[k].strip() for k in required):
                raise PolicyError('An environmental premise requires exact boundary, predicate, source, consent and allocation')
            if assumption['mapping_status'] not in ('DECLARED_NOT_PROVED', 'PROVED'):
                raise PolicyError('Unknown assumption mapping status')
            # This action declares an external premise, not a composition proof.
            if assumption['mapping_status'] == 'PROVED':
                raise PolicyError('Environmental approval cannot establish an internal propagation proof')
        bound = []
        for name in dict.fromkeys([*artifacts, model_report, verification_report, contradiction_report]):
            path = Path(name).resolve()
            bound.append({'path': str(path), 'sha256': sha_file(path)})
        case_key = digest({'target': target, 'requirements': sorted(requirement_ids)})
        revision = 1 + max([r.get('revision', 0) for r in self.store.records('golden_defect_review') if r.get('case_key') == case_key] + [0])
        return self.store.record('golden_defect_review', {
            'case_key': case_key, 'revision': revision, 'contradiction_report': str(Path(contradiction_report).resolve()),
            'title': title, 'target': target, 'requirement_ids': requirement_ids,
            'comment': comment, 'human_consent': consent, 'citations': citations,
            'artifacts': bound, 'model_report': str(Path(model_report).resolve()),
            'verification_report': str(Path(verification_report).resolve()), 'component': component,
            'open_obligations': open_obligations,
            'environmental_assumptions': environmental_assumptions,
            'scope': 'Conditional component repair of a documented golden contradiction; original evidence retained',
        })

    def inspect(self, record):
        blockers = []
        for artifact in record['artifacts']:
            try:
                if sha_file(artifact['path']) != artifact['sha256']:
                    blockers.append('Evidence changed: ' + artifact['path'])
            except OSError:
                blockers.append('Missing evidence: ' + artifact['path'])
        try:
            diagnosis = json.loads(Path(record['contradiction_report']).read_text())
            observed = {c['name']: c for c in diagnosis['checks']}
            for name, expected in [('overlap_within_desired_range', 'sat'), ('same_witness_both_guarantees', 'unsat')]:
                check = observed.get(name, {})
                if check.get('exit_code') != 0 or check.get('stdout', '').strip() != expected:
                    blockers.append('Golden contradiction diagnostic missing or unsuccessful: ' + name)
            model = json.loads(Path(record['model_report']).read_text())['run']
            proof = json.loads(Path(record['verification_report']).read_text())
            gates = {g['gate']: g['status'] for g in model['result']['gates']}
            for gate in ('parse_type', 'hamr_codegen'):
                if gates.get(gate) != 'PASS': blockers.append(gate + ' did not pass')
            if proof['source_run_id'] != model['id']: blockers.append('Proof belongs to another model')
            workspace = Path(proof['workspace']).resolve()
            if not proof.get('source_rs_sha256'): blockers.append('Missing checked source inventory')
            for name, expected in proof.get('source_rs_sha256', {}).items():
                path = (workspace / name).resolve()
                if not path.is_relative_to(workspace) or sha_file(path) != expected:
                    blockers.append('Checked Rust changed: ' + name)
            checks = {c['kind']: c for c in proof['checks'] if c['crate'] == record['component']}
            for kind in ('verus', 'gumbo_tests'):
                check = checks.get(kind, {})
                output = check.get('stdout', '') + check.get('stderr', '')
                pattern = r'verification results:: [1-9][0-9]* verified, 0 errors' if kind == 'verus' else r'test result: ok\. [1-9][0-9]* passed; 0 failed'
                valid_output = bool(re.search(pattern, output))
                if kind == 'verus':
                    summaries = re.findall(r'verification results:: ([0-9]+) verified, ([0-9]+) errors', output)
                    valid_output = bool(summaries) and int(summaries[-1][0]) > 0 and all(int(errors) == 0 for _, errors in summaries)
                if check.get('exit_code') != 0 or not valid_output:
                    blockers.append(kind + ': passing component evidence required')
            if not proof.get('source_rs_preserved'): blockers.append('Source changed during verification')
        except (OSError, ValueError, KeyError, TypeError) as exc:
            blockers.append('Cannot validate repair evidence: ' + str(exc))
        accepted = not blockers and bool(record.get('human_consent'))
        return {**record, 'status': 'REPAIRED_GOLDEN_DEFECT_ACCEPTED_BY_HUMAN' if accepted else 'GOLDEN_DEFECT_REPAIR_CHECKS_INCOMPLETE',
                'blockers': blockers, 'counts_as_accepted_repair_case': accepted,
                'unchanged_golden_pass': False, 'whole_system_acceptance': False,
                'rule_transfer_accepted': False,
                'criterion': 'Cited golden contradiction + explicit human curation + current repaired artifact + passing scoped parser/codegen/Verus/GUMBOX checks. Approved environmental premises are external conditions, not software guarantees. Preserve internal propagation and remaining system obligations.'}

    def catalog(self):
        latest = {}
        for r in self.store.records('golden_defect_review'):
            key = r.get('case_key', r['id'])
            if key not in latest or r.get('revision', 0) > latest[key].get('revision', 0): latest[key] = r
        records = [self.inspect(r) for r in latest.values()]
        return {'cases': records,
                'accepted_repair_cases': sum(r['counts_as_accepted_repair_case'] for r in records),
                'pending_repair_cases': sum(not r['counts_as_accepted_repair_case'] for r in records),
                'counting_scope': 'Defect cases, not proof subgoals or whole-system passes; each case retains its corrected reference scope.'}
