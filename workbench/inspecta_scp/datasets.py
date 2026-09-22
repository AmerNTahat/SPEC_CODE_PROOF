"""Reviewed manifest-level assignments; never infer semantic independence."""
from pathlib import Path

from .approvals import Approvals
from .config import PolicyError, digest
from .sources import Sources
from .storage import safe_child, sha_file
from .vendor.split_dataset import assign


class Datasets:
    def __init__(self, store):
        self.store = store
        self.sources = Sources(store)
        self.approvals = Approvals(store)

    def propose(self, request):
        if not isinstance(request, dict) or set(request) != {'tasks', 'strategy', 'fractions', 'seed'}:
            raise PolicyError('Declare tasks, strategy, explicit fractions (or null), and seed')
        if not isinstance(request['tasks'], list) or not isinstance(request['seed'], str):
            raise PolicyError('Tasks must be a list and seed must be text')
        tasks = []
        for task in request['tasks']:
            if not isinstance(task, dict) or set(task) != {'id', 'family_id', 'lineage_id', 'role', 'source_ids', 'reference_ids'}:
                raise PolicyError('Task needs ID, reviewed family/lineage, role, source_ids and reference_ids')
            for key in ('id', 'family_id', 'lineage_id'):
                if not isinstance(task[key], str) or not task[key].strip():
                    raise PolicyError('Unknown task family/lineage blocks an independence claim')
            hashes = []
            for key in ('source_ids', 'reference_ids'):
                ids = task[key]
                if not isinstance(ids, list) or any(not isinstance(i, str) for i in ids) or len(set(ids)) != len(ids):
                    raise PolicyError('Source inventories must contain unique registered IDs')
                if key == 'source_ids' and not ids:
                    raise PolicyError('Each task needs registered input sources')
                for source_id in ids:
                    source = self.sources.view(source_id)
                    if source['freshness'] != 'CURRENT':
                        raise PolicyError('Dataset source is stale or missing')
                    if key == 'reference_ids' and source['role'] != 'evaluator':
                        raise PolicyError('Reference answers must be registered evaluator-only')
                    if key == 'source_ids' and source['role'] not in {'learning', 'development'}:
                        raise PolicyError('Task inputs cannot be evaluator-only or declared general shared context')
                    hashes.append(source['sha256'])
            tasks.append({**task, 'content_hashes': sorted(set(hashes))})
        try:
            proposal = assign({'tasks': tasks}, request['strategy'], request['fractions'], request['seed'])
        except (ValueError, TypeError) as exc:
            raise PolicyError(str(exc)) from exc
        return self.store.record('dataset', {'proposal': proposal, 'request': request,
            'status': 'DRAFT_REQUIRES_REVIEW', 'independence': 'Provided lineage and exact content only; semantic independence unestablished'})

    def fresh(self, dataset_id):
        record = self.store.read_record('dataset', dataset_id)
        for task in record['proposal']['tasks']:
            for source_id in task['source_ids'] + task['reference_ids']:
                if self.sources.view(source_id)['freshness'] != 'CURRENT':
                    raise PolicyError('Dataset source changed after proposal; new proposal and review required')
        return record

    def request_review(self, dataset_id):
        record = self.fresh(dataset_id)
        return self.approvals.request('approve_dataset', {'dataset_id': dataset_id, 'dataset_digest': digest(record)})

    def approved(self, dataset_id):
        record = self.fresh(dataset_id)
        subject = {'dataset_id': dataset_id, 'dataset_digest': digest(record)}
        request = self.approvals.request('approve_dataset', subject)
        self.approvals.require(request['id'], 'approve_dataset', subject)
        return record

    def validate_run(self, config):
        record = self.approved(config['dataset_assignment'])
        task = next((t for t in record['proposal']['tasks'] if t['id'] == config['dataset_task']), None)
        if task is None:
            raise PolicyError('Selected task is absent from the reviewed assignment')
        if config['mode'] == 'learning' and task['role'] == 'final':
            raise PolicyError('Final tasks cannot drive learning')
        allowed = {}
        for source_id in task['source_ids']:
            source = self.store.read_record('source', source_id)
            root = self.store.read_record('source_root', source['root_id'])
            allowed[str(safe_child(Path(root['path']), source['relative']))] = source['sha256']
        protected = set()
        for other in record['proposal']['tasks']:
            for source_id in other['reference_ids']:
                protected.add(self.store.read_record('source', source_id)['sha256'])
        for relative in config['input_files']:
            path = safe_child(Path(config['project']), relative)
            actual = sha_file(path)
            if allowed.get(str(path)) != actual or actual in protected:
                raise PolicyError('Run input is outside the selected task or duplicates an evaluator reference')
        return record

    def catalog(self):
        records = []
        approvals = self.store.records('approval')
        for record in self.store.records('dataset'):
            try:
                self.fresh(record['id']); freshness = 'CURRENT'
            except (PolicyError, OSError):
                freshness = 'STALE_OR_BROKEN'
            subject = {'dataset_id': record['id'], 'dataset_digest': digest(record)}
            request = next((a for a in approvals if a['action'] == 'approve_dataset' and a['subject'] == subject), None)
            decision = self.approvals.get(request['id'])['status'] if request else 'NOT_REQUESTED'
            records.append({**record, 'freshness': freshness, 'review_status': decision})
        return {'datasets': records, 'scope': 'Human review metadata; evaluator contents are never exported'}
