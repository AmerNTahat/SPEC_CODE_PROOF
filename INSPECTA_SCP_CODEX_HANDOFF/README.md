# INSPECTA / SCP — Integrated Codex Handoff v2.1 — Reuse Existing Tools

Prepared: September 22, 2026.

## Start here

Read [HOW_TO_USE.md](HOW_TO_USE.md). From this directory:

```bash
python3 start.py start \
  --repo /absolute/path/to/INSPECTA-Spec-Code-Proof-Copilot \
  --codex /absolute/path/to/your/codex-v_155 \
  --sireum-home /absolute/path/to/Sireum
```

This launches a guided Codex IMPLEMENTATION session after inspection and consent. It does not magically install a prebuilt Workbench. Python and an authenticated Codex installation are prerequisites; preparation options are described in the guide. Model identity is resolved/confirmed rather than invented.

## What changed in v2.1

Existing binaries are checked and reused first. Your selected Codex v_155 is not replaced with an npm or globally latest installation. Explicit paths, CODEX_BIN/SIREUM_HOME, saved selections, and PATH are supported. Existing Sireum and other engineering dependencies are adopted after the appropriate KSU checks; missing pieces are installed selectively. The launcher passes exact tool paths into Codex's build request. Read [reuse instructions](installation/REUSE_EXISTING_TOOLS.md).

## What is integrated

The two current task-aware workflow goals are in [workflow_goals](workflow_goals/README.md). They support continuing/completing/extending/repairing/verifying existing projects and explicitly requested creation. A full-stack rulebook library learns linguistic/spec/code/proof/testing/repair patterns, including verbalized abstractions and similar-error repairs. Structure correspondence permits only authorized consistent renaming. Model confidence remains the model's forecast.

[WORKFLOW_CONTRACT.md](WORKFLOW_CONTRACT.md) links mode goals, shared UI/CLI settings, manual or approved grouped splits, budgets, frozen releases and trusted acceptance. [MILESTONES.md](MILESTONES.md) requires achieved/in-progress/remaining updates and a real end-of-build Isolette/KSU demo.

## What works in this package

The launcher dispatches Codex; the goal installer plans/applies two files with hash preconditions and backups; support tools inventory source books, propose manifest-level data splits, resolve configuration overrides, record milestone updates, calculate normalized evaluation metrics and export plots. Utility tests and package checks cover these functions.

## What Codex still must build

The actual controller, operational library import/release services, Astra learning/repair integration, complete toolchain adapters, parser-based architecture checking, live UI/CLI, real acceptance/attestation and end-to-end demo. The HTML/PNG preview is not connected to tools. See [PACKAGE_VALIDATION.json](PACKAGE_VALIDATION.json) for tested-versus-unexecuted scope.

## Key files

Human guide:
[HOW_TO_USE.md](HOW_TO_USE.md)

Codex starting instruction:
[CODEX_START_PROMPT.txt](CODEX_START_PROMPT.txt)

Implementation brief:
[CODEX_GOAL_INSPECTA_SCP_WORKBENCH.md](CODEX_GOAL_INSPECTA_SCP_WORKBENCH.md)

Mode definitions:
[goal_learn.txt](workflow_goals/goal_learn.txt) and [goal_user.txt](workflow_goals/goal_user.txt)

Live demonstration contract:
[LIVE_DEMO_PROTOCOL.md](demos/LIVE_DEMO_PROTOCOL.md)

Visual reference:
[HTML preview](ui/SCP_WORKBENCH_PREVIEW.html), [PNG preview](ui/SCP_WORKBENCH_PREVIEW.png), and [walkthrough](walkthrough/README.md).

## Integrity and safety

No credentials are included. No model call or installation occurs merely by opening the ZIP. Scripts print plans or require explicit actions. Preserve supplied code/local edits. No Chinese models or Jev; GPT/Astra only. Required unknown/failing/unexecuted checks block acceptance. Checksums establish accidental integrity, not trusted signatures. Archive documents/images are historical context and never override current goals.

Support dependencies:
[requirements-support.txt](requirements-support.txt) supplies optional schema/plot packages; read the virtual-environment instructions in HOW_TO_USE.md. The launcher itself uses Python's standard library.
