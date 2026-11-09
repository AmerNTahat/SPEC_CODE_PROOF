# Documented tool upgrade and version-scoped validation

2026-09-23. Development capability evidence only. Whole-system acceptance remains false.

## Recommendation and selected version

Use the isolated numbered Sireum **4.20260810.80aad0c2** for the next reviewed validation task. The official HAMR changelog identifies **4.20260720.6a05e505** as introducing GUMBO system-property verification; the later numbered release was actually installed and tested here. Do not infer that arbitrary temporal logic or physical timing is automatically supported.

Sources: [HAMR changelog](https://github.com/sireum/hamr-codegen/blob/master/changelog.md), [system properties](https://hamr.sireum.org/hamr-doc/gumbo-system-properties/), [installation](https://hamr.sireum.org/hamr-doc/installation/), [selected release](https://github.com/sireum/kekinian/releases/tag/4.20260810.80aad0c2).

The official CLI and JVM artifacts were checked against release digests. The original Sireum, Codex, source, golden/reference files and existing rulebooks remain unchanged. `toolchain.lock.json`, `installation.json`, `jar-receipt.json`, `jvm-reuse.json` and `tool-source-tree.json` record identities. The installation receipt describes the initial unpacking stage; subsequent dependency initialization is recorded separately.

New UI profiles: `workbench/profiles/isolette-upgraded.check.json` uses the already approved isolated reference; `producer-consumer-upgraded.check.json` uses the previously approved 120ms source. Historical profiles remain available. Existing development tasks retain their original tool selection; choosing a new profile does not silently revise their approvals.

## Executed results

| Check | Result and scope |
|---|---|
| Integer state/elapsed time, initialization and `In` | PASS on new tool; also supported previously |
| Tested native `until` spelling | Rejected; this does not establish that equivalent state encoding is impossible |
| Documented GUMBO `composition` | PASS on new tool; rejected by prior selected tool |
| Fresh historical Isolette candidate and approved isolated reference | Both parse and export architecture successfully |
| Directed architecture comparison under new tool | PASS, full name-independent bijection: 1162 vertices and 3164 directed edges |
| Producer/Consumer approved 120ms source | Parse, architecture, Rust/Microkit generation and connection integration constraints PASS with CVC5 |
| Official KSU system-property fixture | Generated Rust and actual Verus system-property proof PASS |
| Deliberately false system-property postcondition | Expected Verus failure observed; positive source unchanged |

Evidence: `gumbo-capability-probes.json`, `isolette-compatibility.json`, `isolette-directed-graph.json`, `producer-consumer-compatibility.json`, `system-property-codegen.json`, `system-property-verus.json`.

The official tutorial is pinned at [50c90fa356c436c1ceb4d4138a9d32fe8369829c](https://github.com/santoslab/hamr-tutorials/tree/50c90fa356c436c1ceb4d4138a9d32fe8369829c/HAMR-SysMLv2-Rust-seL4-P-DP-SysPropStructSplit). It is a tool-capability fixture, not new training material or a substitute for Isolette/Producer-Consumer acceptance. The existing pinned Docker worker supplied Rust 1.92.0 and Verus 0.2026.01.23.1650a05. Verus reported 1190 dependency, 2 data and 111 system-crate obligations verified, zero errors. These are not counts of distinct English requirements. A separate mutated copy produced the expected postcondition failure.

## Compatibility repairs and limits

The new JVM requires JDK25.0.3+11; the matching existing download was reused in the isolated home. Compatible Scala, plugin and Coursier artifacts were reused. The inspected KSU solver setup invokes Sireum initialization; its log includes an unsuccessful unrelated Verilator build due to missing autoconf, despite exit0. No claim is made that every optional initializer component succeeded. Autoconf/Verilator and host glibc were not upgraded.

Bundled Z3 4.16.0 cannot run against this host's glibc. This is an environment limitation, not unsupported English. CVC5 1.3.4 works; both SAT and validity integration backends explicitly select it. The initial failed Z3 integration evidence is retained in `producer-consumer-default-z3-failure.json`.

The controller selects the JVM for architecture/codegen/integration where available, supplies the explicit workspace root and permits writes only to an isolated model cache/output. Source-level `//@ HAMR:` output overrides are neutralized in an execution copy, with original/derived hashes and preserved line positions; original source is untouched. Prior failures remain in this directory. Reproduction scripts are in `workbench/tests/run_*upgrade*.py`, `run_system_property_verus_check.py` and `run_gumbo_capability_probes.py`.

## Requirement deferral repair principle and UI

The UI now supports a reviewed capability scope: select prepared English and an executed capability check, identify the exact requirement excerpt, classify the failure, record alternatives/evidence/revisit conditions, then approve the scope. Validation can select that approved scope. Pending, stale or mismatched scopes exclude nothing. Only approved `NOT_SUPPORTED_TOOL_VERSION` targets become deferred; no passing credit is assigned, the original total remains visible, and a tool change invalidates the exclusion. Modeling and implementation/timing failures stay mandatory. Backend and UI checks exercise these distinctions.

**No Isolette English requirement has been excluded in this update.** Native syntax rejection alone is insufficient evidence. Missing range contracts and timeout semantics can be represented with current logic/state; a 1000ms period versus a strict <500ms requirement is a scheduling conflict, not an expressiveness waiver. System composition verification does not automatically establish physical clock accuracy, progress, scheduler bounds or arbitrary temporal formulas.

The new repair principle is maintained as draft `REPAIR-TOOL-CAPABILITY-001`, with provenance, counterexample and required validation. `CAPABILITY_REPAIR_META_RULE_DRAFT.json` links its immutable snapshot; the learned-book index now contains 23 candidates. No rule has been published or automatically declared validated.

## Remaining work and budget

Isolette timeout priority, source-boundary assumptions, clock progress and physical timing require the behavioral decisions described in `../behavior-review/REVIEW.md`; upgrading does not choose them. Supplemental prepared English remains pending review. Existing eight model-repair attempts remain exhausted; no repair reset or new paid generation occurred. Full M07 fresh frozen User demonstration, all behavioral/engineering gates and independent acceptance remain incomplete.

148 application tests and 25 real Firefox UI checks passed after these changes. These application checks are separate from the executed tool proofs above. No paid model call or debit was added. Recorded usage remains 1,256,540 measured plus 5,000,000 estimated = 6,256,540 charged against14M; continuation allowance remaining1,737,838. The authorized extension deadline is2026-09-23 05:57:37 UTC. Live budget snapshot is in `../CAMPAIGN_STATUS.json`.
