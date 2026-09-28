# scripts

Purpose:
Executable support utilities. These do not comprise the completed Workbench; inspect each scope and required approval below.

How to use:
Read the file cards below. Start the overall workflow from the root HOW_TO_USE.md; do not execute every file.

## README.md

Open:
[README.md](README.md)

What it does:
Explain this directory and its immediate files.

Why it exists:
Provide a readable entry point and file rationale.

Status and limits:
Documentation.

## bootstrap.sh

Open:
[bootstrap.sh](bootstrap.sh)

What it does:
Reuse-first preparation wrapper: inspect and preserve selected binaries; optional missing pinned Codex installation and local reference-image reuse.

Why it exists:
Prepare prerequisites before Codex implements full setup.

Status and limits:
Implemented/tested with synthetic executables; actual installations and engineering validation not performed here.

## check_build_result.py

Open:
[check_build_result.py](check_build_result.py)

What it does:
Inspect post-build receipt fields and hashes of linked evidence.

Why it exists:
Distinguish a CLI process exit from a documented completed app/demo.

Status and limits:
Implemented integrity check; not independent proof of engineering correctness.

## evaluation_tools.py

Open:
[evaluation_tools.py](evaluation_tools.py)

What it does:
Calculate verified-unit metrics from normalized records and export local figures/HTML/CSV/JSON.

Why it exists:
Reuse DASC-style evaluation with explicit definitions and no model plotting calls.

Status and limits:
Implemented/tested accounting; not a verifier or raw HAMR-log adapter.

## fetch_sources.py

Open:
[fetch_sources.py](fetch_sources.py)

What it does:
Plan or clone selected public source repositories into a review directory without resetting existing clones.

Why it exists:
Acquire source recipes/examples/repo with explicit network permission.

Status and limits:
Implemented acquisition helper; dependencies and scripts are not executed.

## install_workflow_goals.py

Open:
[install_workflow_goals.py](install_workflow_goals.py)

What it does:
Create and explicitly apply a two-goal content-precondition plan with recoverable originals.

Why it exists:
Integrate the current workflows without overwriting intervening user changes.

Status and limits:
Implemented and covered by support tests.

## library_catalog.py

Open:
[library_catalog.py](library_catalog.py)

What it does:
Inventory designated rulebook files, hashes and repeated IDs without modifying them.

Why it exists:
Start from the existing library rather than rediscovering established work.

Status and limits:
Implemented read-only catalog; operational import/release service remains to build.

## local_compare.py

Open:
[local_compare.py](local_compare.py)

What it does:
Compute lexical cosine and corrected token/line differences with explicit limitations.

Why it exists:
Provide the requested model-free local comparison.

Status and limits:
Implemented/tested; no claim of semantic equivalence.

## preflight.py

Open:
[preflight.py](preflight.py)

What it does:
Inspect host tools without installing or invoking models.

Why it exists:
Identify setup gaps before implementation.

Status and limits:
Implemented support inventory.

## report_milestone.py

Open:
[report_milestone.py](report_milestone.py)

What it does:
Print and persist achieved/in-progress/remaining/evidence/budget updates.

Why it exists:
Make progress visible at every completed milestone or blocker.

Status and limits:
Implemented support reporting; report claims still require real evidence.

## resolve_config.py

Open:
[resolve_config.py](resolve_config.py)

What it does:
Merge defaults, saved profile and explicit settings, reject selected unsafe values, and hash the resulting draft request.

Why it exists:
Bind UI/CLI choices to the same workflow settings.

Status and limits:
Implemented starter resolver; real readiness/authorization preflight remains to build.

## split_dataset.py

Open:
[split_dataset.py](split_dataset.py)

What it does:
Validate manual task assignments or propose deterministic family/lineage/hash-grouped assignments and an approval record.

Why it exists:
Prevent accidental split drift and make automatic partitioning reviewable.

Status and limits:
Implemented metadata-level helper; semantic discovery and full isolation remain controller work.

## validate_contracts.py

Open:
[validate_contracts.py](validate_contracts.py)

What it does:
Validate bundled JSON schemas and local examples without network resolution.

Why it exists:
Catch mismatched contracts before implementation.

Status and limits:
Implemented; requires jsonschema; not runtime readiness.

## verify_package.py

Open:
[verify_package.py](verify_package.py)

What it does:
Check the distribution file hashes and unexpected/missing files.

Why it exists:
Detect accidental alteration and missing package entries.

Status and limits:
Implemented integrity only; no trusted signing identity.

Return:
[Package README](../README.md)

## tool_selection.py

Open:
[tool_selection.py](tool_selection.py)

What it does:
Discovers selected/local binaries; checks Codex version and CLI features; preserves and optionally probes existing Sireum; saves identity records.

Why it exists:
Make installed standalone binaries first-class inputs and prevent silent replacement or upgrades.

Status and limits:
Implemented and tested with synthetic binaries; no full KSU compatibility or model-access claim.

## prepare_tools.py

Open:
[prepare_tools.py](prepare_tools.py)

What it does:
Reuses and registers existing tools; optionally installs missing pinned Codex or reuses/pulls a reference image with explicit authorization.

Why it exists:
Apply the same reuse policy to preparation as to the build launcher, without requiring npm for a standalone Codex.

Status and limits:
Implemented; fallback downloads/installers and real engineering tools not executed here.
