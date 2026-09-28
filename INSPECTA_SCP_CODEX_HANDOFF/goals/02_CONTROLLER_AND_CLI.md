# Goal 02 — One deterministic controller and a real CLI
Implement a Python domain/service layer with durable run state and one shared API for CLI/UI. Prefer modest local architecture (database plus content-addressed artifact store) over distributed services.

## Operations
Inspect, prepare, retrieve, ask for judgment when needed, generate, check, repair, review, package, verify attestation, publish. Register tool operations as typed IDs with validated arguments and timeouts. Invoke subprocesses with argument arrays; do not accept arbitrary model-supplied shell strings as an authority bypass.

## Commands to implement
`inspecta-scp doctor`, `setup --install-missing`, `init`, `inspect`, `learn`, `run`, `check --offline`, `status`, `logs --follow`, `pause`, `resume`, `stop`, `review`, `rules publish`, `report`, `attest create`, `attest verify`, `experiment run`, `ui`.

Use `--config` for schema-validated profiles; CLI overrides must be explicit and reflected in the immutable run manifest. Support `--json` and readable human output. Do not replace OS `scp`. Proposed commands are not assumed to exist before this milestone.

## State and checkpoints
Track CREATED, INSPECTING, READY, RUNNING, CHECKING, REPAIRING, REVIEW_REQUIRED and terminal ACCEPTED/FAILED/BLOCKED/BUDGET_EXHAUSTED/CANCELLED. Separate provisional candidate checkpoints from accepted snapshots. A multi-step repair may continue from a provisional artifact, but cannot overwrite accepted evidence. Use atomic promotions and record parent revision.

## Control behavior
Persist event IDs, job IDs, command/agent invocations, checkpoint hashes, approvals, and budgets. Reconnecting clients must not restart work or reset budgets. Pause/stop distinguish requested versus completed cancellation; terminate spawned process groups where supported. Noninteractive unresolved approval returns a durable request and a documented exit status.

## Tests
CLI/API parity; config validation; idempotent restart; cancellation during tool/model work; failed candidate rollback; missing tools; no-progress loops; invalid operation IDs; budget exhaustion; concurrent publication; corrupted checkpoints. Mocked adapter tests are separated from real execution tests.

## Completion
A fixed Isolette workflow callable from CLI and backend, with real results and durable evidence, before adaptive learning is enabled. Follow goals/04 for the Codex and budget contracts.

## Integrated configuration and operations
Implement WORKFLOW_CONTRACT.md and both workflow_goals directly. Add `dataset inspect/propose/approve`, `rules import/catalog/review/publish`, `demo isolette --live --config`, `onboard`, and `plot/compare` commands to the same services UI uses. Route continue/complete/extend/repair/verify/create explicitly, preserving supplied code. Bind UI/CLI budgets to resolved config; do not parse hard-coded prose at runtime. Validate draft versus runnable configuration separately. `scripts/resolve_config.py` and `split_dataset.py` are starter logic to integrate/test, not parallel engines.
