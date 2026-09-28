# Build dependencies and optional engineering tools

## Application build

Use Python 3.11+ in a virtual environment. `requirements.txt` declares direct dependencies; `requirements.lock` pins the resolved dependency set tested for this export. The setup script installs only into `.venv`. The core application uses SQLite; no PostgreSQL migration is part of this checkpoint.

`workbench/frontend/package-lock.json` pins React 18.3.1, TypeScript 4.9.5 and associated build dependencies. The current verification host reused Node 10.19.0/npm 6.14.4. That is an old toolchain and is not a recommendation for an internet-facing deployment; validation on a maintained Node release remains future work. The server serves React assets from installed `node_modules`, so a generated `dist/app.js` alone is insufficient. `npm ci --ignore-scripts --no-audit --no-fund` and `npm run build` prepare the assets.

Firefox is needed only for the optional actual-browser smoke test. PDF extraction needs Poppler (`pdftotext`) only when PDF preparation is used.

## Optional real engineering reproduction

These large dependencies are intentionally not committed, automatically installed, or needed merely to start the UI. The recorded campaign used:

| Capability | Recorded tool identity |
| --- | --- |
| Sireum / HAMR system properties | 4.20260810.80aad0c2; compatible initialized libraries; CVC5 selected |
| Java | JDK 25.0.3+11 |
| Codex worker | Selected 0.155.1 binary and companion sandbox resources; recipient supplies model access |
| Rust | 1.92.0, rust-src and required targets |
| Verus | 0.2026.01.23.1650a05 |
| Microkit SDK | 1.4.1 with compatible cross-build tools and QEMU |
| Existing worker image | `jasonbelt/microkit_provers@sha256:bab407fd7f4aac24d7bee1234cd6bab9b6a29df380c2f0491af8e3ed1888a405` |

Reference projects: <https://github.com/sireum/kekinian>, <https://hamr.sireum.org/hamr-doc/>, <https://github.com/verus-lang/verus>, <https://github.com/seL4/microkit>, <https://github.com/openai/codex/releases/tag/rust-v0.155.1>. These links identify upstream sources; the clean application build does not test availability or compatibility of every external engineering dependency.

Reuse compatible tools and verify their identities; do not assume a newer release is equivalent. A selected engineering profile must provide actual local project inputs, the existing Sireum path and its expected SHA-256. All model inputs must be explicitly allowlisted. The current worker also pins expected Codex and bubblewrap resources; a generic executable in PATH is not automatically compatible.

The public default toolchain deliberately has null Sireum fields. Copy a historical template to a local ignored file, supply your own authorized paths/identities, and pass it with `--profile`. Templates under `workbench/profiles/historical/` are not loaded by default and are not turnkey portable demos. `run_*` engineering scripts retain their original campaign/workspace assumptions; the `test_*` suite and browser smoke are the portable application checks.

To reproduce the original Isolette/Producer-Consumer engineering campaign, obtain a separately reviewed artifact bundle with models, libraries, exact source manifests, proofs and approved assumptions. To resume the original learning campaign, additionally restore a consistent private state export and verify relocated evidence and budget identities. Neither is bundled or claimed by this source checkpoint.

## Dependency provenance

Project license: root LICENSE. Vendored support helper origins/hashes are in `workbench/inspecta_scp/vendor/PROVENANCE.json`; their handoff sources are not runtime dependencies. Third-party npm/Python distributions retain their own licenses. The rulebook export excludes raw extraction prompts, model transcripts and training-document passages, and references the original private provenance snapshot by hash.
