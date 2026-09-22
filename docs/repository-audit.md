# Repository audit — 2026-09-22

Scope: implement the Workbench alongside existing code in this checkout. No reset,
cleanup, permission changes, push, paid model run, or legacy model/rulebook edit.

## Identity and preservation

Initial commit: `e994e5babe6701aa4907ef32f08db34e712865ee`, initial branch `master`.
Development branch: `inspecta-scp-workbench-20260922`.
Existing tracked modifications: `.gitignore`, `sireum_verification_plan.txt`.
Their hashes and selected legacy-file hashes are in
`reports/build/preserved-input-hashes.json`. The root ignore policy excludes most
root files; do not mistake ignored work for absent work or replace that policy.
Nested source identities are in `reports/build/source-revisions.json`; a parent
repository identity does not establish that an ignored nested directory is pinned.

Several historical trees, including `codex_mcp_workflow`, `all_for_test`, and
`isolette_before_nightly`, have inaccessible descendants. They were not chmodded,
copied, or declared audited. Historical DASC evidence remains untouched. No new
42-unit registry or historical performance claim has been inferred.

## Handoff and goal integration

All 121 manifest entries passed `scripts/verify_package.py` (integrity, not signed
authenticity). Handoff references resolve under `INSPECTA_SCP_CODEX_HANDOFF`.
Repository targets are distinct: its two revised workflows specify
`SCP-extention-artificats/isolette_io_extnded/`. That target was absent. The reviewed
plan created only those two files; it did not overwrite the actual older workflows
in `isolette/sysml`. See goal-install-plan.json, goal-install-review.json,
workflow-goals-review.diff, and goal-install-receipt.json under reports/build.

Read: start prompt, START_HERE, workflow contract, milestones, master goal, both
revised mode goals, user decisions, reuse-first instructions, focused installation
and controller/budget goals. Historical archive instructions are not active.

## Reusable sources and confirmed defects

* `isolette/sysml`: existing SysML models, goals, model libraries, rulebooks and
  historical evaluation folders. Only model/library copies were used for smoke
  checks; evaluation folders are not generator context.
* `rule-books_7`: 32 catalogued documents. Isolette's `rule-books`: 11 documents.
  Both catalogs report 10 MR identities with repeated occurrences. Repeated IDs
  are pending duplicate/conflict review, not independently verified rules.
* `HAMR-agent-configuration-experiments/hamr-claude-training`: local modeling,
  implementation, testing and CLI instructions; Simple Isolette and event-data
  Producer/Consumer examples. Network Guard is not in the inspected example list.
* `tools/self_adapt.py:extract_block` and `embedding_distance.py:extract_block`
  search forward beyond a declaration's owner boundary; a later owner's GUMBO
  could be returned. These legacy routines must not become trusted checks.
* `tools/self_adapt.py:strong_diff` sums opcode end positions rather than edit
  lengths. Its embedding mode invokes an API. Workbench offline comparison must
  use the corrected local helper and never silently fall back to embeddings.
* `tools/gumbo_tools.py` emits `assume true` / `guarantee true` placeholders. It is
  not a source-faithful contract synthesis or acceptance implementation.

## Runtime repair and reuse

The original `codex-resources/bwrap` symlink referred to an older package.
The official v0.155.1 full package was downloaded, its published archive checksum
verified, and its bwrap digest checked against the running session's expectation.
Existing `codex`, `codex-155`, and the supplied helper match the package bytes.
They were not replaced. The old resource link is saved alongside the new link;
the entire old package remains intact. The verified package is preserved under
`tools/codex-runtime-v0.155.1`; REPAIR_RECORD.json records provenance.
Normal sandboxed execution works after the repair. Elevated execution was used
for the authorized repair and local branch creation, not engineering checks.

Selected Codex: root `codex-155`, actual 0.155.1, CLI/help checks passed.
Sireum: honor existing SIREUM_HOME, with initialized JAR and JVM. Actual build:
`4.20260323.9c4caf1f`. Sireum was not reinstalled or upgraded.
Existing `.venv/bin/python` is 3.11.11; default python3 is 3.8.10. Existing Node
on PATH is 10.19.0. Cargo/rustc/Verus were not found on PATH; absence from PATH
does not prove absence from the host. No tool bootstrap was executed.

Real `hamr sysml tipe` checks ran on separate copies of Isolette and KSU
Producer/Consumer. Both exited zero with `Well-formed!`; Isolette also reported
instantiation warnings and missing substituted datatypes. These remain visible
and preclude claiming full engineering compatibility. No proof/build result is
inferred. The initial unsupported `type-check` help probe is retained in the log;
the documented and checked command is `tipe`.

## Configuration/operation contract

One Python controller must serve CLI and UI. Resolve defaults, saved profile and
explicit overrides, then validate authorization and hash the immutable result.
Null is deliberate. Auto cannot authorize creation. Existing project operations
preserve source and names; checks operate in disposable input snapshots. A tool
exit code is separate from parse, proof, requirements, architecture and acceptance.
Unknown/stale/missing required gates block acceptance. Runtime model generation is
not authorized merely because application implementation is authorized.

## Remaining readiness decisions

M01 still needs generation, proof, build and selected dependency compatibility
checks, reference profile validation, model availability and event-adapter checks.
Attempts to retrieve the handoff's Loonwerks provers-env recipe URLs returned
cache-miss errors; the assumed local provers-env directory is absent. No unreviewed
replacement installer has been run. Model credentials have not been read or printed.
No enforceable token ceiling was found in inspected Codex exec help. Paid demos
need a bounded authorization and an explicitly accepted enforcement policy, plus
later release review. The current implementation session has no exposed aggregate
token/billing meter; demo model usage is zero. Build and demo ledgers stay separate.
