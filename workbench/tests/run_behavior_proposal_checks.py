"""Actual Z3 checks of explicit proposal-level transcriptions, not full GUMBO proof.
No model calls, source mutations, approved requirement changes or repair attempts.
"""
from pathlib import Path
import hashlib,json,subprocess,time
root=Path.cwd();out=root/'reports/demo/behavior-review';out.mkdir(parents=True,exist_ok=True)
solver=Path('/path/to/SPEC_CODE_PROOF_CoPILOT/INSPECTA-models/kekinian/bin/linux/z3/bin/z3')
solver_command=['/bin/bash',str(solver)]  # Existing Cosmopolitan APE entry requires shell dispatch on this host.
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
mode='''(declare-datatypes () ((Mode INIT NORMAL FAILED)))
(declare-const previous Mode) (declare-const healthy Bool) (declare-const elapsed Real)
(assert (>= elapsed 0))
(define-fun allowed ((next Mode)) Bool
 (and
  (=> (and (= previous INIT) (> elapsed 1)) (= next FAILED))
  (=> (and (= previous INIT) (<= elapsed 1) healthy) (= next NORMAL))
  (=> (and (= previous INIT) (<= elapsed 1) (not healthy)) (= next INIT))
  (=> (and (= previous NORMAL) healthy) (= next NORMAL))
  (=> (and (= previous NORMAL) (not healthy)) (= next FAILED))
  (=> (= previous FAILED) (= next FAILED))))
'''
ranges='''(declare-const lo Int) (declare-const hi Int) (declare-const current Int)
(define-fun source_environment ((l Int) (u Int)) Bool
 (and (<= 97 l) (<= l 99) (<= 98 u) (<= u 100) (<= l (- u 1))))
'''
cases=[
('original_timeout_overlap','sat',mode+'(assert (= previous INIT)) (assert healthy) (assert (> elapsed 1))', 'Counterexample region: original MRM2 requires NORMAL while MRM4 requires FAILED; reachability is not established.'),
('proposed_timeout_total','unsat',mode+'(assert (not (or (allowed INIT) (allowed NORMAL) (allowed FAILED))))','Under the proposed timeout-priority semantics every enum mode, health flag and nonnegative elapsed time admits an output.'),
('proposed_timeout_deterministic','unsat',mode+'(declare-const a Mode) (declare-const b Mode) (assert (allowed a)) (assert (allowed b)) (assert (distinct a b))','Proposed guards cannot require different output modes simultaneously.'),
('strict_one_second_boundary','unsat',mode+'(assert (= previous INIT)) (assert (= elapsed 1)) (assert (not healthy)) (assert (allowed FAILED))','At exactly1.0s an unhealthy INIT does not time out: retain source strict greater-than.'),
('failure_latched_until_reinitialize','unsat',mode+'(assert (= previous FAILED)) (declare-const next Mode) (assert (allowed next)) (assert (distinct next FAILED))','Compute cannot leave FAILED; power-cycle initialization is a separate operation.'),
('golden_early_failure_differs','sat',mode+'(assert (= previous INIT)) (assert (not healthy)) (assert (= elapsed (/ 1.0 5.0))) (assert (allowed INIT))','Golden INIT-unhealthy case requires FAILED already at0.2s, whereas proposed source-timed behavior stays INIT.'),
('old_clock_can_freeze','sat','(declare-const before Real) (declare-const after Real) (assert (>= before 0)) (assert (>= after before)) (assert (= before after))','Nonnegative monotonicity alone admits a frozen clock; an actual clock/progress obligation is necessary.'),
('environment_is_satisfiable','sat',ranges+'(assert (source_environment lo hi))','Non-vacuity check for TableA5 plusEA-OI-6 ordering.'),
('reversed_heat_guards_without_environment','sat',ranges+'(assert (and (<= 96 lo) (<= lo 101) (<= 97 hi) (<= hi 102))) (assert (< current lo)) (assert (> current hi))','TableA7 internal domains alone allow a NORMAL heat-command overlap.'),
('source_environment_excludes_heat_overlap','unsat',ranges+'(assert (source_environment lo hi)) (assert (< current lo)) (assert (> current hi))','Source-backed bounds and ordering rule out simultaneous below-lower and above-upper guards.'),
('out_of_domain_copy_is_unrealizable','unsat',ranges+'(declare-const copied Int) (assert (= lo 200)) (assert (= copied lo)) (assert (and (<= 96 copied) (<= copied 101)))','A hypothetical Valid input200 cannot satisfy both unconditional copying and TableA7. TableA5 excludes this environmental witness.'),
('source_bounds_imply_copied_internal_domains','unsat',ranges+'(assert (source_environment lo hi)) (assert (not (and (<= 96 lo) (<= lo 101) (<= 97 hi) (<= hi 102))))','Restoring the omitted source environment resolves the valid-copy/domain contradiction without widening outputs.'),
('golden_producer_missing_desired_range_contract','sat',ranges+'(assert (not (source_environment lo hi)))','Golden Operator_Interface GUMBO supplies no desired-range guarantees. With no such premise, composition cannot discharge the restored consumer assumptions.'),
('hold_last_valid_range_induction','unsat',ranges+'''(declare-const old_lo Int) (declare-const old_hi Int) (declare-const valid Bool)
(assert (source_environment old_lo old_hi))
(assert (=> valid (source_environment lo hi)))
(define-fun next_lo () Int (ite valid lo old_lo))
(define-fun next_hi () Int (ite valid hi old_hi))
(assert (not (source_environment next_lo next_hi)))''','The proposed hold-last-valid refinement preserves ordered bounds even during invalid-input propagation, assuming a valid initial stored pair and source-backed valid inputs.'),
('candidate_initial_range_is_valid','unsat',ranges+'(assert (not (source_environment 97 98)))','Proposed initial stored pair97/98 is within the source domains; values are a design choice for review, not mandated initial outputs.'),
('golden_1000ms_can_miss_500ms_deadline','sat','''(declare-const arrival_phase_ms Real)
(assert (> arrival_phase_ms 0)) (assert (< arrival_phase_ms 1000))
(define-fun polling_wait_ms () Real (- 1000 arrival_phase_ms))
(assert (>= polling_wait_ms 500))''','Even zero execution/transport cost cannot ensure <500ms arbitrary-phase response for a1000ms polling stage.'),
('illustrative_50ms_five_stage_budget','unsat','''(declare-const w1 Real) (declare-const w2 Real) (declare-const w3 Real) (declare-const w4 Real) (declare-const w5 Real) (declare-const other_cost_ms Real)
(assert (and (<= 0 w1) (<= w1 50) (<= 0 w2) (<= w2 50) (<= 0 w3) (<= w3 50) (<= 0 w4) (<= w4 50) (<= 0 w5) (<= w5 50) (<= 0 other_cost_ms) (<= other_cost_ms 200)))
(assert (>= (+ w1 w2 w3 w4 w5 other_cost_ms) 500))''','Conditional arithmetic only: five<=50ms waits plus<=200ms other cost gives<=450ms. Actual path count, WCET, jitter, transport and rendering bounds are not measured or established.')]
report={'solver':str(solver),'solver_sha256':sha(solver),'solver_version':subprocess.run(solver_command+['--version'],capture_output=True,text=True,check=True).stdout.strip(),'scope':'Manually transcribed local guards, invariants and latency arithmetic; not full SysML/GUMBO translation, implementation proof, reachable-state proof or scheduling analysis','whole_system_acceptance':False,'model_calls':0,'requirements_changed':False,'checks':[]}
for name,expected,body,meaning in cases:
    query='; '+meaning+'\n(set-option :timeout 5000)\n(set-logic ALL)\n'+body+'\n(check-sat)\n'+('(get-model)\n' if expected=='sat' else '')
    path=out/(name+'.smt2');path.write_text(query);start=time.monotonic();command=solver_command+['-smt2',str(path)];p=subprocess.run(command,capture_output=True,text=True,timeout=10)
    actual=p.stdout.splitlines()[0] if p.stdout.splitlines() else 'NO_RESULT'
    report['checks'].append({'name':name,'meaning':meaning,'query':path.relative_to(root).as_posix(),'query_sha256':sha(path),'command':command,'expected':expected,'actual':actual,'check_result':'MATCH' if p.returncode==0 and actual==expected else 'MISMATCH','exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'elapsed_seconds':time.monotonic()-start})
report['all_expected_results_observed']=all(c['check_result']=='MATCH' for c in report['checks'])
report['source_hashes']={str(p.relative_to(root)):sha(p) for p in [root/'isolette/sysml/Steve_Miller_FAA_docAR-08-32.pdf',root/'reports/demo/isolette-revised-generated-Regulate.sysml',root/'.scp-workbench/app/runs/670db1da04a7439190a1dc0f9993f8e2/candidate/Regulate.sysml',root/'.scp-workbench/app/runs/670db1da04a7439190a1dc0f9993f8e2/candidate/Operator_Interface.sysml']}
(out/'solver-results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':len(cases),'all_expected_results_observed':report['all_expected_results_observed'],'model_calls':0}));raise SystemExit(0 if report['all_expected_results_observed'] else 1)
