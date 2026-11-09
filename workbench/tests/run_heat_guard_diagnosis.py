"""Executed SMT diagnosis of the two heat guards, not a whole-model proof.

Manual transcription is checked against exact source fragments. Real arithmetic
is used only for these finite integer witnesses; no floating-point claim follows.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import time

root = Path(__file__).resolve().parents[2]
out = root / 'reports/demo/isolette-rust'
solver = root / '.scp-workbench/tools/sireum-4.20260810.80aad0c2/Sireum/bin/linux/cvc5'
reference = root / 'isolette/sysml/Regulate.sysml'
text = reference.read_text()
assert 'current_tempWstatus.degrees < lower_desired_temp.degrees' in text
assert 'current_tempWstatus.degrees > upper_desired_temp.degrees' in text
base = '''(set-logic QF_LRA)
(declare-const current Real)
(declare-const lower Real)
(declare-const upper Real)
(declare-const heat_on Bool)
; Restrict to Normal mode. These are the REQ_MHS_2/3 guard inequalities.
(define-fun below () Bool (< current lower))
(define-fun above () Bool (> current upper))
'''
queries = [
    ('overlap_within_desired_range', '(assert (= current 98))\n(assert (= lower 99))\n(assert (= upper 97))\n(assert (and below above))', 'sat'),
    ('same_witness_both_guarantees', '(assert (= current 98))\n(assert (= lower 99))\n(assert (= upper 97))\n(assert (=> below heat_on))\n(assert (=> above (not heat_on)))', 'unsat'),
    ('conditional_ordering_excludes_overlap', '(assert (<= lower upper))\n(assert (and below above))', 'unsat'),
]
report = {'scope': 'Diagnostic manual transcription of golden heat guards; not HAMR/Logika/Verus acceptance or approval of a new premise',
          'original_reference': str(reference), 'reference_sha256': hashlib.sha256(reference.read_bytes()).hexdigest(),
          'solver_sha256': hashlib.sha256(solver.read_bytes()).hexdigest(), 'model_calls': 0, 'checks': []}
for name, assertions, expected in queries:
    path = out / (name + '.smt2')
    path.write_text(base + assertions + '\n(check-sat)\n')
    start = time.monotonic()
    cmd = [str(solver), '--lang=smt2', str(path)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    report['checks'].append({'name': name, 'command': cmd, 'exit_code': result.returncode,
                            'stdout': result.stdout, 'stderr': result.stderr, 'expected': expected,
                            'expected_observed': result.returncode == 0 and result.stdout.strip() == expected,
                            'elapsed_seconds': time.monotonic() - start})
(out / 'HEAT_GUARD_DIAGNOSIS.json').write_text(json.dumps(report, indent=2) + '\n')
assert all(c['expected_observed'] for c in report['checks']), report
print([(c['name'], c['stdout'].strip()) for c in report['checks']])
