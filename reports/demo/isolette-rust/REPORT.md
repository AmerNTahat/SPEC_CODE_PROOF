# Actual Isolette Rust, GUMBO, Verus and GUMBOX work

This is a supervised implementation/debugging experiment on isolated copies, not an accepted system or published/transferred rulebook. Original models, golden files, implementations, books and tools are preserved. No paid model call was made.

## Existing behavior and actual Rust selection

The latest generated Regulator already contained four GUMBO blocks: interface, regulator mode, heat source and failure reporting. The copied Monitor has three, Operator Interface one, and the data model three invariant blocks. `CONTRACT_INVENTORY.json` inventories these source blocks; it is not a complete English-coverage or verified-unit count. The missing work was implementation/proof, not a complete absence of behavior specifications.

Following the approved KSU `component-implementation-guide.md`, `testing-guide.md` and CLI guide, all11 thread definitions in a new model copy select `HAMR_AADL::Thread` and `Implementation_Language = HAMR::Implementation_Languages::Rust`. The exact change is `rust-backend.patch`; no original/reference file changed. Platform Microkit alone does not select Rust per thread.

The real Rust backend failed at Float64 literal0.0 in the timeout GUMBO contract. `checks.json` preserves that error. A separately preserved candidate uses Integer64 milliseconds and strict>1000 instead of floating-point seconds and>1.0. That candidate parses, exports architecture and generates Rust/Microkit artifacts (`integer-clock-checks.json`). It is not accepted: clock sampling/units, overflow, progress and the overlapping timeout/healthy guards remain explicit review/proof obligations. This is an alternative representation, not a waiver or proof that temporal English is unsupported.

Logika was actually executed for both model revisions. It returned0 but established no nonempty integration-constraint proof. These models' GUMBO blocks do not declare the port integration clauses used by the Producer/Consumer example. Local compute contracts are not thereby proved. Do not turn empty success into behavioral verification.

## Actual generated implementation checks

The existing pinned KSU Docker worker supplied Rust1.92.0/Verus0.2026.01.23.1650a05 and cached dependencies, offline. All11 generated component crates were checked with their real `make verus` and `cargo test` commands:22 commands,6 successful. The three scaffolding components that passed without substantive GUMBO contracts are not counted as verified English behavior. Most application entry points were generated stubs, so failed postconditions and absent output DataPort panics were expected implementation defects, not missing tool support.

Evidence: `verification-baseline.json`. Each record retains commands, stdout/stderr, exit status, durations and source hashes. No `assume`, `admit` or new `external_body` was inserted to bypass proof. Existing generated logging/API trust boundaries remain unchanged.

- **Regulator failure-output propagation repaired:** initialize and compute publish the existing diagnostic-state flag. Verus:7 component obligations verified,0errors. Tests:5 passed, including3 GUMBOX suites. This proves conditional output propagation, not completeness of a hardware fault detector. See `detector-implementation.patch` and `verification-detector-repair.json`.
- **Monitor interface implemented:** adapted the algorithm already in `isolette/hamr/microkit/crates/thermostat_mt_mmi_mmi/...`, preserved new generated contracts, initialized all output DataPorts and used match expressions for enums. Verus:14 component obligations verified,0errors;4 tests passed. See `monitor-interface-reuse.json` and `verification-monitor-interface.json`. This is explicit implementation reuse, not new held-out transfer evidence.
- **Heat implementation still fails:** after fixing unsupported executable enum equality with an equivalent match, Verus reports10 verified/1error at REQ_MHS_3. GUMBOX reports3 test functions passed/2 failed. A concrete shrunk witness is Normal,current0,lower1,upper−1: REQ_MHS_2 requires On and REQ_MHS_3 requires Off. These values satisfy the broad Earth-temperature datatype range but no ordered-bound premise was declared. No conditional priority can satisfy both outputs. See `verification-heat-match.json`.

The dependency library's1190 proofs and the data crate's20 proofs are recorded separately; they are not new Isolette English requirements.

## Three-failure stop and human guidance

Heat baseline, first implementation and enum-match implementation all failed validation. Automatic heat repair stopped. `ordered-bounds-PROPOSAL.patch` adds a specific component assumption, Lower_Desired_Temp.degrees <= Upper_Desired_Temp.degrees. It is **pending human review**, with the source/environment rationale and exact counterexample in `ORDERED_BOUNDS_REVIEW.json`. Even if approved for a conditional component proof, producer/composition discharge remains open; no guarantee is deleted or whole-system acceptance inferred.

The current golden omissions remain disclosed separately. They cannot explain away contradictory active contracts or missing application bodies. The timer representation candidate also remains unaccepted.

## What “five Producer/Consumer tests” meant

The prior repaired consumer output names two basic tests (`test_initialization`, `test_compute`) and three generated GUMBOX suites (`prop_testInitializeCB_macro`, `prop_testComputeCB_macro`, `prop_testComputeCBwGSV_macro`). The suites are configured for100 valid cases each. These are five test functions/suites, not five distinct English requirements. Both the real output and generated `src/test/tests.rs` were inspected. The two basic tests are not a substitute for the GUMBOX postcondition checks.

## Maintained learning and replay

Reused rules include RA-001 (assumption ownership/discharge), the mode-qualified hysteresis rules and the KSU implementation/testing workflow. New unvalidated draft `RUST-CONTRACT-REALIZATION-001` records explicit backend selection, numeric-representation diagnosis, DataPort initialization, preserving generated contracts and separate Verus/GUMBOX validation. There are25 maintained draft candidates; no rule release or transfer is claimed.

Reproduction scripts: `workbench/tests/run_isolette_rust_checks.py`, `run_isolette_integer_clock.py`, and `run_isolette_rust_verification.py`. Initial model scripts preserve existing experiments rather than overwrite. The verification script checks the existing campaign deadline and stops before its reserve; it requires the already installed Docker worker and cache. Reports name exact model/output/worker identities. No tool reinstall or upgrade was needed.

### Final component result and assembled candidate

The existing Monitor mode transition relation was implemented without adding a timeout or changing its contracts. Verus and all generated tests passed; exact counts are in `verification-monitor-mode.json`. This is local golden-scope component evidence, not a physical deadline proof.

The three separately checked application bodies (regulator failure-output, Monitor interface, Monitor mode) are assembled in `.scp-workbench/isolette-rust/rust-assembled-candidate`; `ASSEMBLED_CANDIDATE.json` binds their hashes to their proof reports. Other components retain unimplemented scaffolding. No complete-build or system acceptance is claimed for the assembly. The original/generated baselines and each failed/repair workspace remain preserved.
