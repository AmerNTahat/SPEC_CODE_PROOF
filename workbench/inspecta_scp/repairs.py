"""Bounded provisional repairs in isolated, immutable branches.

Source promotion is deliberately separate. Passing a subset of gates cannot
turn a provisional revision into an engineering-accepted artifact.
"""
import hashlib
import json
from pathlib import Path
import tempfile

from .architecture import Architecture
from .config import PolicyError, digest
from .requirements import Requirements
from .storage import safe_child, sha_file


class Repairs:
    def __init__(self, controller):
        self.controller = controller
        self.store = controller.store

    def _source_files(self, run):
        folder = self.store.root / 'runs' / run['id']
        manifest = json.loads((folder/'input-workspace-manifest.json').read_text())
        result = {}
        for rel, expected in manifest['files'].items():
            path = safe_child(folder/'candidate', rel)
            data = path.read_bytes()
            if hashlib.sha256(data).hexdigest() != expected:
                raise PolicyError('Original run candidate changed')
            result[rel] = {'sha256': expected, 'content': self.store.object({'text': data.decode('utf-8')})}
        return result

    def stage(self, run_id, issue, patch, parent_id=None):
        if not isinstance(issue, str) or not issue.strip() or len(issue) > 200:
            raise PolicyError('Bounded diagnostic/issue identity required')
        if not isinstance(patch, dict) or not patch:
            raise PolicyError('Nonempty exact replacement patch required')
        self.store.db.execute('BEGIN IMMEDIATE')
        try:
            run = self.controller.status(run_id)
            if run['state'] not in {'READY', 'PAUSED', 'CHECKED', 'FAILED', 'BLOCKED'}:
                raise PolicyError('Pause running work before staging a repair')
            if run['remaining_seconds'] <= 0:
                raise PolicyError('Run deadline exhausted; repair cannot renew it')
            if run.get('source_changed') or not run.get('policy_current', True):
                raise PolicyError('Original sources or approved policy changed')
            existing = [r for r in self.store.records('repair_candidate') if r['run_id'] == run_id]
            if len(existing) >= run['config']['budget']['repairs_per_run'] or sum(r['issue'] == issue for r in existing) >= run['config']['budget']['repairs_per_issue']:
                raise PolicyError('Repair attempt allowance exhausted')
            if parent_id:
                parent = self.store.read_record('repair_candidate', parent_id)
                if parent['run_id'] != run_id or parent['config_hash'] != run['config_hash']:
                    raise PolicyError('Parent belongs to another run/configuration')
                files = dict(parent['files'])
            else:
                files = self._source_files(run)
            before = {rel: value['sha256'] for rel, value in files.items()}
            if not set(patch) <= set(run['config']['repair_allowed_files']):
                raise PolicyError('Patch exceeds explicitly authorized repair scope')
            for rel, change in patch.items():
                if not isinstance(change, dict) or set(change) != {'expected_sha256', 'text'}:
                    raise PolicyError('Replacement needs exact expected_sha256 and text')
                if change['expected_sha256'] != files[rel]['sha256']:
                    raise PolicyError('Patch was drafted against a different revision')
                text = change['text']
                if not isinstance(text, str) or len(text.encode()) > 4*1024*1024:
                    raise PolicyError('Invalid or oversized repair file')
                files[rel] = {'sha256': hashlib.sha256(text.encode()).hexdigest(), 'content': self.store.object({'text': text})}
            after = {rel: value['sha256'] for rel, value in files.items()}
            if before == after or any(r['tree_sha256'] == digest(after) for r in existing):
                raise PolicyError('No progress: unchanged or previously attempted candidate')
            candidate = self.store.record('repair_candidate', {'run_id': run_id, 'config_hash': run['config_hash'],
                'issue': issue, 'parent_id': parent_id, 'files': files, 'tree_sha256': digest(after),
                'changed_files': sorted(rel for rel in files if before[rel] != after[rel]),
                'status': 'PROVISIONAL_UNCHECKED', 'source_files_modified': 0})
            self.store.event(run_id, 'repair_staged', {'candidate_id': candidate['id'], 'issue': issue,
                'parent_id': parent_id, 'attempt_number': len(existing)+1, 'budget_reset': False})
            self.store.db.execute('COMMIT')
        except BaseException:
            self.store.db.execute('ROLLBACK')
            raise
        return candidate

    def validate(self, candidate_id):
        candidate = self.store.read_record('repair_candidate', candidate_id)
        prior = [v for v in self.store.records('repair_validation') if v['candidate_id'] == candidate_id and v['status'] not in {'PAUSED'}]
        if prior:
            return prior[-1]
        run = self.controller.status(candidate['run_id'])
        if run['config_hash'] != candidate['config_hash'] or run.get('source_changed') or not run.get('policy_current', True):
            raise PolicyError('Repair configuration, sources or policy became stale')
        if run['state'] not in {'READY', 'PAUSED', 'CHECKED', 'FAILED', 'BLOCKED'} or run['remaining_seconds'] <= 0:
            raise PolicyError('Run cannot check a repair within the existing budget')
        config = run['config']
        self.controller._validate_policies(config)
        folder = Path(tempfile.mkdtemp(prefix='repair-', dir=self.store.root/'runs'/run['id']))
        (folder/'candidate').mkdir()
        for rel, value in candidate['files'].items():
            target = safe_child(folder/'candidate', rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            text = self.store.load_object(value['content'])['text']
            if hashlib.sha256(text.encode()).hexdigest() != value['sha256']:
                raise PolicyError('Repair content hash mismatch')
            target.write_text(text)
        manifest = {'source_root': config['project'], 'files': {k:v['sha256'] for k,v in candidate['files'].items()},
                    'provisional_candidate': candidate_id}
        (folder/'input-workspace-manifest.json').write_text(json.dumps(manifest))
        self.store.change(run['id'], {run['state']}, 'CHECKING', {'repair_candidate': candidate_id})
        gates, interrupted, error, captured = [], None, None, None
        try:
            for gate in config['required_gates']:
                current = self.store.get(run['id'])
                if current['state'] in {'PAUSE_REQUESTED', 'STOP_REQUESTED'}:
                    interrupted = 'PAUSED' if current['state']=='PAUSE_REQUESTED' else 'CANCELLED'
                    break
                if current['remaining_seconds'] <= 0:
                    interrupted = 'BUDGET_EXHAUSTED';break
                if gate == 'parse_type':
                    result, interrupted = self.controller._parse_type(run['id'], config, folder)
                elif gate in {'architecture', 'architecture_capture'}:
                    captured, interrupted = Architecture(self.controller).capture(run['id'], config, folder)
                    result = Architecture(self.controller).check(config.get('architecture_policy'), captured) if gate=='architecture' else captured
                elif gate == 'requirements_coverage':
                    if captured is None and config.get('requirement_ledger'):
                        captured, interrupted = Architecture(self.controller).capture(run['id'],config,folder)
                    result = Requirements(self.store).coverage(config.get('requirement_ledger'),captured)
                elif gate in {'hamr_codegen', 'integration_constraints'}:
                    from .engineering import Engineering
                    result, interrupted = Engineering(self.controller).check(run['id'],config,folder,gate)
                else:
                    result = {'gate': gate, 'status': 'NOT_RUN', 'reason': 'Trusted adapter not implemented'}
                gates.append(result)
                if interrupted:break
            if {rel:sha_file(safe_child(folder/'candidate',rel)) for rel in candidate['files']} != manifest['files']:
                raise PolicyError('Provisional candidate changed while checking')
            if self.controller.status(run['id']).get('source_changed'):
                raise PolicyError('User source changed while checking; no promotion')
            self.controller._validate_policies(config)
        except (PolicyError, OSError, ValueError, KeyError) as exc:
            error = str(exc)
        # Restore original result atomically; no provisional check overwrites it.
        self.store.db.execute('BEGIN IMMEDIATE')
        try:
            current=self.store.get(run['id'])
            if current['state'] not in {'CHECKING','PAUSE_REQUESTED','STOP_REQUESTED'}:
                raise PolicyError('Repair worker lost ownership')
            if current['state']=='STOP_REQUESTED':interrupted='CANCELLED'
            elif current['state']=='PAUSE_REQUESTED':interrupted='PAUSED'
            elif current['remaining_seconds']<=0:interrupted='BUDGET_EXHAUSTED'
            state = interrupted or run['state']
            status = interrupted or ('BLOCKED' if error else 'FAILED' if any(g['status']=='FAIL' for g in gates) else
                'CHECKED_PROVISIONAL' if len(gates)==len(config['required_gates']) and all(g['status']=='PASS' for g in gates) else 'BLOCKED')
            validation=self.store.record('repair_validation',{'candidate_id':candidate_id,'run_id':run['id'],
                'status':status,'gates':gates,'error':error,'engineering_accepted':False,'source_files_modified':0,
                'config_hash':candidate['config_hash'],'tree_sha256':candidate['tree_sha256']})
            self.store.db.execute('UPDATE runs SET state=?,worker=NULL,version=version+1 WHERE id=?',(state,run['id']))
            self.store.event(run['id'],'repair_checked',{'validation_id':validation['id'],'state':state,
                'candidate_status':status,'original_result_preserved':True,'budget_reset':False})
            self.store.db.execute('COMMIT')
        except BaseException:
            self.store.db.execute('ROLLBACK');raise
        return validation

    def catalog(self, run_id=None):
        return {'candidates':[r for r in self.store.records('repair_candidate') if run_id is None or r['run_id']==run_id],
                'validations':[r for r in self.store.records('repair_validation') if run_id is None or r['run_id']==run_id],
                'promotion':'UNAVAILABLE_PENDING_COMPLETE_ENGINEERING_GATES'}

    def diff(self, candidate_id):
        import difflib
        candidate = self.store.read_record('repair_candidate', candidate_id)
        before = (self.store.read_record('repair_candidate', candidate['parent_id'])['files']
                  if candidate['parent_id'] else self._source_files(self.store.get(candidate['run_id'])))
        patches = {}
        for rel in candidate['changed_files']:
            old = self.store.load_object(before[rel]['content'])['text']
            new = self.store.load_object(candidate['files'][rel]['content'])['text']
            patches[rel] = ''.join(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True),
                                                       fromfile='parent/' + rel, tofile='provisional/' + rel))
        return {'candidate_id': candidate_id, 'patches': patches,
                'scope': 'Exact text change only; not a semantic acceptance result'}
