# Isolette behavioral corrections and pinned GUMBO capability review

Status: review package prepared; no behavioral acceptance, requirement change, model repair, tool upgrade or rule release. The fresh generated architecture passed its directed-graph check previously; that does not establish the requirements below. This review used zero paid model calls.

## Can GUMBO limitations explain missing temporal requirements?

Yes, some requirements need capabilities beyond a local compute contract, and available features depend on the selected toolchain. But absence in a golden example does not establish a language limitation or authorize dropping an obligation.

Actual isolated Sireum parser/type-checker probes were executed with the existing toolchain and approved HAMR libraries:

| Probe | Observed result | What it establishes |
|---|---|---|
| Integer elapsed-time input, remembered state, initialization, `In(...)`, and `elapsed_ms > 1000` predicate | PASS / Well-formed | This local state-based timeout encoding is accepted. It does not supply a clock, prove progress or prove the implementation. |
| Add `(not expired) until expired` to that accepted baseline | FAIL at `until` | This proposed native-until syntax is rejected. It does not prove that every possible encoding of an until-like property is impossible. |
| Add the current documented `composition` system-property construct to the accepted baseline | FAIL at `composition` | The installed parser does not accept this newer system-composition syntax. |

Reproducible inputs, run IDs, stdout, stderr and durations: [gumbo-capability-probes.json](gumbo-capability-probes.json). These were syntax capability probes, not repairs of Isolette or contract proofs.

Current official [component-contract documentation](https://hamr.sireum.org/hamr-doc/gumbo-component-contracts/) describes initialization and compute pre/postconditions, state and `In(...)`. Current [system-property documentation](https://hamr.sireum.org/hamr-doc/gumbo-system-properties/) also describes composition, abstract schedules, assertions and loop invariants. Thus “GUMBO only ever supports local contracts” would be incorrect. Availability in online documentation is not evidence that the installed version implements the feature. Abstract schedule reasoning alone is not a measured or proved physical deadline.

The checked local parser builder handles library/subclause constructs; its subclause and AIR representation have state, functions, invariants, integration, initialization and compute fields. Source/tool identities accompany this review. No upgrade was attempted.

For each English obligation, distinguish: directly expressible and checked; expressible with explicit state/clock modeling; requires supported system-level analysis; needs physical timing analysis; unsupported by the pinned tool; or unresolved interpretation. An unsupported or unproved obligation stays open. Do not award a passing verification unit because the golden omitted it. Do not label every omitted clause a tool limitation.

## Source correction: desired-temperature ranges

The earlier review used only the Regulator section and reported conflicting unconstrained ranges. Full-source inspection changes that diagnosis: FAA A.3.4 already supplies important dependencies that data preparation omitted.

- Table A-5, PDF page 101 / printed A-10: integer Lower Desired Temperature [97..99] °F; Upper Desired Temperature [98..100] °F; initial status Invalid.
- EA-OI-5, EA-OI-6 and EA-OI-7, PDF page 102 / A-11: lower >=97, desired-bound ordering, upper <=100. EA-OI-6's printed wording is awkward (“Upper Desired Temperature of -1°F”); the proposed reading is lower <= upper - 1°F. Exact source wording is preserved for review.
- Table A-7's wider internal domains do not replace the external assumptions. Source-backed bounds exclude a Valid value 200 and reversed desired bounds. Prior unconstrained counterexamples remain useful diagnostics but are not admissible environmental inputs once the source assumptions are justified.
- The checked golden Operator_Interface contracts have alarm-range constraints, but no desired-range/order guarantees. Consequently, adding a consumer assumption alone would not complete the producer/composition proof.

Proposal: restore the actual source passages in prepared English; allocate external-input obligations to the Operator Interface/system boundary; prove or explicitly justify the environmental assumptions. Preserve validity/failure behavior rather than silently clamp values or redefine a Valid status as failure.

During invalid inputs, a possible implementation refinement is to hold the last validated ordered desired pair, initially 97/98. That pair is a proposed design choice, not a mandated source initialization. The source leaves the failed-interface outputs unspecified, so review this refinement and its initialization/propagation behavior before adoption.

The UI now supports selecting approved context passages by line range, explaining their relevance and creating a new English revision for review. It preserves the previous document and approval. This operation does not infer arbitrary dependency closure or discharge assumptions automatically.

Prepared revision: `c29f7775771a56e2ac7bea245d9d05877407624b21f856051f90e015e609244a`, PENDING.
[Review English and exact added passages](PREPARED_ENGLISH_WITH_DEPENDENCIES.md); [provenance and approval identity](PREPARED_ENGLISH_WITH_DEPENDENCIES.json).
FAA source lines 4579–4722 include the Temperature Sensor, Heat Source and Operator Interface dependencies. No golden worked answer was added to the generator context.

## Timeout: what the golden does and proposed correction

The checked compatibility reference's Manage_Regulator_Mode_i declares `lastRegulatorMode`, initializes the output to INIT, and contains cases for INIT+healthy -> NORMAL and INIT+unhealthy -> FAILED immediately. It has no elapsed timer, and its GUMBO block does not explicitly initialize or update that history state. This is a contract-coverage observation, not a claim that every implementation has the same defect.

FAA Figure A-4 (PDF page109 / printed A-18) instead shows INIT -> FAILED on Duration(INMODE)>1.0s. The diagram has been rendered and transcribed into English in the pending preparation. [Rendered page](figure-a4.png), [page/hash provenance](figure-a4-provenance.json).

The fresh generated contract retains both INIT+healthy -> NORMAL and INIT+elapsed>1 -> FAILED. Healthy INIT after the threshold enables inconsistent outputs. Neither the diagram nor the examined prose supplies explicit overlapping-guard priority. The model correctly flags this unresolved issue; syntax acceptance cannot resolve it.

Proposed discrete interpretation for review: deadline first, using elapsed residence time sampled at guard evaluation.

| Previous mode | Condition | Next mode |
|---|---|---|
| INIT | elapsed >1.0s | FAILED |
| INIT | elapsed <=1.0s and healthy | NORMAL |
| INIT | elapsed <=1.0s and unhealthy | INIT |
| NORMAL | healthy / unhealthy | NORMAL / FAILED respectively |
| FAILED | any | FAILED until reinitialization |

This preserves strict `>`: unhealthy at exactly1.0s remains INIT. It makes the branches disjoint, but **priority is a proposed refinement requiring review**, not a fact silently attributed to the FAA. An alternative is a justified urgent-transition semantics and proof that overlap is unreachable; that cannot be assumed under one-second periodic polling.

A real monotonic clock must supply elapsed residence time, reset on entry, and progress appropriately. Nondecreasing state alone admits frozen time. Updating a timestamp after evaluating a previous-dispatch elapsed value could introduce an extra dispatch of delay; implementation must align the sampled time with the guards. Counter ticks are not automatically elapsed seconds. Finite-width overflow and any real-to-machine-number abstraction also need verification.

[Guard-only proposed patch](timeout-priority-proposal.patch) is a review artifact; it has not been applied. It resolves guard overlap only, not the clock integration or timing issues.

## Timing: source obligation versus deployment choice

The golden Regulator and Operator Interface thread periods are 1000ms. FAA status/display response requirements are strictly below0.5s; heat-control response has a separate6s bound. A single1000ms polling stage can wait nearly1000ms after an arbitrary-phase event, even if execution and communication take no time. Current assumptions do not justify the shorter deadline.

Proposal: retain the reference-faithful structural training profile, and review a separate operational timing profile against the actual end-to-end path. Include all sampling waits, execution bounds, scheduling jitter, communication and display costs. Do not change the FAA requirement or claim that syntax or a runtime smoke test proves it.

For illustration only, five polling waits bounded by50ms plus all other costs bounded by200ms would give<=450ms. The actual path count and cost bounds have not been established, and this is not a selected schedule or measured WCET. GUMBO temporal expressiveness cannot make a too-slow deployment satisfy a deadline.

## Executed checks and limits

Existing Z3 4.13.4 executed17 explicitly transcribed guard, invariant and timing-arithmetic queries, with all expected SAT/UNSAT outcomes observed. Results include non-vacuous environmental assumptions; proposed mode totality/determinism and strict boundary; frozen-clock witness; copy-domain consistency under source bounds; preserved ordered range under the proposed hold-last-valid refinement; and a one-second polling counterexample. [Exact queries and solver outputs](solver-results.json).

These are **not17 proved system requirements**. They are manual proposal-level transcriptions, not automatic translation of the entire SysML/GUMBO model, reachable-state analysis, implementation verification or scheduling/WCET proof. The pinned GUMBO checks above establish syntax capability only.

Workbench application tests:144 passed. Real Firefox UI checks:24 passed, including the new context supplement flow. Synthetic application tests are not live engineering evidence.

## Decisions and remaining work

The concrete review items are the supplemented English/diagram transcription; timeout priority (or an alternative unreachable-overlap argument); invalid-input range handling; producer assumption discharge; and a justified operational timing profile. WORKFLOW_CONTRACT.md states that a data/model/tool/library/policy amendment invalidates affected evidence. These proposals therefore remain pending and do not alter the selected data, source golden, generated model, deployed schedule or toolchain.

After decisions: map each English obligation to a supported encoding and actual proof obligation, run approved behavioral corrections through the KSU gates, and recheck affected structure/behavior. A further paid model repair would also need explicit retry authorization: the existing8-attempt family allowance is exhausted. The extra time authorization covered this review; it did not reset that count.

Budget at this review:1,256,540 measured +5,000,000 explicitly authorized estimated debits =6,256,540 charged against14M; continuation remaining1,737,838. Zero new paid calls/debits. The live campaign deadline remains2026-09-23 04:29:36 UTC. Whole-system acceptance, publication and frozen User demonstration remain incomplete. No push.

A reusable preparation lesson was also saved as the unvalidated draft
PREP-CONTEXT-DEPENDENCIES-001: preserve referenced source context and trace assumption
ownership before choosing a behavioral repair. There are now22 maintained draft
candidates. [Candidate and provenance](CONTEXT_DEPENDENCY_META_RULE_DRAFT.json).
The added draft does not alter the rules selected for earlier validation or publish
a release. KSU remains the engineering workflow.
