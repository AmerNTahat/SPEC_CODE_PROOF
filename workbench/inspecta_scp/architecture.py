"""Capture real HAMR AIR/declarations and compare exact reviewed structural deltas.

No graph-isomorphism guessing, lexical architecture inference or proof claims.
"""
import copy
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re

from .approvals import Approvals
from .config import PolicyError, digest
from .storage import safe_child


TIME_UNITS = {'ps': '1', 'ns': '1000', 'us': '1000000', 'ms': '1000000000', 's': '1000000000000'}


def normalize(value):
    if isinstance(value, list):
        return [normalize(v) for v in value]
    if not isinstance(value, dict):
        return value
    # Only location metadata is excluded; contracts, initialization, classifiers,
    # resolved ownership, property values and unknown fields remain significant.
    result = {k: normalize(v) for k, v in value.items() if k not in {'pos', 'posOpt', 'opPosOpt', 'uriFrag'}}
    if result.get('type') == 'UnitProp':
        unit = result.get('unit', {}).get('value')
        if unit in TIME_UNITS:
            try:
                number = Decimal(result['value']) * Decimal(TIME_UNITS[unit])
                if not number.is_finite():
                    raise PolicyError('Nonfinite architecture property')
                result['value'] = format(number.normalize(), 'f')
                result['unit'] = {'type': 'Some', 'value': 'ps'}
            except (InvalidOperation, TypeError) as exc:
                raise PolicyError('Invalid numeric architecture property') from exc
    return result


def differences(left, right, path=()):
    if type(left) is not type(right):
        return [{'path': list(path), 'before': left, 'after': right}]
    if isinstance(left, dict):
        result = []
        for key in sorted(set(left) | set(right)):
            if key not in left or key not in right:
                result.append({'path': list(path + (key,)), 'kind': 'added' if key not in left else 'removed'})
            else:
                result.extend(differences(left[key], right[key], path + (key,)))
        return result
    if isinstance(left, list):
        if len(left) != len(right):
            return [{'path': list(path), 'before': left, 'after': right}]
        result = []
        for i, (a, b) in enumerate(zip(left, right)):
            result.extend(differences(a, b, path + (i,)))
        return result
    return [] if left == right else [{'path': list(path), 'before': left, 'after': right}]


def apply_delta(baseline, changes):
    expected = copy.deepcopy(baseline)
    seen = []
    for change in changes:
        if not isinstance(change, dict) or set(change) != {'path', 'before', 'after', 'rationale'}:
            raise PolicyError('Each approved delta needs path, exact before/after and rationale')
        path = change['path']
        if not isinstance(path, list) or not path or not isinstance(change['rationale'], str) or not change['rationale'].strip():
            raise PolicyError('Nonempty delta path and review rationale required')
        if any(path[:len(p)] == p or p[:len(path)] == path for p in seen):
            raise PolicyError('Overlapping architecture changes are ambiguous')
        seen.append(path)
        parent = expected
        try:
            for part in path[:-1]:
                if type(part) is int and part < 0:
                    raise PolicyError('Negative delta index')
                parent = parent[part]
            key = path[-1]
            if type(key) is int and key < 0:
                raise PolicyError('Negative delta index')
            if parent[key] != change['before']:
                raise PolicyError('Delta before-value does not match baseline')
            parent[key] = copy.deepcopy(change['after'])
        except (KeyError, IndexError, TypeError) as exc:
            raise PolicyError('Delta path does not resolve') from exc
    return expected


def element_index(models):
    elements = {}
    def add(key, kind, owner, value):
        if key in elements:
            raise PolicyError('Duplicate resolved architecture identity: ' + key)
        elements[key] = {'kind': kind, 'owner': owner, 'sha256': digest(normalize(value))}
    def component(value, owner=None):
        if value.get('type') != 'Component':
            raise PolicyError('Unsupported component representation')
        name = '::'.join(value['identifier']['name'])
        add(name, 'component', owner, value)
        for feature in value['features']:
            add('::'.join(feature['identifier']['name']), 'port', name, feature)
        for connection in value['connections']:
            add('::'.join(connection['name']['name']), 'connection', name, connection)
        def contracts(node):
            if isinstance(node, dict):
                if node.get('type') in {'GclGuarantee', 'GclAssume'}:
                    add(name + '#'+ node['id'], node['type'], name, node)
                for child in node.values():
                    contracts(child)
            elif isinstance(node, list):
                for child in node:
                    contracts(child)
        contracts(value['annexes'])
        for child in value['subComponents']:
            component(child, name)
    for model in models.values():
        if model.get('type') != 'Aadl' or not model.get('components'):
            raise PolicyError('Missing instantiated HAMR architecture')
        for value in model['components']:
            component(value)
    return elements


class Architecture:
    def __init__(self, controller):
        self.controller = controller
        self.store = controller.store
        self.approvals = Approvals(self.store)

    def capture(self, run_id, config, folder):
        record, output, interrupted = self.controller._run_tool(run_id, config, folder, 'architecture_capture')
        record['scope'] = 'Real HAMR instantiated AIR and resolved package declarations; not behavior proof or engineering acceptance'
        reason = 'Architecture export did not complete'
        status = 'UNKNOWN'
        snapshot = None
        if interrupted:
            reason = 'Architecture export interrupted: ' + interrupted
        elif record['exit_code'] != 0:
            status = 'FAIL' if 'INSPECTA_ARCHITECTURE_REJECTED' in record['stdout'] + record['stderr'] else 'UNKNOWN'
            reason = 'Trusted architecture export rejected or could not start'
        elif 'Instantiation Warning' in record['stdout'] or 'MISSING_AADL_TYPE' in record['stdout']:
            reason = 'Unresolved instantiation warnings block structural acceptance'
        else:
            match = re.search(r'^INSPECTA_ARCHITECTURE_EXPORTED:(\d+)$', record['stdout'], re.M)
            if match and int(match[1]) > 0:
                files = list(output.iterdir())
                if any(p.is_symlink() or not p.is_file() for p in files) or sum(p.stat().st_size for p in files) > 64 * 1024 * 1024:
                    raise PolicyError('Unsafe or excessive architecture output')
                models = {}
                for i in range(int(match[1])):
                    model = json.loads(safe_child(output, 'model-' + str(i) + '.json').read_text())
                    key = '::'.join(model['components'][0]['identifier']['name'])
                    if key in models:
                        raise PolicyError('Duplicate model identity')
                    models[key] = model
                declarations = {}
                for line in safe_child(output, 'declarations.tsv').read_text().splitlines():
                    index, name = line.split('\t', 1)
                    if not index.isdigit() or name in declarations:
                        raise PolicyError('Malformed declaration export')
                    declarations[name] = json.loads(safe_child(output, 'declaration-' + index + '.json').read_text())
                if not declarations:
                    raise PolicyError('Missing resolved declarations')
                value = {'models': models, 'declarations': declarations}
                snapshot = self.store.record('architecture_snapshot', {
                    'run_id': run_id, 'config_hash': record['config_sha256'],
                    'input_manifest_sha256': record['input_manifest_sha256'],
                    'tool_identity': record['tool_identity'], 'raw': self.store.object(value),
                    'normalized': self.store.object(normalize(value)), 'elements': element_index(models),
                    'status': 'CAPTURED_NOT_APPROVED', 'normalization': 'hamr-position-free-time-ps-v2'})
                record['snapshot_id'] = snapshot['id']
                status, reason = 'PASS', 'Instantiated AIR and resolved declarations captured; no conformance claim'
        return {'gate': 'architecture_capture', 'status': status, 'reason': reason,
                'snapshot_id': snapshot['id'] if snapshot else None,
                'evidence': self.store.object(record)}, interrupted

    def propose(self, snapshot_id, changes=None):
        snapshot = self.store.read_record('architecture_snapshot', snapshot_id)
        baseline = self.store.load_object(snapshot['normalized'])
        changes = [] if changes is None else changes
        expected = apply_delta(baseline, changes)
        # Resolve identities now: a delta may not manufacture duplicate owners.
        element_index(expected['models'])
        return self.store.record('architecture_policy', {'baseline_id': snapshot_id, 'changes': changes,
            'expected': self.store.object(expected), 'mode': 'approved-change' if changes else 'equivalence',
            'normalization': snapshot['normalization'], 'status': 'DRAFT_REQUIRES_APPROVAL'})

    def request_review(self, policy_id):
        policy = self.store.read_record('architecture_policy', policy_id)
        return self.approvals.request('approve_architecture', {'policy_id': policy_id, 'policy_digest': digest(policy)})

    def approved(self, policy_id):
        policy = self.store.read_record('architecture_policy', policy_id)
        subject = {'policy_id': policy_id, 'policy_digest': digest(policy)}
        request = self.approvals.request('approve_architecture', subject)
        self.approvals.require(request['id'], 'approve_architecture', subject)
        return policy

    def check(self, policy_id, capture):
        result = {**capture, 'gate': 'architecture'}
        if capture['status'] != 'PASS':
            return result
        if not policy_id:
            return {**result, 'status': 'NOT_RUN', 'reason': 'Reviewed architecture policy required'}
        policy = self.approved(policy_id)
        baseline = self.store.read_record('architecture_snapshot', policy['baseline_id'])
        current = self.store.read_record('architecture_snapshot', capture['snapshot_id'])
        if baseline['tool_identity'] != current['tool_identity'] or baseline['normalization'] != current['normalization']:
            return {**result, 'status': 'UNKNOWN', 'reason': 'Tool or normalization differs from approved baseline'}
        expected = self.store.load_object(policy['expected'])
        actual = self.store.load_object(current['normalized'])
        delta = differences(expected, actual)
        evidence = self.store.object({'policy_id': policy_id, 'snapshot_id': current['id'],
                                     'capture_evidence': capture['evidence'], 'differences': delta})
        return {**result, 'status': 'FAIL' if delta else 'PASS', 'evidence': evidence,
                'reason': str(len(delta)) + ' unapproved structural/declaration differences',
                'scope': 'Exact normalized HAMR/declaration conformance; not semantic requirement fidelity'}
