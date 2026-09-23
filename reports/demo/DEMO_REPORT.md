# Live demonstration: executed, validation incomplete

## Data preparation and KSU-based evolution: executed checkpoint

The implemented UI/CLI now has an explicit Data preparation stage before new rule
learning. It supports existing English, exact excerpts of approved English documents,
and Astra extraction when English is absent. Large models use resumable100-line
obligation windows; successful batches are retained. Prepared English is bound to
its data role, source revision and subsequent learning/validation task. Source claims
and golden models are excluded from formalization context; the reviewed English is
passed as selected. Model interpretations remain drafts pending review.

KSU remains the engineering workflow. Miller/FAA supplies English presentation style
and, where applicable, actual existing Isolette requirements. It does not override
KSU workflow execution. The original FAA Monitor and Regulator sections were prepared
unchanged, with exact source ranges and inherited source authorization. This is
source reuse, not new semantic validation. Model-derived Isolette descriptions are
supplements and cannot replace omitted FAA obligations.

Executed preparation:

- First full Monitor extraction:300-second timeout; no usable response or usage
  totals. Charged the previously authorized1M estimated debit, separately from usage.
- Monitor retry: five successful bounded batches,133 draft source-linked requirements,
  101134 measured tokens and452.604 seconds across successful batches.
- Regulator extraction:88 draft source-linked requirements,25836 measured tokens,
  290.518 seconds. Retained as a model-derived supplement to existing FAA English.
- Producer/Consumer extraction:32 draft source-linked requirements,15169 measured
  tokens,106.160 seconds; source-derived reconstruction data, not independent English.
- New actual rule-learning call: prepared FAA Monitor English + original Monitor +
  all nine approved KSU guides;46158 measured tokens and116.847 seconds. Produced
  draft **RA-001** on requirement allocation, assumption/guarantee composition, trace
  preservation and requirement-preserving repair. It has not passed development gates.

The maintained learned book now contains20 candidates. Existing books and prior
results are preserved. This stage does not publish a release or establish accepted
system cost improvement. New preparation interpretations and validation configurations
must be reviewed before claiming a new formalization result.

Validation of implementation:128 application tests and21 real Firefox checks passed.
Browser checks use synthetic inputs, separately labeled from the real Astra calls.

Current charged campaign usage:1182675 measured +4000000 estimated =5182675 tokens.
The14M aggregate cap leaves8817325; the3M continuation sublimit leaves1811703.
No new token or time authorization is implied. See `CAMPAIGN_STATUS.json` for the
clock snapshot, and `data-preparation-evidence/` for saved call records.

Prepared documents: `prepared-faa-english-monitor.md`, `prepared-faa-english-regulator.md`,
`prepared-english-monitor-batched.md`, `prepared-english-regulator.md`, and
`prepared-english-producer-consumer.md`. Learning receipt:
`learning-from-prepared-english.json`. Operator instructions:
`../../workbench/DATA_PREPARATION.md`.

## Continuation authorization and scheduling clarification

The user authorized up to 3M additional charged tokens within the unchanged 14M
aggregate cap and 45 more minutes. See `CONTINUATION_3M_45_MINUTES.json`.
The controller enforces the additional sublimit and preserves earlier consumption.

A follow-up compatibility audit found that the selected KSU example's saved
`microkit.schedule.xml` allocates 10+50+10+50=120, whereas the reused current
generator defaults allocate 30+50+30+50=160. These are scheduling allocations,
not AI tokens or measured execution times. The failure does not demonstrate
that the system requirements are infeasible. See `KSU_SCHEDULE_COMPATIBILITY_FINDING.json`.
No schedule was copied into generation/training, no original was modified, and no
compatibility repair or schedulability proof is claimed.

## New graph assessment supersedes the architectural interpretation of exact diffs

The user requested name-independent directed graph equivalence. Implemented and
executed a new evaluator on the saved live HAMR captures; no extra model calls.

- **Producer/Consumer graph: PASS**, 15 vertices and 32 directed edges on each side,
  with a stored bijection preserving containment, port directions, wiring, bindings
  and supported properties. Its historical 41 exact syntax/declaration differences
  are **not** 41 architectural defects.
- **Isolette graph: FAIL**, 1162 versus 935 vertices and 3164 versus 2534 directed
  edges across the exported instance graphs. Names/order alone do not explain this.
- After graph PASS, Producer/Consumer parsed assume/guarantee feature cosine is
  approximately **0.9752** (three obligations per side). This is advisory, not semantic
  embeddings or behavior proof. Isolette post-graph similarity was not run.

See `producer-consumer-graph-assessment.json`, `isolette-graph-assessment.json`,
`producer-consumer-directed-graphs.svg`, and `../../workbench/GRAPH_EQUIVALENCE.md`.
The original results below remain unchanged as historical evidence. Structural
projection success does not establish payload types, requirement fidelity, helper
semantics, implementation, proofs, tests, or whole-system acceptance.

The additional 1M-token allowance and 45-minute extension are recorded in
`TOKEN_EXTENSION.json` and `TIME_EXTENSION_45_MINUTES.json`. Current cumulative
usage: **994,378 measured tokens + 3,000,000 estimated debits = 3,994,378 charged**,
leaving **10,005,622** within the 14M ceiling. No consumption was reset.

All four focused extractions completed. The exact KSU context revision was approved
and used in two further calls: generalized workflow learning and specialization
from the actual Microkit timing failure. These two calls used **91,248 measured
tokens**, **231.394 seconds** total, and no new estimated debit. The Microkit tool
attempt itself took **16.919 seconds**, zero model tokens; parse PASS, generation FAIL
(frame 120, used budget 160). See `KSU_MICROKIT_ATTEMPT.json`,
`ksu-workflow-generalize.json` and `ksu-workflow-specialize.json`.

There are **19 maintained draft candidates** in the versioned learned book; see
`LEARNED_BOOK_EXPORT.json` and `.scp-workbench/app/learned-rulebooks/INDEX.md`
(repository relative). UI controls expose workflow failure learning and the approved
context selections. The latest approved split opens by default. These drafts are
not published or validated transfer knowledge. No unsupported timing changes were
applied; successful repair and cost reduction remain unestablished.
See `../../workbench/KSU_WORKFLOWS.md` for source scope, stage mapping and limitations.

## Earlier checkpoint (before graph comparison and the additional token grant)


The user approved the isolated Isolette compatibility reference: 148 port-direction
edits across seven copied files. Original Isolette files, original Monitor training,
DASC artifacts, and existing rulebooks remain unchanged. The new development
validation assignment is recorded in `APPROVED_MIGRATED_VALIDATION_SPLIT.json`.
Earlier reference failures remain historical evidence and are not relabeled as passes.

## Latest executed results

| Target | Real executed gates | Exact golden comparison | Acceptance |
|---|---|---|---|
| Isolette Regulator | Parse/type PASS; architecture capture PASS | 844 differences | NOT_VALIDATED |
| KSU Producer/Consumer | Parse/type PASS; Slang/JVM generation PASS; connection integration constraints PASS; architecture capture PASS | 41 differences | NOT_VALIDATED |

See `isolette-refined-rule-validation.json` and
`producer-consumer-refined-rule-validation.json`. These contain run/config identities,
actual gate evidence, generated source, evaluator-only golden source, and differences.
Generation is not compilation or implementation verification. Connection proofs do
not establish whole-system behavior. Exact comparison includes resolved declarations
and contract syntax; a difference count is not a count of independently proven defects.
Producer/Consumer's remaining differences require contract/declaration analysis;
Isolette also differs in architectural organization. No equivalence is inferred.

## Learning and actual self-evolution

All 12 FAA guidebook context batches completed with approved Monitor training and
Regulator held out. They produced overlapping draft rules, not 12 distinct validated
principles. The actual failed Isolette generation informed a new Astra rule revision
(`actual-failure-rule-refinement-2.json`). That recorded revision was then reapplied
to both approved English tasks in new workspaces. Prior failures and repair counts
were retained. Golden files and comparison witnesses were excluded from model inputs.
Producer/Consumer's refined-rule repair removed duplicated scheduling properties;
its Monitor-specific behavioral rule was reported as inapplicable. This is not
controlled evidence of learning benefit or independent final transfer.

An Isolette retry was blocked before a model call because optional generated-model
architecture diagnostics exceeded the prompt bound. The optional inventory is now
bounded with explicit omission counts; no requirement, contract, or reference was
weakened. The subsequent paid call and real checks executed successfully as calls,
but validation still failed as shown above.

## Budget and remaining blockers

The campaign retains the original 13,000,000-token best-effort ceiling and start time,
plus the explicitly approved 60-minute extension (7,200 seconds total). Latest usage:
811,482 measured tokens plus 3,000,000 authorized estimated debits; 9,188,518 tokens
remain with no outstanding reservation. Estimates are not measured usage or billing.
See `CAMPAIGN_STATUS.json` for its timestamp-relative wall-clock snapshot and
`AUTHORIZATION.json`, `FAILURE_ACCOUNTING_POLICY.json`, and `TIME_EXTENSION.json`.
No automatic deadline or token renewal is authorized.

Producer/Consumer has reached its configured eight-repair allowance. A new task or
rule revision does not reset that lineage. Further blind repairs are not a substitute
for the missing acceptance work. The following remain incomplete:

- Golden conformance and independent requirement/contract fidelity.
- A populated, reviewed requirement-unit inventory and assumption-discharge adapter.
- Required full implementation, proof, build, and independent test acceptance.
- Supporting/contrasting rule validation, reviewed publication, and a fresh frozen
  User application cycle. No release approval has been requested for an unvalidated draft.
- Controlled cost-benefit/final-transfer evidence and an acceptance attestation.

M07 remains incomplete. No mock run replaces these real results; no acceptance gate
was weakened. Verification coverage remains undefined without a reviewed registry.

## UI and replay

See `../../workbench/LEARNING_WORKFLOW.md`. The UI now restores the approved split,
shows cosine-distance epsilon (default 0.1, maximum 0.3; lexical token-count vectors),
supports context repositories/uploads, resumable batch extraction, campaign pause/resume,
editable unit definitions, exact development-task review, and refined-rule test preparation.
Evidence inspection displays generated SysML, the golden reference, actual gate status,
and differences. SHA-256 fingerprints identify exact revisions; they are not passwords.

Read-only replay of the recorded checks uses `learning inspect-validation`; it does
not launch a model. Tool records and events are exported under `live-evidence/`;
latest metric exports are in both `*-refined-rule-validation-metrics/` directories.
Full local snapshots remain in `.scp-workbench/app`. Browser/support tests are
explicitly separate from live engineering evidence.

## Historical checkpoint before authorization

The following records describe the earlier deferred state, not current consent.

No live model-driven Isolette learning -> release review -> fresh User cycle or
additional KSU learning/application demonstration has been run. No synthetic demo
has been substituted. Demo model calls: 0; model tokens: 0; actual billing: unknown
for this implementation session and not inferred from token prices.

Completed engineering preparation is recorded separately in reports/build:
real Isolette and Producer/Consumer type-check smoke commands, Isolette codegen
and Logika invocations, and three isolated application-worker integration checks.
The Logika invocations did not establish discharged obligations. These are not
live learning, behavior verification, whole-system acceptance, or transfer evidence.

The user explicitly deferred paid demonstrations and instructed implementation to continue.
No paid-demo approval is currently requested. M07 remains incomplete.

Additional executed offline preparation (not a live demonstration):

- The controller generated real Slang/JVM artifacts and verified a nonempty
  Producer/Consumer connection constraint with per-connection solver feedback.
  A deliberately incompatible receiver contract was rejected; removing receiver
  obligations produced BLOCKED rather than a vacuous proof claim. See
  `reports/build/real-engineering-integration.json`. Original sources were preserved.

- Seven real Producer/Consumer structural checks exercised unchanged models,
  wiring/contract failures and exact reviewed consistent renaming. See
  `reports/build/real-structure-integration.json`.
- A real bounded repair branch rejected a broken connection and checked its
  corrected child while preserving the original source and run result. See
  `reports/build/real-repair-integration.json`.
- The KSU Simple Isolette source emitted 12 port-direction warnings with both
  the reused March Sireum and a separate digest-checked August reference CLI.
  A disposable candidate moved direction annotations onto the 12 typed features;
  the reused March tool then passed type checking and architecture capture.
  This syntax migration remains provisional and unapproved, with no source
  promotion or behavioral-equivalence claim. See
  `reports/build/ksu-isolette-migration.json` for exact diffs and evidence.
- Offline metrics generated CSV/JSON and 18 plot files. A separate verifier
  validated a real DSSE signature made with an ephemeral test-only key, returning
  INCOMPLETE (exit 3) because engineering acceptance was not established.
  See `reports/build/real-reporting-integration.json`. No production trust setup
  or verified-unit denominator was inferred.

Prerequisites only if the user later resumes M07:
1. Complete the missing M01/M02-M06 application and engineering capabilities.
2. Establish a reviewed requirement/unit registry and compatible Isolette proof,
   build and independent test profile; resolve reported instantiation warnings.
3. Obtain bounded aggregate live-demo authorization. Strict Codex CLI token-cap
   capability is not validated. Best-effort execution needs explicit consent.
4. Validate live access to gpt-6-astra; cached model metadata and authenticated
   login are inventory evidence only.
5. Review the learned release before publication/application. No release is approved.

There is deliberately no fabricated live-demo recovery command: the live-demo
adapter is not implemented yet. Implement it before documenting an executable
M07 command. Available real preparation commands in this checkout are:

```sh
./inspecta-scp onboard
./inspecta-scp --json doctor
./inspecta-scp --json check --offline --config workbench/profiles/producer-consumer.check.json
```

The worker needs Linux namespace permissions. Run the check from the normal user
terminal if the outer Codex sandbox denies nested namespace creation; retain the
Workbench sandbox. Never enable an unsandboxed fallback.
