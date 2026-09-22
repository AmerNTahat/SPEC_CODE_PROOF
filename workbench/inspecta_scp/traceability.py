"""Human-only drill-down from recorded runs; missing links stay explicit."""
import hashlib
import json

from .config import PolicyError, digest, relative_file
from .metrics import Metrics
from .storage import safe_child


class Traceability:
    def __init__(self, controller):
        self.controller = controller
        self.store = controller.store

    def manifest(self, run_id):
        self.store.get(run_id)
        snapshot = next((e for e in self.store.events(run_id) if e['kind'] == 'snapshot'), None)
        if snapshot is None:
            raise PolicyError('No recorded input snapshot')
        manifest = self.store.load_object(snapshot['payload'])
        disk = json.loads(safe_child(self.store.root, 'runs/' + run_id + '/input-workspace-manifest.json').read_text())
        if digest(disk) != digest(manifest):
            raise PolicyError('Input manifest changed since snapshot')
        return manifest

    def input(self, run_id, relative):
        relative = relative_file(relative)
        manifest = self.manifest(run_id)
        if relative not in manifest['files']:
            raise PolicyError('File is not in this run input allowlist')
        path = safe_child(self.store.root, 'runs/' + run_id + '/candidate/' + relative)
        if path.stat().st_size > 4 * 1024 * 1024:
            raise PolicyError('Input exceeds source viewer limit')
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != manifest['files'][relative]:
            raise PolicyError('Input snapshot was modified')
        run = self.controller.status(run_id)
        return {'run_id': run_id, 'relative': relative, 'sha256': manifest['files'][relative],
                'text': data.decode('utf-8'), 'original_source_current': relative not in run['source_changed'],
                'scope': 'Exact run snapshot for human review; not exported to a model'}

    def evidence(self, run_id, sha256):
        run = self.store.get(run_id)
        references = [g['evidence'] for g in (run['result'] or {}).get('gates', []) if g.get('evidence')]
        reference = next((r for r in references if r['sha256'] == sha256), None)
        if reference is None:
            raise PolicyError('Evidence is not directly attached to this run result')
        return {'run_id': run_id, 'sha256': sha256, 'record': self.store.load_object(reference),
                'scope': 'Human-only executed evidence; tool scope and limitations apply'}

    def report(self, run_id):
        run = self.controller.status(run_id)
        config = run['config']
        manifest = self.manifest(run_id)
        ledger = self.store.read_record('requirement_ledger', config['requirement_ledger']) if config.get('requirement_ledger') else None
        metrics = Metrics(self.controller).report(run_id)
        gates = (run['result'] or {}).get('gates', [])
        snapshots = {}
        for gate in gates:
            if gate.get('snapshot_id'):
                snapshot = self.store.read_record('architecture_snapshot', gate['snapshot_id'])
                snapshots[snapshot['id']] = snapshot['elements']
        obligations = {o['id']: o for o in ledger['record']['obligations']} if ledger else {}
        units = []
        for unit in metrics['unit_results']:
            units.append({**unit, 'obligations': [obligations[i] for i in unit['obligation_ids'] if i in obligations],
                          'formal_elements': {element: [elements[element] for elements in snapshots.values() if element in elements]
                                              for element in unit['formal_element_ids']},
                          'implementation_sources': [{'path': p, 'sha256': manifest['files'].get(p)} for p in unit['implementation_files']],
                          'gates': [g for g in gates if g['gate'] in unit['formal_gate_ids']],
                          'applied_rule_bindings': [], 'rule_binding_status': 'No executed rule-binding record established'})
        return {'run_id': run_id, 'config_hash': run['config_hash'], 'state': run['state'],
                'current': run['evidence_current_for_source'] and run['policy_current'],
                'sources': [{'path': p, 'sha256': sha} for p, sha in manifest['files'].items()],
                'ledger_id': config.get('requirement_ledger'), 'obligations': list(obligations.values()),
                'registry_id': config.get('unit_registry'), 'units': units, 'gates': gates,
                'architecture_snapshots': snapshots, 'configured_rule_release': config.get('rule_release'),
                'missing_links': ([] if ledger else ['No reviewed requirement ledger']) +
                                 ([] if config.get('unit_registry') else ['No reviewed unit registry']) +
                                 ['No executed rule-binding provenance established'],
                'scope': 'Recorded relationships only; unresolved links and unsupported acceptance remain explicit'}
