"""Bounded HAMR generation and integration checks; no whole-program proof claim."""
import base64
import json
from pathlib import Path
import re

from .config import PolicyError
from .storage import sha_file


def classify(operation, record, artifacts, platform='JVM'):
    stdout, stderr = record['stdout'], record['stderr']
    if record['interrupted']:
        return 'UNKNOWN', 'Tool interrupted: ' + record['interrupted']
    if 'bwrap:' in stderr:
        return 'UNKNOWN', 'Worker sandbox could not start'
    if record['exit_code'] != 0:
        return 'FAIL', 'HAMR tool returned a nonzero status; inspect recorded diagnostics'
    if 'Instantiation Warning' in stdout or 'MISSING_AADL_TYPE' in stdout:
        return 'UNKNOWN', 'Unresolved instantiated-model warnings'
    if operation == 'hamr_codegen':
        if platform=='Microkit':
            if not any(name.endswith('.rs') for name in artifacts) or not any(name.endswith('Cargo.toml') for name in artifacts):
                return 'UNKNOWN','Generator returned without expected Rust/Microkit artifacts'
            return 'PASS','HAMR emitted Rust/Microkit artifacts; compilation, Verus and runtime tests are separate'
        if not any(name.endswith('.scala') for name in artifacts):
            return 'UNKNOWN', 'Generator returned without the expected Slang source artifacts'
        return 'PASS', 'HAMR emitted Slang/JVM artifacts; compilation and implementation verification are separate'
    claims = re.findall(r'^Checking (.+)$', stdout, re.MULTILINE)
    if not claims or 'Integration constraints verified!' not in stdout:
        return 'UNKNOWN', 'No completed nonempty integration-constraint verification established'
    results = record.get('integration_results', [])
    if len(results) != len(claims) or not all(
            r.get('type') == 'IntegrationConstraintReporting.IntegrationConstraint'
            and r.get('srcPort') and r.get('dstPort') and r.get('claim') and r.get('smt2Query')
            and r.get('smt2QueryResult', {}).get('value') == 'Unsat' for r in results):
        return 'UNKNOWN', 'Complete per-connection solver feedback is required'
    return 'PASS', 'Logika verified the reported connection integration constraints only'


class Engineering:
    def __init__(self, controller):
        self.controller = controller
        self.store = controller.store

    def check(self, run_id, config, folder, operation):
        if operation not in {'hamr_codegen', 'integration_constraints'}:
            raise PolicyError('Unsupported engineering adapter')
        record, output, interrupted = self.controller._run_tool(run_id, config, folder, operation)
        artifacts = {}
        integration_results = []
        size = 0
        for path in sorted(Path(output).rglob('*')):
            if path.is_symlink():
                raise PolicyError('Generated evidence contains a symlink')
            if not path.is_file():
                continue
            size += path.stat().st_size
            if size > 64 * 1024 * 1024 or len(artifacts) >= 10000:
                raise PolicyError('Generated evidence exceeds bounded artifact inventory')
            data = path.read_bytes()
            if operation == 'integration_constraints' and path.parent.name == 'integration_constraints' and path.suffix == '.json':
                try:
                    integration_results.append(json.loads(data))
                except (ValueError, UnicodeDecodeError) as exc:
                    raise PolicyError('Malformed solver feedback') from exc
            artifacts[path.relative_to(output).as_posix()] = {
                'sha256': sha_file(path), 'bytes': len(data),
                'content': self.store.object({'encoding': 'base64', 'data': base64.b64encode(data).decode('ascii')})}
        record.update(run_id=run_id, artifacts=artifacts, operation=operation,
                      integration_results=integration_results,
                      checked_claims=re.findall(r'^Checking (.+)$', record['stdout'], re.MULTILINE),
                      scope='Generation or connection integration only; no implementation proof, compilation, independent tests or acceptance')
        status, reason = classify(operation, record, artifacts,config.get('hamr_platform','JVM'))
        return {'gate': operation, 'status': status, 'reason': reason,
                'evidence': self.store.object(record)}, interrupted
