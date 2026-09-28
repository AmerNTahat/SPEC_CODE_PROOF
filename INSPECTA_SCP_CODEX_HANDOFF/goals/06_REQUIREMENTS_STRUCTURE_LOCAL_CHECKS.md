# Goal 06 — Complete obligations, intact architecture, local diagnostics
## Reviewed requirements
Build a source-backed requirement ledger with IDs/sub-obligations, locations, owner, intended representation and acceptance method. Astra may draft it; independent review approves the acceptance source. Freeze ledger/policy for a run. Missing source decisions remain unresolved. Candidate agents cannot delete obligations, strengthen assumptions or weaken guarantees to obtain a pass.

Coverage checks reference actual resolved elements, not labels alone. Distinguish mapped, checked and semantically reviewed. Nonbehavioral requirements need proper architecture/timing/deployment/review checks rather than fictitious GUMBO clauses. Trace links are not proof of faithful meaning.

## Structure
Use parsed/resolved Sireum/HAMR output through an adapter. Compare required declarations and instantiated architecture: archetypes/component definitions, hierarchy, ports/kinds/types/directions, connections, role identity, relevant scheduling/units/bindings, GUMBO ownership.

Support explicit equivalence, approved-change conformance, and new-design conformance. Check against the approved architecture and diff against the pre-repair candidate. Preserve unaffected obligations across the project. Unknown syntax/constructs and timeouts never silently pass. Equivalent names require approved mappings, not arbitrary graph matching that hides same-type swaps.

## Local checks
Audit helper implementations before patching. Implement model-free token-vector cosine and corrected line/token differences with no network fallback. `scripts/local_compare.py` is a tested lexical starting utility, not a SysML parser or semantic oracle. Its tokenization/sequence distance are versioned and ordering limitations explicit. Both-empty vectors give an undefined score rather than automatic perfect acceptance.

Legacy API cosine remains disabled by default. Keep retrieval indexes apart from evaluator references. Freeze corpus statistics on allowed sources. Do not return hidden-reference distances to final target generation.

## Tool gates
Parse/type check -> coverage -> structure -> project generation/build -> independent tests and supported formal verification -> review. Cache evidence only with exact source/artifact/tool/policy identities. Unknown/missing mandatory evidence blocks acceptance. Verify command output and expected artifacts; exit status alone may not establish all obligations ran.

## Required negative tests
Missing contract; contract on wrong part; duplicate requirement IDs; missing or reversed connection; same-typed role swap; port-kind change; wrong unit/period; removed initialization; changed `<`/`<=`; contradictory assumptions; disabled tests; unapproved proof bypass; stale library; unsupported construct; empty test suite. Test valid rename/unit normalization under the explicit policy as positives.

Completion: injected defects are detected and rejected without weakening acceptance; reports identify exact obligations/elements and scope limits.

## v2.0 task-aware structure and naming
Implement both declaration/ownership and instantiated-architecture views. For same-architecture reconstruction use one global scope-aware, role-preserving mapping; display-name changes cannot hide swapped same-typed endpoints. Preserve external library/ABI identities by default. For supplied projects use an approved delta and baseline defect list, not blind equivalence to incomplete/wrong input. Regenerate generator-owned APIs after authorized name changes and recheck all affected references/contracts/tests/proofs. AADL and SysML revisions need reviewed normalization and declared scope, not assumed equality. Use full-system and partial-system creation/continuation tests.
