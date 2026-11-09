# Default tool and feature-scoped qualification

The workspace default is Sireum4.20260810.80aad0c2 with CVC5 integration checks. `workbench/default-toolchain.json` feeds the shared UI/CLI resolver. Standard profile files now explicitly select it; historical tool selections are preserved under `workbench/profiles/legacy/`. Saved runs retain their original configurations. `workbench/tools-env.sh` also selects the upgraded Sireum for shell use. No global installation was replaced.

Tool capability does not mean all system checks automatically run: choose/configure the relevant system properties and formal verification gates. The upgraded tutorial proof demonstrates tool capability, not full coverage of every model or rule.

## Qualification policy

A candidate may qualify only for its declared feature scope after all applicable supported checks and required rule-validation evidence pass. Unsupported or explicitly reference-excluded obligations are neither failed nor passed; exclude them from the scoped pass/fail denominator and retain separate counts plus the original English total. Do not call them statistical outliers: they are documented coverage exclusions. Do not describe an untested future/latest release as unsupported.

The UI now distinguishes:
- NOT_SUPPORTED_TOOL_VERSION: reviewed evidence of selected-version limitation, with alternative encodings considered.
- OUT_OF_SCOPE_REFERENCE: reviewed exclusion from this qualification scope because the reference does not cover the obligation; tool support is not inferred.
- Required modeling, implementation and timing failures: remain mandatory unless explicitly included in a reviewed scope exclusion.

Pending or stale scopes exclude nothing. Exact English, evidence runs, reason, alternatives and revisit conditions are reviewed. Supporting reference evidence must be the actual inspected reference run; changing its source invalidates that evidence. The review does not automatically prove semantic absence, completeness or rule correctness. Exclusions receive zero verification credit and do not establish whole-system acceptance. Changes in tool or supporting evidence require reassessment.

The controller reports `qualification_denominator`, `deferred_targets`, `reference_excluded_targets`, `total_targets` and per-target results. These are inventory counts, not invented success rates. No specific Isolette exclusion has yet been approved/applied in this update.

## What the inspected golden actually covers

See `../behavior-review/REVIEW.md` for the examined source and PDF provenance.

| PDF obligation | Inspected golden contract/deployment | Diagnosis |
|---|---|---|
| FigureA4 INIT timeout after Duration(INMODE)>1s | Mode contracts fail immediately on unhealthy INIT; no elapsed timer | Golden coverage/behavior gap; elapsed-state encoding is accepted by the tool |
| Desired-temperature ranges/order from TableA5 and environmental assumptions | Operator Interface has alarm-range contracts but lacks desired-range/order guarantees | Boundary/producer proof gap; not established as tool limitation |
| Strict response below500ms | Golden periods1000ms; no demonstrated end-to-end proof | Deployment timing mismatch; composition proof alone cannot fix it |

Thus these features can be explicitly excluded from a golden-faithful rulebook qualification scope if selected for review, but must be labeled as reference coverage exclusions, not proven language limitations. Their source requirements remain in the full-system backlog.

## Rulebook status

New maintained draft SYSTEM-COMPOSITION-CHECKS-001 covers allocation, assume/guarantee composition, explicit schedules, generated system proofs, negative controls and the separation of physical timing. It is exported with the other candidates (24 total), preserving original books. `SYSTEM_CHECK_META_RULE_DRAFT.json` contains provenance and the immutable export receipt.

No candidate is newly certified by this change. The current publication implementation still requires independent rule-application/transfer attestation, whose adapter is incomplete. This is a Workbench implementation limitation, not unsupported English, and cannot be hidden by narrowing requirement statistics. The tutorial proof and application tests do not clear that rule-qualification gate. Existing scopes and exclusions must not be represented as published releases.

Validation:149 application tests passed; frontend compiled; 25 real Firefox UI checks passed. Zero new paid calls. Original14M cap and all prior debits retained; no new time or repair-count authorization inferred.
