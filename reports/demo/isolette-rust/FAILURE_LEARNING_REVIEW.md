# Heat-control failure: provenance and repair lessons

The repair checkpoint is now **six attempts**, with existing attempts, the total run cap, time and token debits retained. Increasing the checkpoint does not approve the pending ordered-bounds premise. This report does not accept the heat component or the complete Isolette model.

## Why the failure occurs

The exact English supplied to the latest generation is saved in `ACTUAL_GENERATION_ENGLISH.txt` (development task `964513fce75671168d2afedd9d7e0346a1d6871eb80d78e5469146884b726057`, prepared English `93dec850f20cbc1579d8205c8de7a2229642e4c0f422a9976bf6b68848fb5cd0`). Lines237–241 contain:

- REQ-MHS-2: NORMAL and current temperature less than the lower desired temperature requires heat On.
- REQ-MHS-3: NORMAL and current temperature greater than the upper desired temperature requires heat Off.

The selected English contains no EA-OI-6. If the lower bound exceeds the upper bound, a temperature between them meets both guards. No choice of heat output can satisfy both guarantees. Changing branch priority merely chooses which guarantee fails.

The executed GUMBOX shrink produced current0, lower1, upper−1, Normal. A separate CVC5 diagnostic uses current98°F, lower99°F, upper97°F, demonstrating the same conflict with all three temperatures inside97–100°F. The diagnostic confirms guard overlap is satisfiable, both output guarantees at that witness are unsatisfiable, and adding ordering excludes the overlap. This is a small, manually transcribed guard diagnosis, **not** a full HAMR/Logika/Verus model proof. The finite witnesses do not establish general floating-point soundness.

## What the golden contains

Both original `isolette/sysml/Regulate.sysml` lines384–393 and the approved isolated compatibility reference retain the same two compute-case guards and opposing guarantees. The heat contract has no enclosing desired-bound ordering assumption. Inspection therefore identifies the same local contract dependency gap in the golden. We have not run a fresh whole-golden Rust proof in this investigation and do not claim that result.

The generated model did not invent these two behaviors. It formalized the supplied heat requirements, but generation/data preparation did not establish the dependency needed to use them consistently. Earlier successful parsing, graph comparison, or checks of other components could not establish this missing behavioral premise. The gap should have been identified before implementation retries.

## What the full English says

FAA AR-08-32 EA-OI-6 appears before the selected Regulator excerpt, in the operator-interface environmental assumptions (PDF page102 / printedA11). `../behavior-review/PREPARED_ENGLISH_WITH_DEPENDENCIES.md` lines426–430 preserves the extracted wording and rationale. The rationale explicitly warns that a lower desired temperature greater than or equal to the upper desired temperature makes On/Off unclear and can cause excessive cycling.

The printed/extracted “Upper Desired Temperature of -1°F” wording requires review before declaring an exact one-degree-margin requirement. The existing proposal lower≤upper is only a minimal condition for excluding overlap of these strict guards. It is not asserted to be the complete FAA condition. The more complete English preparation is still pending approval; it was not the input used by this generation.

## Lessons retained from each heat round

| Recorded round | Failure | Lesson and next action |
| --- | --- | --- |
| Generated scaffold | Missing output DataPort values; failed postconditions/tests | Implement required initialize/compute outputs while preserving contracts. |
| Heat implementation | Executable enum equality rejected by Verus | Replace equality with an equivalent exhaustive match; recheck proof and tests. |
| Match implementation | Verus10 verified/1error; GUMBOX3passed/2failed | Replay counterexample, inspect guard overlap, trace English assumptions and their owners before more code edits. |

These manual component rounds are separate from the paid generation lineage. No history or exhausted total model-run allowance has been reset. The six-attempt checkpoint is a maximum, not a requirement to waste attempts when a prerequisite review is necessary.

`REPAIR-ASSUMPTION-CLOSURE-001` is a new maintained **draft** repair rule, alongside `PREP-CONTEXT-DEPENDENCIES-001`, `RA-001`, and `RUST-CONTRACT-REALIZATION-001`. The draft generalizes the process: capture the failure, distinguish implementation/tool/contract issues, test conflicting guards, trace full English dependencies, allocate assumption ownership, review changed premises, and repeat affected proof/tests. Its approved source context is the KSU implementation/testing guidance; generated failure feedback is supervised development evidence. Golden inspection remains evaluator diagnosis, not silently added training material. No transfer or release acceptance is implied.

The UI now displays the six-attempt setting and a “Lessons from failed repairs” section with each observed failure, cause, proposed next check, rule and evidence freshness. Exact records and the immutable learned-book location are in `FAILURE_LEARNING_RULEBOOK.json`.

## Proposed next repair, still pending premise approval

Review the original EA-OI-6 wording and the existing ordered-bounds proposal. Once approved, add the reviewed dependency to the English and the appropriate component precondition, then rerun heat Verus and GUMBOX. Separately establish how the operator interface or producer guarantees it, or record it as an explicit externally enforced system assumption. A conditional component proof alone cannot close that integration obligation.

This issue is **not** unsupported GUMBO functionality and must not be excluded from acceptance as an uncovered golden feature. The supported guarantees are mutually inconsistent for an admitted input. No assumption, requirement, golden file or acceptance result was changed by this investigation.

## Evidence and budget

- `SIX_ATTEMPT_POLICY.json`: recorded authorization and unchanged-history policy.
- `HEAT_GUARD_DIAGNOSIS.json` and its three `.smt2` inputs: executed CVC5 diagnosis with exact commands, hashes and timings.
- `verification-heat-implementation.json` and `verification-heat-match.json`: retained actual Rust/Verus/GUMBOX failures.
- `FAILURE_LEARNING_RULEBOOK.json`: three failure lessons, new draft rule and immutable book snapshot.
- `FAILURE_LEARNING_TIME_EXTENSION.json`: recorded25-minute extension.

No additional paid model calls were made. Charged campaign usage remains6,256,540 tokens (1,256,540 measured plus5,000,000 estimated), within the14M aggregate cap; continuation allowance remaining1,737,838. M07 remains in progress.
