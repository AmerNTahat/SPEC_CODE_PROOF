# One workflow, one configuration, one controller

Version: 2.0, September 22, 2026.

## Responsibilities

Handoff:
Tells Codex what software and integration tests to implement. It is not loaded into every runtime agent call.

Learning workflow:
`workflow_goals/goal_learn.txt` is the authoritative Learning Mode behavior.

User workflow:
`workflow_goals/goal_user.txt` is the authoritative User Mode behavior. Continue an existing codebase when requested. Creation from scratch requires explicit selection or a declared approved benchmark.

Runtime configuration:
Carries actual paths, task operation, data assignments, toolchain/model identities, release, assistance and budget. UI/CLI create equivalent requests; neither is privileged over the other.

Controller:
Validates and enforces permissions, scope, budgets, checkpoints, checks, approvals and evidence. Agent statements are not acceptance evidence.

Rules:
Supply scoped engineering knowledge. They cannot override permissions, requirements, acceptance checks or budget policy. The combined release selects specialized books, rather than concatenating all context on every call.

## Configuration precedence

Application defaults -> chosen saved profile -> explicit UI/CLI values -> authorization and policy validation -> immutable resolved configuration and hash.

Explicit null is not the same as an omitted override. UI must send only deliberate changes. No goal-file literal may silently replace a resolved value. Budget increases need recorded approval and preserve prior consumption. A data/model/tool/library/policy amendment invalidates affected evidence.

The build session's budget, the post-build demo campaign budget, and an individual learning/user run budget are different. No unlimited automatic retry loop may hide behind that distinction. Experiment budgets aggregate all trials.

## Task operations

`auto` only resolves intent before writes; it does not grant permissions.

`continue-project`, `complete-system`, `extend-system`, `repair-system`, `verify-only`, and explicitly authorized `create-system` are supported. Missing one file does not authorize a new whole system. Mixed tasks record per-artifact changes. Verify-only may emit reports in the output area, but must not edit supplied source artifacts.

## Data roles and split controls

User-assigned:
The user supplies learning/development directories or approved task manifests. Preserve assignments; detect leakage and conflicts. Do not silently move files or change labels.

Propose-grouped:
Inventory tasks and source lineage, propose a deterministic seeded assignment with explicit fractions, and ask for approval of membership/hash. Group connected families, descendants, renamed variants, and duplicate source/solution content. The supplied helper is a manifest-level partitioner, not a semantic dataset discoverer. Unknown lineage is a blocker for an independence claim, not guessed independence.

Shared context:
Approved general libraries/manuals can be available across roles when explicitly declared. Do not hide target-specific worked answers in the shared context.

Learning:
Approved sources and solutions may inform extraction.

Development:
Feedback can improve candidate rules and policies. Support/query tasks must respect lineage; query reference artifacts stay evaluator-only.

Final transfer:
The release/policy is frozen. Reference outputs, graph witnesses and golden similarity scores are evaluator-only and cannot drive repairs. Legitimate task diagnostics remain available under the predeclared protocol. An optional final collection is required before claiming final transfer, not before every learning session.

## Acceptance scope

Reconstruction: structure equivalence under one global scope-aware role-preserving bijection and permitted internal renaming.

Completion/extension: approved delta plus unchanged obligations; do not reject additions because the starting model lacked them.

Repair: correct the permitted defect and preserve unaffected architecture, contracts and behavior.

New design without a unique reference: conformance to reviewed requirements/architecture constraints, not invented equivalence.

A matching graph does not prove behavioral equivalence. Lexical cosine does not prove semantic correctness. Type-checking does not prove source fidelity. Testing is not formal proof. Signatures establish integrity/attribution under their trust assumptions, not certification.

## Shared UI/CLI contract

Expose the same dataset roles, split proposal/approval, requested operation, protected scope, rule release, model/profile, budgets, and assistance. A result click must connect unit -> requirement -> rule/binding -> model/code -> executed tool -> evidence. Protect evaluator-only references from agents regardless of what an authorized human can inspect.

## Implementation checks

Test UI/CLI parity, overriding a preset, paused/resumed consumption, unapproved split changes, conflicting family assignments, source changes after approval, invalid rule bundles, unauthorized creation/renaming, stale proofs, missing checks, and bounded repair. Definitions live here and in the two mode goals; focused goals explain implementation, not a competing policy.

## Installation policy update — v2.1
Reuse the downloaded Codex v_155 and suitable existing Sireum before any installation. Supply executable paths through launcher arguments or CODEX_BIN/SIREUM_HOME. Only missing approved dependencies need KSU setup. [Reuse-first instructions](installation/REUSE_EXISTING_TOOLS.md) supersede earlier generic latest/fresh-install wording.
