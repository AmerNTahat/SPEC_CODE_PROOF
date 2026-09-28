# INSPECTA/SCP Workbench checkpoint

Selective source checkpoint before UI performance and multi-server work. This is a local application in development, not a production release or a claim of complete system verification.

## Build and start

Requirements: Python 3.11+ with venv/pip and Node.js/npm compatible with the committed frontend lockfile. An internet connection is needed for the initial dependency installation. See [the dependency and tool guide](docs/DEPENDENCIES.md).

```sh
# Run from the repository root. Select an existing Python 3.11+ if needed:
# export INSPECTA_PYTHON=python3.11
./scripts/setup-workbench.sh
./inspecta-scp onboard
./inspecta-scp ui --port 8766
```

Open the private loopback URL printed by the server. Do not share its token. The default UI uses the bundled starter profile and empty rulebook directory. Set up learning opens without downloading tools or calling a model. The starter model is a UI fixture, not a verified engineering example. With no Sireum configured, formal checks remain unavailable rather than passing.

```sh
PYTHONPATH=workbench .venv/bin/python -m unittest discover -s workbench/tests
mkdir -p reports/build
PYTHONPATH=workbench .venv/bin/python workbench/tests/run_browser_smoke.py
```

The optional browser test requires Firefox and local socket access. It uses synthetic projects and makes no model calls. Raw test/build output stays ignored.

## What is included

- Shared Python controller/CLI/API, React UI source, schemas, adapters, tests and pinned application dependencies.
- Portable default startup plus historical profile templates for reference.
- [Draft rulebook revision export](rulebooks/README.md), retaining its unvalidated/release-pending status.
- [Recorded engineering results and limitations](reports/checkpoint/RESULTS.md). These are historical summaries, not bundled proof evidence or results for the starter fixture.

The application starts with an empty local SQLite state. Importing a readable draft export is not a substitute for restoring its source records, approvals and evidence. The private campaign database, logs, PDFs, source example collections, model replies, installed tools and generated workspaces are not distributed. Existing remote legacy files remain as they were; the checkpoint adds the Workbench without extending unrelated legacy work.

## Known limitations

Large Learning/Rulebooks views currently rebuild extensive evidence and may be slow. The planned summaries, lazy loading, PostgreSQL, multi-user authentication and distributed workers are not implemented by this checkpoint. The API is loopback-only and its local access token is not a multi-user identity system. Do not expose it as a production multi-user service.

Independent rule transfer/release and the complete frozen User demonstration remain incomplete. A passing component proof or scoped exclusion is not whole-system acceptance. No user credentials or paid-run authorization are included.

Older workflow documents are retained for implementation history. For installation and checkpoint scope, this README and `docs/DEPENDENCIES.md` take precedence over historical machine paths or outdated readiness statements in those documents.

## Development handoff

Read [the current handoff status and continuation guide](docs/HANDOFF_STATUS.md) before using the [original handoff package](INSPECTA_SCP_CODEX_HANDOFF/START_HERE.md). The package is preserved unchanged for provenance; its original packaging results and proposed milestones do not describe current completion. Continue the existing application in the current session; do not launch another implementation session with `start.py start`.
