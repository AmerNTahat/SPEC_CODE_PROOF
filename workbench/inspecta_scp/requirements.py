"""Source-backed, immutable reviewed obligations and resolved-element coverage."""
from .approvals import Approvals
from .config import GATES, PolicyError, digest
from .knowledge import validate_schema
from .sources import Sources


class Requirements:
    def __init__(self, store):
        self.store = store
        self.sources = Sources(store)
        self.approvals = Approvals(store)

    def propose(self, value):
        validate_schema(value, 'requirements.schema.json')
        if value['state'] != 'DRAFT' or value['approval_reference'] is not None:
            raise PolicyError('Only unapproved requirement drafts can be proposed')
        if not value['project_id'].strip() or value['project_id'] == 'UNRESOLVED' or not value['obligations']:
            raise PolicyError('Resolved project and nonempty obligation inventory required')
        ids = [o['id'] for o in value['obligations']]
        if any(not key.strip() for key in ids) or len(set(ids)) != len(ids):
            raise PolicyError('Requirement IDs must be nonempty and unique')
        by_id = {o['id']: o for o in value['obligations']}
        sources = {}
        for obligation in value['obligations']:
            if obligation['review_status'] != 'DRAFT' or obligation['approval_reference'] is not None:
                raise PolicyError('Imported approval labels are not authority')
            if not obligation['obligation'].strip() or not obligation['owner'] or obligation['representation'] == 'unresolved':
                raise PolicyError('Resolve obligation meaning, ownership and representation before review')
            chain, node = set(), obligation
            while node['parent_id'] is not None:
                if node['id'] in chain or node['parent_id'] not in by_id:
                    raise PolicyError('Requirement parent missing or cyclic')
                chain.add(node['id'])
                node = by_id[node['parent_id']]
            gates = obligation['required_gate_ids']
            if not gates or len(set(gates)) != len(gates) or not set(gates) <= GATES - {'architecture_capture', 'requirements_coverage'}:
                raise PolicyError('Explicit recognized acceptance gates required')
            mapped = obligation['mapped_elements']
            if not mapped or len(set(mapped)) != len(mapped) or any(not x.strip() for x in mapped):
                raise PolicyError('Explicit unique target element identities required')
            source_id = obligation['source_reference']
            if not source_id or not obligation['source_text'] or not obligation['source_text'].strip():
                raise PolicyError('Exact source reference and source passage required')
            source = self.sources.view(source_id)
            if source['role'] == 'evaluator' or source['freshness'] != 'CURRENT':
                raise PolicyError('Evaluator or stale material cannot define generator-visible obligations')
            if obligation['source_text'] not in source['text']:
                raise PolicyError('Cited requirement passage is not present in exact source revision')
            sources[source_id] = source['sha256']
        manifest = digest(sources)
        if value['source_manifest'] is not None and value['source_manifest'] != manifest:
            raise PolicyError('Source manifest identity does not match citations')
        return self.store.record('requirement_ledger', {'record': {**value, 'source_manifest': manifest},
                  'sources': sources, 'status': 'DRAFT_REQUIRES_INDEPENDENT_REVIEW'})

    def request_review(self, ledger_id):
        ledger = self.store.read_record('requirement_ledger', ledger_id)
        self.fresh(ledger)
        return self.approvals.request('approve_requirements', {'ledger_id': ledger_id, 'ledger_digest': digest(ledger)})

    def fresh(self, ledger):
        for source_id, sha in ledger['sources'].items():
            source = self.sources.view(source_id)
            if source['sha256'] != sha or source['freshness'] != 'CURRENT':
                raise PolicyError('Requirement source changed; ledger/evidence invalidated')

    def approved(self, ledger_id):
        ledger = self.store.read_record('requirement_ledger', ledger_id)
        self.fresh(ledger)
        subject = {'ledger_id': ledger_id, 'ledger_digest': digest(ledger)}
        request = self.approvals.request('approve_requirements', subject)
        self.approvals.require(request['id'], 'approve_requirements', subject)
        return ledger

    def coverage(self, ledger_id, architecture):
        base = {'gate': 'requirements_coverage', 'status': 'NOT_RUN'}
        if not ledger_id:
            return {**base, 'reason': 'Reviewed source-backed ledger required'}
        ledger = self.approved(ledger_id)
        if not architecture or not architecture.get('snapshot_id') or architecture['status'] != 'PASS':
            return {**base, 'reason': 'Fresh successful architecture capture/conformance required'}
        snapshot = self.store.read_record('architecture_snapshot', architecture['snapshot_id'])
        elements = snapshot['elements']
        results = []
        for obligation in ledger['record']['obligations']:
            problems = []
            owner = elements.get(obligation['owner'])
            if not owner or owner['kind'] != 'component':
                problems.append('Declared owner does not resolve to a component')
            for key in obligation['mapped_elements']:
                element = elements.get(key)
                if element is None:
                    problems.append('Missing resolved element: ' + key)
                    continue
                if key != obligation['owner'] and element['owner'] != obligation['owner']:
                    problems.append('Element belongs to a different owner: ' + key)
                if obligation['representation'] == 'behavior_contract' and element['kind'] != 'GclGuarantee':
                    problems.append('Behavioral obligation must map to an actual guarantee: ' + key)
            results.append({'id': obligation['id'], 'status': 'UNMAPPED' if problems else 'MAPPED',
                            'problems': problems, 'required_gates': obligation['required_gate_ids'],
                            'checked': False, 'semantically_reviewed': False})
        record = {'ledger_id': ledger_id, 'snapshot_id': snapshot['id'], 'obligations': results,
                  'scope': 'Resolved mapping/ownership only. Mapping is not proof of faithful meaning or executed acceptance.'}
        failed = any(r['problems'] for r in results)
        return {**base, 'status': 'FAIL' if failed else 'PASS', 'reason': 'Unresolved mappings' if failed else 'All reviewed obligations map to owned resolved elements',
                'evidence': self.store.object(record), 'ledger_id': ledger_id,
                'mapped_obligations': sum(not r['problems'] for r in results), 'checked_obligations': 0}
