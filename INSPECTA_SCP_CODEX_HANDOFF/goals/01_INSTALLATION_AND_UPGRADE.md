# Goal 01 — Reuse-first compatible installation and controlled upgrade
## Outcome
A working profile using suitable existing tools first, preserved user-selected Codex v_155 and Sireum, only missing dependencies installed, and reproducible lock files.

## Actions
1. Read the current Loonwerks `provers-env/readme.md`, `docker/readme.md`, `bin/versions.sh`, installer scripts, and chosen KSU example scripts. Inspect host OS/architecture/resources, restrictions, installed tools, model authentication, and existing checkouts. Confirm suspected repository defects before patching.
2. Prefer user-local Workbench/Codex installation and versioned engineering workers. On Apple Silicon inspect the native path; on unsupported/locked-down hosts use an approved VM/backend. No assumption that the current machine is x86 Linux.
3. Honor `selected_tools` in the build request and the child environment CODEX_BIN/SIREUM_BIN/SIREUM_HOME. Use the downloaded Codex v_155 / 0.155.* binary after CLI checks, with no npm reinstall. Reuse current Sireum when its selected KSU profile passes. Resolve a new official release only for an explicit approved update or missing tool. For an installer, download/inspect before execution, validate published checksums when available, retain receipt and final executable version. Do not trust a changing tag as an experiment identity. Do not invent the Astra ID.
4. Inspect locally available `jasonbelt/microkit_provers` images first; preserve a suitable image as reference after smoke-testing. Pull only when absent or explicitly refreshed. Record manifest/platform/digest. Do not treat it as the original DASC toolchain.
5. Adopt the compatible existing native/worker profile as current-validated. Fresh-build a side-by-side worker only when missing/incompatible or explicitly requested, from the shared recipe with deliberate compatible pins. Build only the current target architecture unless another is requested. Use Dockerfile/script changes, not undocumented `docker commit` state. Include required Logika solvers and selected Rust/JVM/model-library dependencies; warm caches during setup.
6. Install missing prerequisites from approved sources. The included bootstrap only helps prepare Codex/reference image; implement the full idempotent installer in the application. Never silently resize disks/LVM, replace unrelated global installations, disable TLS, expose tokens, prune shared caches, or push an image.
7. Run parser/codegen/proof/host tests and required deployment smoke tests. Repeat the selected engineering operations network-disabled. Save exact commands and real results. An unavailable check is blocked, not passed.
8. Lock all versions, dependencies, platform/backend, image digest, feature capabilities, model alias resolution, and relevant configurations. No updates during experiments.

## Separate trust zones
The controller owns worker launch. Codex/candidate programs do not get the Docker socket or signer keys. Candidate execution has no model credentials. The published development image's passwordless sudo and user setup are not a security boundary: harden launches/users/capabilities and test isolation.

## Upgrade protocol
Create a proposed new lock/image -> run regression suite against old and new -> report semantic/tool differences -> approve adoption -> preserve rollback. Run K0/K1/S1/S2 on the same adopted environment. Do not credit a tool upgrade to self-evolution.

## Completion
Host/source audit, installation receipt, actual executable identities, reference/current profiles, verified capability matrix, successful supported smoke tests, network-off scope, and recovery commands. Required unresolved tools prevent dependent milestones from passing.

Primary references: R01–R05, R08–R12 in sources/REFERENCES.md.

## Integrated v2.0 startup
Use the launcher for inventory and Codex dispatch; full Sireum/current-validated setup is M01 work, not something the support scripts claim completed. Discover existing -> honor user pins -> compatibility smoke tests -> install only missing approved pieces -> lock. Prefer shared Loonwerks recipes; reference/current-validated containers or native backend as appropriate. Missing packages should be installed in a reviewed user-local/container scope; never unrestricted host changes or blind remote scripts. Authentication or privileges may require a human pause. Do not downgrade a current tool silently to make examples pass.

## Required reuse tests

Existing standalone Codex with no npm must start without an installation. A renamed binary outside PATH must work via an explicit path. Broken/incorrect-version selection must block, not reinstall. Existing SIREUM_HOME must remain unchanged; an unbuilt checkout must not bootstrap during inventory. A missing solver must trigger only targeted preparation. Existing local reference images must not pull unless refreshed. Use the local helper tests and real M01 profile evidence separately.

Read [REUSE_EXISTING_TOOLS.md](../installation/REUSE_EXISTING_TOOLS.md).
