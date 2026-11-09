# Golden contradiction repaired and accepted by human

**Status: REPAIRED_GOLDEN_DEFECT_ACCEPTED_BY_HUMAN**

One accepted defect-repair validation case: Isolette Regulate / Manage Heat Source, conflicting REQ-MHS-2 and REQ-MHS-3. This is a conditional component result under a human-approved repaired contract, not an unchanged-reference pass or whole-Isolette acceptance.

## Human curation and source citation

The user approved the strict ordering discussed in the prior response, requested that we apply the repair, maintain a meta-rule, cite the discovered golden defect and guidebook, and count checked repairs in a separate human-accepted category. Exact consent and evidence identities are retained in `GOLDEN_DEFECT_ACCEPTANCE.json`.

Original `isolette/sysml/Regulate.sysml` lines384–393 has NORMAL/below-lower -> On and NORMAL/above-upper -> Off, without a local desired-bound ordering assumption. FAA AR-08-32 REQ-MHS-2/3 appears in the actual generated-task English at `ACTUAL_GENERATION_ENGLISH.txt` lines237–241. The missing ordering dependency is discussed in FAA EA-OI-6 (PDF102/printedA11); its extracted wording and rationale are preserved in `../behavior-review/PREPARED_ENGLISH_WITH_DEPENDENCIES.md` lines426–430. The rationale explicitly warns of the On/Off ambiguity from reversed bounds.

The real GUMBOX failure and the executed CVC5 witness current98/lower99/upper97 document the contradiction. Original golden files and failed results remain unchanged. Golden inspection and human curation make this supervised development evidence; it is not independent held-out transfer evidence.

## Applied repair

The isolated model `.scp-workbench/isolette-rust/ordered-bounds/Regulate.sysml` now has:

```text
assume ORDERED_DESIRED_BOUNDS:
    Lower_Desired_Temp.degrees < Upper_Desired_Temp.degrees;
```

This is **strict ordering**, as approved, rather than the earlier unapproved <= proposal. No heat guarantee was removed. The exact possible one-degree FAA margin is not claimed by this correction. The applied patch is `ordered-bounds-ACCEPTED.patch`.

The preserved golden now also has an isolated corrected reference at `.scp-workbench/isolette-rust/reference-ordered-bounds/Regulate.sysml`, with the same strict premise. Its parsing and architecture export passed (`golden-ordered-bounds-checks.json`); `golden-ordered-bounds-ACCEPTED.patch` records the exact golden correction. `HUMAN_CURATED_HEAT_ENGLISH.md` records the corresponding scoped English dependency amendment. The original golden and earlier English preparation are unchanged.

HAMR generated the corresponding Rust `requires` clause and GUMBOX precondition. The successful implementation is `.scp-workbench/isolette-rust/rust-ordered-bounds-synced`; it preserves the regenerated contract and migrates only the previously implemented heat body. No new assume/admit/external_body was inserted in application logic to suppress a proof.

## Executed validation

| Check | Result | Evidence |
| --- | --- | --- |
| Sireum parsing/type checking | PASS | `ordered-bounds-checks.json` |
| Architecture export | PASS | Same report; this is export, not a new full graph-equivalence claim |
| Rust/Microkit generation | PASS | Same report |
| Heat component Verus | 11 verified, 0 errors | `verification-ordered-bounds-synced.json` |
| GUMBOX and basic tests | 5 passed, 0 failed | Same report; three property suites and two basic test functions |
| Integration assumption discharge | UNKNOWN/open | No nonempty integration proof establishing producer ordering |

Dependency Verus counts1190 and20 are listed separately in the raw report; they are not added to the component count or treated as English requirement counts. The successful component proof took37.48seconds and the test command11.23seconds, including build overhead. No paid model call was used.

## Failure lessons from the repair

The first attempt to migrate the heat implementation copied the entire previous app, including its empty `requires`. GUMBOX used the newly generated precondition and passed, but Verus correctly still failed one heat postcondition (10 verified/1error). This was our migration mistake. Evidence remains in `verification-ordered-bounds.json`.

The next revision retained the freshly generated contract and migrated only the executable bodies; both tools passed. `ordered-bounds-generated-contract-sync.patch` shows the correction. Together with the previous baseline/enum/match failures, this is the fifth recorded component round, within the approved six-attempt checkpoint. Sandbox startup failure is retained separately and does not claim an executed proof attempt.

Meta-rule `GOLDEN-DEFECT-CURATION-001` records contradiction citation, explicit human curation, regeneration, contract-preserving implementation migration, proof/test revalidation, separate counting, and retained obligations. The reusable rule remains draft pending transfer; the concrete repaired case is accepted. Its provenance and current immutable learned-book location are in `GOLDEN_DEFECT_META_RULE.json` (27 draft candidates).

## Validation criterion and UI

The controller and UI now expose `REPAIRED_GOLDEN_DEFECT_ACCEPTED_BY_HUMAN`. Acceptance requires cited contradiction evidence, a human comment/consent, current repaired artifacts, matching model/proof identities, and passing scoped parser/codegen/Verus/GUMBOX results. Changed evidence revokes the accepted count. Revisions of the same case count once.

The UI section **Golden contradictions repaired with human approval** displays the status, human comment, citations, one accepted repair case, and open obligations. This case does not inflate unchanged-golden passes, whole-system success, or rule-transfer counts.

## Remaining obligations

- Prove that the producer/operator interface establishes strict ordering, or explicitly require it from the environment at the system boundary.
- Resolve the exact guidebook margin if the scope is expanded beyond this approved strict-ordering correction.
- Complete remaining Isolette implementations and timing/clock obligations independently.
- Validate reusable-rule transfer on additional examples before rule release.

Application verification:159 tests passed, frontend build passed,30 real Firefox UI checks passed. Those application checks are separate from the real engineering checks above. M07 remains incomplete. The build receipt retains `partial`/`validation_failed` for the unfinished aggregate demonstration, while this scoped repaired golden defect is accepted.

Budget:20-minute extension recorded; no new paid calls. Campaign remains1,256,540 measured +5,000,000 estimated =6,256,540 charged /14M; continuation remaining1,737,838.
