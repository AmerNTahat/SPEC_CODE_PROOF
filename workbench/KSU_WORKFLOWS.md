# KSU/HAMR workflows and evolving rulebooks

The Workbench currently reuses selected KSU/HAMR stages. It does not yet implement
or demonstrate the entire system-building workflow requested in the master goal.

| Material / executable stage | Location | Current scope |
|---|---|---|
| Existing KSU example and modeling guidance checkout | `../HAMR-agent-configuration-experiments/hamr-claude-training` relative to `workbench/` | Existing source material; importing a document does not prove a rule |
| Saved project/tool/gate selection | `profiles/*.json` | Isolette, Producer/Consumer and simple Isolette configurations |
| Deterministic execution and stage selection | `inspecta_scp/controller.py` | Credential-free bounded checks and preserved run snapshots |
| Parsing and instantiated architecture export | `inspecta_scp/architecture.py`, `controller.py` | Actual reused Sireum/HAMR CLI |
| HAMR generation and Logika integration constraints | `inspecta_scp/engineering.py` | Slang/JVM and Rust/Microkit generation adapters; nonempty connection proofs; not whole-program acceptance |
| Model-driven learning/generation/repair | `inspecta_scp/learning.py`, `development.py` | Reviewed split, hidden golden, actual failed-tool feedback, shared campaign |
| Directed architecture equivalence | `inspecta_scp/graph_equivalence.py` | One name-independent typed mapping; containment, ports, wiring, bindings and supported properties |
| Tool identities and earlier setup checks | `../reports/build/toolchain.lock.json` | Existing Codex 0.155.1 and Sireum reused; no reinstall for the new checker |

The exact context revision is approved in
`reports/demo/APPROVED_KSU_WORKFLOW_TRAINING.json`: FAA context plus KSU `CODEX.md`
and all eight `doc/*.md` guides, original Monitor training, isolated approved
Regulator and Producer/Consumer held out. The nine KSU files are pinned by content
hash; local changes are preserved. Linked files, worked examples and logs are excluded.

The real Microkit attempt is `reports/demo/KSU_MICROKIT_ATTEMPT.json`: parsing
passed; generation failed with frame 120 versus used budget 160, in 16.919 seconds,
with zero model tokens. Astra then learned a generalized workflow rule and a
specialization from the nine approved KSU documents, Monitor, and generated-workspace
diagnostics. Both calls succeeded, totaling 91,248 measured tokens and 231.394 seconds.
The records are `ksu-workflow-generalize.json` and `ksu-workflow-specialize.json`.
Neither call received golden sources or architecture comparison witnesses.

Use **Learning → Learn from workflow failures** to select an approved split, exact
context documents, generated result, failed tool attempt, and generalize/specialize.
Specialization requires a prior draft from that plan. CLI parity is
`inspecta-scp learning learn-workflow-failure --help`. Both clients use the same
service, source freshness checks, campaign budget and immutable book export.

The learned strategy requires reconciling scheduling allocations and overhead,
preserving required timing, and stopping if justified execution bounds are missing.
The current generated model has no execution-time bounds. Reused scheduler source
uses a default 50 per thread and 30 pacer overhead per slot (two of each gives 160).
Those defaults are tool accounting, not measured WCET. No frame inflation or invented
WCET was applied. Successful repair, Rust compilation, Verus, component/runtime tests,
and accepted-system cost improvement remain unestablished. This stage-level attempt
is not a complete paired static-KSU versus evolved-workflow benchmark.

New learned candidates are maintained separately from original rulebooks:

- Authoritative immutable records and provenance: `.scp-workbench/app/workbench.sqlite3`
  relative to the repository root.
- Human-readable index: `.scp-workbench/app/learned-rulebooks/INDEX.md`.
- Immutable snapshots: `.scp-workbench/app/learned-rulebooks/<snapshot>/RULEBOOK.md`
  and `rulebook.json`. Successful extraction/refinement updates the index and retains
  earlier snapshots. The UI **Export versioned learned rulebook** refreshes this view.
- Actual extraction evidence: `reports/demo/learning-batch-*.json`; refinement:
  `reports/demo/actual-failure-rule-refinement-2.json`.

There were 19 draft candidates before explicit data preparation: the original 13, four focused extractions on
whole-system architecture, requirement allocation, engineering workflow and
implementation/proof/testing, plus the two KSU failure-learning candidates. The
focused calls are saved as `reports/demo/focused-*.json`. Coverage is not established
by counts: each rule still requires supporting and contrasting development cases.

Evolution remains: approved sources → draft principles → held-out generation →
real checks → failure-backed rule revision → repeat development checks → reviewed
publication. A published User release must remain frozen. Full implementation
proof, independent system tests, acceptance attestation, and the fresh frozen User
cycle remain incomplete; the selected real tool stages do not replace them.

Data preparation now precedes new learning. Existing FAA English is retained as
primary for Isolette; model-derived descriptions are supplements. The prepared
Monitor English/model pair and the nine KSU guides produced draft RA-001, bringing
the book to20 candidates. It requires source-to-role allocation, assumption/guarantee
composition, explicit gaps, and affected KSU rechecks after repairs. It is not yet
a validated rule or an accepted-system cost improvement. See DATA_PREPARATION.md
and reports/demo/learning-from-prepared-english.json (repository relative).

The 120 ms human-priority experiment now passes real parsing and Microkit generation.
See `reports/demo/KSU_HUMAN_TIMING_OVERRIDE_RANGE.json` and the emitted schedule.
The selected SysML instantiator requires the range expression
`attribute :>> Compute_Execution_Time = 0 [ms] .. 30 [ms];`; nested minimum/maximum
refinements parsed but did not populate AIR, so defaults remained in effect.
Two explicitly allocated 30 ms thread slots plus two existing 30 ms pacer slots
produce120 ms. This is a human-directed development allocation, not measured WCET
or an established solution to the original60/40 ms thread deadlines. Reference
models and reused tools are unchanged. Original graph evidence does not cover this
changed-property candidate; it needs approved-change/conformance validation.

The revised bounded interactive validation flow is documented in VALIDATION_PIPELINE.md.

### SDK cache identity repair, observed 2026-09-23

The reused KSU container includes two SDK versions. A build initially compiled C
objects against 2.1.0, whose image tool rejected the generated domain schedule.
Switching to the existing custom 1.4.1 SDK without rebuilding those objects produced
an image that booted but reported invalid notification channels61/59. Preserving
the mixed build directory and rebuilding C objects/images solely with 1.4.1 fixed
that runtime failure. No channel numbers, contracts, generated source or SDK files
were changed for this repair. Both Rust components repeatedly reached compute in a
bounded20-second QEMU run. This is runtime smoke evidence, not payload correctness,
WCET, periodic timing or whole-system acceptance.

Replay: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python workbench/tests/run_ksu_clean_image_runtime.py`.
This uses the existing pinned image, isolated generated workspace, offline Cargo
cache and recorded campaign deadline. It preserves the previous build directory.
Evidence: `reports/build/ksu-container-clean-sdk141-runtime.json`.
The generalizable SDK/cache lesson is queued for interactive Learning review in
`reports/demo/KSU_SDK_CACHE_REPAIR_LESSON.json`; no frozen User release changed.

The isolated Sireum4.20260810.80aad0c2 upgrade executes the official pinned KSU system-property tutorial through real Rust generation and Verus, including a false-postcondition negative control. See `reports/demo/tool-upgrade/REPORT.md`. This is capability evidence; the fixture is excluded from the approved training split and does not replace the required application demonstrations. Version-specific capability deferral is a maintained draft repair principle, not a rule release.
