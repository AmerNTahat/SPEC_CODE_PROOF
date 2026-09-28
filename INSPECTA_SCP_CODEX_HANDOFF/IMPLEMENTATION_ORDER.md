# Build milestones and required progress updates

## Update contract

At each milestone completion, and when blocked or pausing, emit a user-visible update with these exact labeled fields:

Milestone:
Identifier and state.

Achieved:
Concrete implemented behavior, not intended behavior.

In progress:
The current step and scope.

Remaining:
Outstanding milestones and acceptance work.

Evidence:
Commands executed, result files, test counts where measured, and current revisions.

Budget:
Actual reported build usage, demo usage separately, and unresolved metering limitations.

Blockers / approvals:
State precisely; do not silently skip a required check.

Record the same information in `IMPLEMENTATION_PROGRESS.md` and `reports/build/milestones.jsonl`. The included `scripts/report_milestone.py` creates labeled updates and evidence digests. These reports are development records, not independent proof that a claim is true. Print the update in Codex even if the helper wrote files. During long work, give concise progress updates at meaningful steps; do not wait until every milestone ends.

## M00 — Audit and goal integration

Inspect actual repo/local edits and source books. Compare the new goals with installed goals. Use a plan/diff then approved hash-checked installation; preserve originals. Define task scope, sources, missing dependencies, model availability, build authorization, and the real demo authorization envelope.

Completion evidence:
Repository audit, source catalog, before/after goal receipt, operation routing/configuration contract.

## M01 — Fresh validated environment

Use current Codex/Sireum and shared Loonwerks installers. Maintain digest-pinned reference and current-validated profiles; provision required solvers and example dependencies. Do not update tools during a study. Log missing permissions/auth and actual commands.

Completion evidence:
Toolchain lock, environment doctor output, real smoke checks for selected profiles. A downloaded image alone is insufficient.

## M02 — Controller, budgets and CLI

Implement shared services, persistent run state, process deadlines, permissions, transactional repair, metering capability detection, pause/stop/resume, configuration resolution and split policies.

Completion evidence:
Controller tests, CLI help and real fixed-flow run, conservation/overshoot/unsupported-hard-cap tests, configuration parity fixtures.

## M03 — Rulebook library and learning

Import existing books with provenance, deduplication/conflict review and compatibility states. Extract full-stack linguistic/spec/code/proof/test/repair patterns. Implement conditional retrieval, role bindings, model confidence forecasts, supervised generalization/specialization and release approval.

Completion evidence:
Existing-library import, meaningful candidate pattern, supporting and contrasting development case, immutable export, raw-evaluator exclusion.

## M04 — Requirements and structural checks

Reviewed requirement ledger, parsed declaration and instantiated architecture comparison, global role/name correspondence, allowed change contract, cross-stack obligations, fresh tool evidence and repair safety.

Completion evidence:
Positive renaming and negative wiring/role tests; real selected HAMR parsing/generation/proof/test commands; missing obligation and stale-proof rejection. Unsupported checks block affected acceptance.

## M05 — Guided UI

Wire the existing visual direction to real controller data. Learning/User and Automatic/Interactive are separate axes. Include manual/assisted splits, operation selector, library/repair browser, budget controls, evidence links and run control.

Completion evidence:
Browser interaction tests using actual backend, UI/CLI parity, source-link access controls. A screenshot or static HTML alone cannot complete M05.

## M06 — Evaluation, plots, traceability and attestation

Fixed unit registry, normalized metrics, separate verified/accepted/end-to-end status, DASC-style exports, real source drill-down, evidence invalidation and independent signed-bundle verifier.

Completion evidence:
Known-answer metric tests, CLI/UI/export agreement, real source mappings, tamper/stale-policy rejection. Do not fabricate 42 historical units or price assumptions.

## M07 — Required end-of-build live demonstration

Run a bounded Isolette learning -> reviewed release -> fresh User session -> real validation cycle and at least one selected additional KSU example. Include existing-project continuation and a separately declared creation/consistent-renaming test. Exercise a deliberate failure, safe repair, budget checkpoint, plots, and integrity verification.

The user's requested demo is LIVE, not a mock substituted silently. Obtain bounded authorization once before paid demo activity. A later protected rule-release publication or scope change still requires its configured approval. Demo-only approval must not authorize unrestricted real projects.

Completion evidence:
`reports/demo/DEMO_REPORT.md`, run/config hashes, commands/exit statuses, model/tool/library versions, verified-unit manifests, plots/raw data, UI screenshots or recording, attestation verification, and a replay captured from the actual completed live run. No independent final-transfer claim without a valid untouched collection.

If credentials, required tools, or budget prevent the live demonstration, publish a blocked/partial report, keep M07 incomplete, provide the exact recovery command, and separately offer the synthetic support demo. Never label that fallback a successful engineering demo.

## M08 — Handover and guided operation

Package the working CLI/UI, reproducible installation, docs and test evidence. Provide exact commands for another real learning cycle, validation, frozen release application, demo replay and experiments. Write `.scp-workbench/BUILD_RESULT.json` with executable path and evidence hashes. Verify it with `scripts/check_build_result.py`.

Completion evidence:
Executable works, evidence hashes resolve, demo status is honest, user can reopen UI and continue. Do not claim all goals complete when a tool stage, app feature or demo remains blocked.

## Installation policy update — v2.1
Reuse the downloaded Codex v_155 and suitable existing Sireum before any installation. Supply executable paths through launcher arguments or CODEX_BIN/SIREUM_HOME. Only missing approved dependencies need KSU setup. [Reuse-first instructions](installation/REUSE_EXISTING_TOOLS.md) supersede earlier generic latest/fresh-install wording.
