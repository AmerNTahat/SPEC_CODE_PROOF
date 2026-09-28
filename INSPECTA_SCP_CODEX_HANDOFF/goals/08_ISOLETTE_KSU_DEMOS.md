# Goal 08 — Isolette and KSU demonstration workflows
## Source preparation
Inspect KSU's current build/verification, testing, modeling, tool-interface and change-report guides and each selected example's actual scripts. Pin them and adapt the procedures to Codex. Do not assume Claude-specific setup filenames change engineering semantics. Install missing profile dependencies using Goal 01.

## Demo A: Isolette
Use the preserved SCP profile and reviewed source obligations. Show Learning selection -> verbalized principle -> confidence -> development check failure -> bounded repair -> human review -> published rule release -> User application -> architecture and requirements evidence -> attestation verification. Show both assistance settings. Include a deliberately structure-breaking patch that is rejected.

## Demo B: KSU Producer/Consumer
Exercise event-data versus data-port applicability and supported Rust/Microkit procedures. Keep target profile separate from the original Slang/Logika setup. Do not claim cross-toolchain transfer from a simple tool configuration change.

## Demo C: KSU Simple Network Guard
Use manual unit, manual GumboX and randomized contract tests plus actual verification where configured. Capture initialization, state and boundary cases, test serial execution requirements, valid/rejected inputs, deterministic seeds, shrunken failing examples when supported, and all component results. A test failure does not stop collection of other component failures unless isolation demands it.

## Verification scope
Host component tests do not establish deployment correctness. Match generated-component profiles: some synthetic monitor components intentionally lack ordinary test/proof harnesses; derive obligations from trusted profile rather than assuming every crate behaves the same. Runtime monitoring remains a later feature unless required by the selected example.

## Public presentation
Recorded replay must be labeled recorded; fault injection synthetic; real outcomes measured. A setup demonstration and a training example are not automatically held-out tests. No generated positive metrics or confidence numbers inserted to make a demo look complete.

## Output
Reproduction commands, pinned project profiles, source/obligation manifest, actual artifacts, traceability, signed result scope, video/replay script, and cost accounting. If external source files are absent, locate them through the approved repos rather than inventing golden solutions.

## Mandatory end-of-build demo
Follow M07 in MILESTONES.md and demos/LIVE_DEMO_PROTOCOL.md. A recorded or synthetic preview is not a live demo substitute. Run actual bounded Isolette learning, approval, fresh User session and verification; include selected KSU workflow and task-aware continuation. Separately declare creation/rename capability tests. Produce DEMO_REPORT.md plus raw evidence, plots and a replay captured from that run. If blocked, keep the milestone incomplete and issue an exact recovery instruction.
