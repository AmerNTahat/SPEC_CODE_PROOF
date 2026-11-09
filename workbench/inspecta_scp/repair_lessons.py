"""Human-visible failure lessons; diagnostic records never grant rule acceptance."""
from pathlib import Path
from .storage import sha_file


def catalog(store):
    result = []
    for lesson in store.records('repair_failure_lesson'):
        evidence = lesson.get('evidence', [])
        def current(item):
            try:
                return Path(item['path']).is_file() and sha_file(item['path']) == item['sha256']
            except (OSError, KeyError):
                return False
        result.append({**lesson, 'evidence_current': bool(evidence) and all(current(item) for item in evidence),
                       'acceptance_effect': 'Diagnostic only; no requirement, proof-premise or rule-release approval'})
    return sorted(result, key=lambda item: (item.get('sequence', 0), item['id']))
