# Acceptance, transfer and proof scope

The user requested two separate progress dimensions: accept behavior for the current reviewed golden scope when its checks pass and a human approves; report transfer as in progress until the same learned rule is validated on a named additional example. Then report **Accepted and transferred**, expanding coverage only to the explicitly checked examples. Each example retains its uncovered PDF requirements as current limitations.

The UI now shows per-candidate transfer state and named attempted/accepted scopes, separate from behavior acceptance and rule publication. Unattempted candidates are marked not started, not falsely called tested. A passing tool-capability fixture never establishes transfer. Current acceptance must remain valid and a passing matching rule-transfer review must exist before Accepted and transferred is shown. Loss of current acceptance removes the expansion. In progress denotes the workflow stage, not an active paid process.

## What the recorded passes actually mean

| Executed check | Target | Observed result | Scope |
|---|---|---|---|
| Logika/CVC5 | Producer/Consumer approved120ms source | PASS | Reported connection integration constraints |
| Verus | Isolated repaired Producer/Consumer consumer Rust |7 verified,0errors after repair | Contracts of that repaired component copy |
| Rust tests | Same repaired consumer workspace |5 passed | Recorded component test suite |
| Verus system proof | Official KSU system-property tutorial |111 system-crate obligations verified,0errors | Tutorial's generated composition proof; separate dependency/data counts |
| Deliberately false postcondition | Negative copy of tutorial | Expected proof failure | Negative control |
| Latest Isolette prior acceptance review | Generated Isolette | Parse/architecture PASS; formal verification and independent requirements tests NOT_RUN | No Isolette behavioral proof is attached to that review |

Evidence is `producer-consumer-compatibility.json`, `../../build/ksu-container-repair.json`, `system-property-verus.json` and `ISOLETTE_BEHAVIOR_ACCEPTANCE_REVIEW.json`. Historical failures remain preserved. In particular, the consumer proof initially failed before repair, and its SDK image build failed at that stage. Thus “all checks passed” is not accurate across all targets/history.

The earlier terse NOT_RUN wording was ambiguous: the tools did run elsewhere, but those passing proofs cannot be assigned to a different Isolette model. A new upgraded Isolette engineering check is recorded separately in `isolette-engineering.json` when completed; it is not a new paid generation or transfer result.

## Current golden limitations

Keep the three examined feature groups visible: elapsed initialization timeout, desired-bound/order producer guarantees, and strict sub500ms response timing. They are labeled **Not supported in golden yet**, not unsupported in the tool. This is a partial inspected feature inventory, not an assertion that every remaining PDF requirement was proved. See `GOLDEN_COVERAGE_ACCEPTANCE.md` and the persistent notes. No automatic waiver or human approval is fabricated.

## Fresh upgraded Isolette engineering check

Executed unchanged latest generated Isolette in rund203636c718c436fb8a0393807635595 with upgraded Sireum, CVC5 and Microkit generation;65.15 seconds, no paid calls. Parser and architecture export PASS. Logika exited0 but supplied no nonempty integration-constraint proof evidence, so integration remains UNKNOWN, not PASS. Generation emitted45 C files,0 Rust files and0 Cargo manifests. The expected Rust/Microkit gate therefore remains UNKNOWN. No Verus proof of this Isolette ran.

The source does not select the `Implementation_Language = HAMR::Implementation_Languages::Rust` property used by the Producer/Consumer example. The generator output is therefore not the Rust verification workspace that the current adapter expects. This is a configuration/evidence gap, not a demonstrated language limitation or a reason to waive English requirements. The C artifacts and original logs remain preserved. No model or golden was edited, and no exhausted model-repair budget was reset. The check neither accepts Isolette behavior nor establishes rule transfer.
