# English-first validation and interactive repair

Upload `.txt`/`.md` English in Learning → Validate & refine, or select an already
reviewed preparation. Uploads are saved to Prepare English for exact review.
PDFs use the existing materials ingestion. Missing English is prepared from the
selected source before training; derived English remains reconstruction evidence.

Generation receives the reviewed English, selected sanitized rule candidates,
permitted shared files, and the approved Markdown engineering guides from that
training plan. For the approved demonstration plan these are KSU CODEX.md and all
eight guides. Linked material and held-out golden models are excluded. The controller
runs the declared engineering gates; guidance cannot turn an unsupported stage into
a pass. KSU remains the workflow; Miller supplies requirements-writing style.

`learning validate --task ID --campaign ID --auto-repair` and the UI share
`Development.validate_cycle`. It runs initial generation then at most three repair
attempts. Each attempt records a distinct context, model usage and actual checks.
Failures produce a report with failed gates, diagnostic categories, selected rule
IDs, repair gates, and Astra's reported applications. Keyword matching ranks the
selected rules for review; it is not semantic retrieval or proof of applicability.
Astra must check prerequisites/exclusions and preserve requirements. Golden graph
witnesses, scores and reference sources do not enter repair prompts.

After three attempts, execution returns HUMAN_GUIDANCE_REQUIRED. Inspect the result
and enter a suggestion in the UI, then choose “Save suggestion and authorize up to
3 more repairs”. CLI parity:

```
./inspecta-scp learning repair-guidance --result ID --expected-attempts 3 \
  --reviewer 'Your name' --suggestion 'Your scoped repair suggestion'
```

This is an explicit continuation, not a reset: total run/issue limits, campaign
usage/deadline, split, English requirements and release approvals remain enforced.
Task revisions retain their ancestor repair counts. A spent total allowance still
blocks continuation. Tool/budget/model failures can stop earlier. The existing
failure-learning and rule-refinement controls produce reviewable drafts, not
published rules. A requirement change still needs an exact new task review.

Acceptance remains separate: syntax/type → directed architecture → requirement and
contract fidelity → implementation/proof/testing. Current adapters do not establish
full behavioral equivalence or complete system acceptance. Missing gates remain open.

An explicit task amendment may add source-linked English and select rules extracted
from identical approved training with context contained in the new approved plan.
It records the reason, originating plans and predecessor. English/task review is
required; prior repair counts and caps remain unchanged. The proposed Isolette test
is visible in Validate & refine and becomes preparable after English review.

Rust/Verus/Microkit execution on this Ubuntu20.04 host uses the existing pinned KSU
container (see reports/build/rust-verus-environment.json), because the compatible
Verus binary requires newer glibc. tools-env.sh selects the isolated host Rust
installation but does not solve that glibc limitation. Use the saved container
replay scripts for actual component proofs/builds; do not replace the host libc.

## Approved structural profiles

During Data preparation, distinguish behavioral English from deployment choices
reconstructed from an approved training example. For the current Isolette review,
the user selected one Thread per Process: the Regulator System contains four
Processes, each wrapping one behavioral Thread. This is a scoped design choice,
not a universal AADL rule. Golden consultation makes this supervised development;
it cannot be reported as untouched transfer evaluation.

The validation evidence panel now shows a per-root structural profile from resolved
Sireum AIR: component counts, direct Thread ownership, profile violations and GUMBO
owners. It also shows a lexical declaration outline as an advisory style observation.
A Process-wrapper omission is a structural failure; declaration reordering alone
is not a semantic failure. The absence of GUMBO in an example does not justify
omitting an English requirement. Structural and behavioral acceptance stay separate.

The directed graph checker uses joint directed-neighborhood refinement and iterative
bounded bijection search. A PASS still requires an independent final comparison of
all typed vertices and all directed edges, including multiplicity. Names and source
order are not compared. Search exhaustion remains UNKNOWN. Payload equivalence,
GUMBO semantics, implementation, proof and timing require their own checks.

Supervised mechanical experiments appear separately in the UI. They preserve their
parent generated run, source patch, actual engineering run, graph witness and scope.
They are not recorded as fresh model generation or independent rule validation.
The current experiment preserves all four generated GUMBO blocks byte-for-byte.

Generation prompts retain the complete reviewed English, selected rules, approved
KSU documents, shared syntax context and previous generated file. If needed, only
redundant optional generated-AIR diagnostics are omitted, with an explicit omission
count. Oversized mandatory context fails before a model reservation. Generation
can use up to 600 seconds but reserves at least 120 seconds of the remaining campaign
window for engineering checks. Neither the aggregate nor continuation allowance is
reset by retries or task amendments.

## Referenced context and tool capability review

Data preparation can supplement a selected English revision with exact passages
from its approved context selection. UI: Data preparation -> Prepared English
-> Add referenced assumptions, tables or definitions. Read the numbered source,
select a passage and explain the dependency. The resulting revision needs review;
the original approval remains intact. Diagram transcriptions can be added with
page/figure provenance through the existing English editor and reviewed likewise.
This is an explicit source-selection operation, not automatic dependency discovery.

The CLI uses the same controller operation:

```
inspecta-scp learning supplement-context --preparation PREPARATION_ID \
  --passages passages.json --rationale "Restore the referenced boundary assumptions"
```

`passages.json` is an array of objects with `context_id`, `start`, and `end`.
Only exact, current, approved context passages are accepted. No model call is needed.
Tests cover preserved prior approvals, new review, unselected-context rejection,
source provenance, edits and CLI/controller result identity; Firefox exercises the UI.

For behavioral review, distinguish source omission, ambiguous interpretation,
missing formalization, unsupported installed-tool features and physical deployment
limitations. A golden example's missing clause does not waive an English obligation.
The current Isolette review records pinned-tool probes, a pending diagram/context
revision and17 manually transcribed solver queries in
`reports/demo/behavior-review/REVIEW.md`. These probes and queries are not full
GUMBO translation, implementation or end-to-end timing proofs. No system acceptance
is inferred from parser acceptance or from matching a golden architecture.

## Version-scoped capability review

Select prepared English and an executed capability check in the UI's capability panel. Classify each proposed exception, document exact source excerpts, alternative encodings and a revisit condition, then review/approve the scope. Development validation can select this scope. Only current approved tool-version deferrals affect the scoped target list; the original total and deferred items remain visible and receive no passing credit. No requirement is automatically deferred by a failing gate. Tool upgrades invalidate exclusions. See `reports/demo/tool-upgrade/REPORT.md` for the tested upgrade and limitations.

Integration profiles may explicitly select `integration_solver: cvc5` or `z3`; `auto` preserves tool defaults. The tested numbered Sireum upgrade uses CVC5 for SAT and validity because its bundled Z3 is incompatible with the host glibc.

The default tool is selected by `workbench/default-toolchain.json`; standard profiles use the upgraded system-property-capable version. `OUT_OF_SCOPE_REFERENCE` is a separate reviewed qualification exclusion for missing golden coverage. It does not assert tool incapability. The scoped denominator excludes approved unsupported-tool and reference-coverage targets, while both counts and the original total remain visible. See `reports/demo/tool-upgrade/QUALIFICATION_SCOPE.md`; publication still requires applicable executed checks and independent rule-validation evidence.

## Human acceptance of checked behavior

Development evidence offers **Prepare golden-scope behavior review**. The separate acceptance panel binds the generated/reference runs, directed graph assessment, applicable executed checks and exact approved requirement exclusions. All checks must pass before **Accept checked behavior for this golden scope** is enabled. Missing or stale checks remain blockers; a human decision cannot manufacture proof. `ACCEPTED_GOLDEN_SCOPE` accepts this model only, not full PDF coverage or a reusable rule release. Rule-transfer validation is not a prerequisite for this model-specific decision.

Transfer progress is separate from model-specific human acceptance. Only named examples with current acceptance and matching completed rule-transfer review expand the reported transferred scope. Uncovered PDF requirements remain attached. Historical Logika/Verus proof disclosures state their target, obligation scope and source report; they do not silently satisfy another model's acceptance gate. NOT_RUN refers to the selected run/obligation, not the global tool history.


## Partial success and scoped rulebook approval

In Learning or Knowledge, open **Partial success and scoped rulebook approval**.
Declare an exact scope from a recorded development result with its supplied candidate
rule revisions and selected check gates. Eligible scopes are selected initially;
you can deselect any of them. Enter a review comment, review the exact selection,
and enter a reviewer name to approve all displayed scopes.

The decision is `ACCEPTED_CURRENT_SCOPE`: the supplied bundle is accepted for the
named example and selected checks only. It does not demonstrate causal use of every
rule, publish a release, complete transfer, or establish whole-system acceptance.
A missing mandatory selected check blocks approval. Other checks remain visible.
Approval binds immutable evidence and rechecks freshness at confirmation; changes
require a new review. Approval can be revoked through the existing approval service.

Scores count selected checks, not proof subgoals or English requirements. Without
mapped requirement evidence, requirement coverage is unknown. Approved current
capability inventories distinguish tool limitations and exclusions from golden
scope; neither receives pass credit. Missing golden coverage alone is not evidence
of a tool limitation. Reports preserve reasons, assumptions, and next actions.
The suggested Isolette invalid-range consumption check is NOT_VERIFIED, not a
claimed failure or unsupported feature.

CLI equivalents under `learning`: `rulebook-scope --result ID --title TITLE --gates
GATE ...`, `rulebook-scopes`, and `rulebook-bulk-review --scopes ID ... --comment
TEXT`. Confirm the returned approval using the existing approval command. UI and
CLI use the same backend validation. Download the partial validation JSON report
from the panel for exact rule revisions, scope scores, pending checks, and history.


## Evidence decisions and formal rulebook qualification

The first panel in Learning, **Rulebook evidence and decisions**, suggests a review
from a selected result's declared run and rule gates and always requires formal
verification. This is a deterministic controller suggestion, not a paid model call.
Choose human-reviewed partial scope or all declared checks required. Existing narrow
parser/export check-scope approvals are retained and explicitly distinguished from
formal rulebook qualification.

Every category retains its original status and evidence. Counts use their actual
units: gate verdicts, connection claims, mapped formal obligations, Verus units,
or test cases. There is no combined correctness percentage. Missing requirement
mapping never becomes verified-English coverage. The display includes parse/type,
architecture export and comparison, HAMR, integration, formal checks, builds,
requirement mapping/tests, Verus, GUMBOX, R2U2 and QEMU. Unconnected adapters say
NOT_CONFIGURED or NOT_RUN. Historical graph and component proof reports remain
visible separately and cannot qualify another model merely because they passed.

For unresolved required targets, keep required, propose an exclusion, or open
AI-assisted repair. Exclusions require a classification, evidence/reason, and
revisit condition. Approve, edit and approve, reject, or revoke beside the target.
Labels distinguish HUMAN_APPROVED_EXCLUSION_TOOL_LIMITATION,
HUMAN_APPROVED_EXCLUSION_GOLDEN_COVERAGE and HUMAN_APPROVED_DEFERRAL. A user's
classification records their reviewed decision; it does not automatically prove
that a tool can never express a property. Original failures remain visible.

The entire formal gate cannot be excluded. Partial formal acceptance requires
adapter-produced mapped obligations: unique id, requirement, contract and status
(PASS/FAIL/UNKNOWN/NOT_RUN) under the evidence object's mapped_obligations field.
No browser endpoint may upload success counts. All included obligations must pass,
and at least one formal obligation (or a complete passing formal gate) must remain.
Current general run adapters do not yet provide every formal/code/test mapping;
those missing results remain blockers rather than inferred from historical notes.

Accept reviewed scope saves ACCEPTED_DECLARED_SCOPE or
ACCEPTED_HUMAN_REVIEWED_PARTIAL_SCOPE only after those checks. Every included
mandatory target must pass. Saving candidate notes does not require acceptance.
Approval/revocation records and exact rule revisions are retained. Tool, source,
evidence and exclusion changes invalidate affected approvals. Transfer and User-mode
publication are separate; this feature does not bypass their gates.

AI-assisted repair first shows the existing diagnostic/meta-rule report. Running
one attempt uses the existing Development controller's approvals, time/token limits,
shared attempt counter and human checkpoint. It follows the task's configured KSU
workflow. It rechecks configured gates, not unimplemented adapters. It creates a
new result for human inspection; no old exclusion or acceptance moves to it.
Requirement/assumption amendments still require the existing reviewed task flow.

R2U2/QEMU reporting is prepared for future trusted adapters, not a new executable
integration. An anomaly-free observation requires an active monitor, completed
positive observation window, clock (simulated/wall), scenario and anomaly count.
Exit zero alone supplies no anomaly-free claim and no universal proof.

CLI parity: learning evidence-review --result ID --policy partial|all --note TEXT;
evidence-reviews; evidence-exclude --review ID --target TARGET --reason-code
TOOL_LIMITATION|GOLDEN_COVERAGE|DEFERRAL --reason TEXT --revisit TEXT;
evidence-accept --review ID; evidence-note --review ID --text TEXT --reviewer NAME;
evidence-repair --review ID --target TARGET [--campaign ID]. Approval uses the
existing approval command with its exact returned subject digest. The browser and
CLI share the same controller enforcement. Download evidence, scores and decisions
preserves the complete current report for review.


## Simple KSU verification review

Learning now starts with a compact project review: the verification categories are
grouped using the local KSU HAMR overview and testing guide (model/contracts,
code generation, implementation/Verus, component tests, integration/observation).
This is a view of verification evidence, not a new claim that all adapters execute.
Details, setup and legacy approvals are collapsed. The reviewer enters a name once;
unfinished required targets have checkboxes and the action bar stays visible.

Select unfinished targets and Approve selected exclusions, Edit selected then
approve, or Defer selected. Recorded diagnostic reasons and a revisit condition
are prefilled; typing is optional. Defaults say human deferral from the current
scope, not a proved tool limitation. Deferring a decision is a separate operation
that leaves checks required. If the entire remaining selection can be excluded
while passing nonempty formal evidence remains, the action becomes Exclude selected
& accept partial. The controller commits all selected decisions atomically and
rejects a stale fingerprint or invalid target without partial approval. Undo
exclusions/acceptance is available alongside the saved decisions.

The semantic-similarity panel is a separate post-architecture criterion. New scope
suggestions require its policy; historical scope records are retained. Choose a
maximum cosine distance before applying the gate (0.1/0.2/0.3 choices in UI; CLI
supports [0,0.3]). Applying the threshold executes the existing offline graph and
contract-feature comparison, creates a new exact review, and selects it in the UI.
No paid model call is needed. Threshold application is an explicit human action;
retrieval epsilon is never reused implicitly. Parsed contract-feature cosine is
not semantic embeddings or formal equivalence. Empty contracts, failed graph
comparison, changed checker/source/tool identities cannot clear this gate.

Progress refreshes every 15 seconds while the page is visible, and after decisions
or repair results. A successful bounded repair creates a new review for its new
model and switches the UI to it, preserving previous decisions as history.
Semantic thresholds and exclusions must be reviewed for the new model.

CLI: learning evidence-quick --review ID --targets TARGET ... --action exclude|defer
--reviewer NAME --fingerprint DIGEST [--accept] [--edits JSON_FILE];
evidence-semantic --review ID --max-distance NUMBER --reviewer NAME.

Human authorization: start semantic comparison at cosine distance 0.1; never exceed 0.3. The backend enforces the ceiling for both UI and CLI. This is independent of retrieval epsilon and does not waive formal verification.

Prepared exact scope exclusions appear as review cards in the main KSU gate view,
with approve, edit-and-approve and reject actions. A golden-coverage exclusion
records missing reference behavior rather than claiming a tool limitation.
Until the human approves, the target remains required. Existing formal contracts
remain checked. The full evidence view retains history and revocation controls.

Generated system proofs have their own artifact-bound result panel. Dependency
proof totals and compilation errors are distinct from system verification-condition
counts. A proof on an experimental model does not supply acceptance evidence for
a different current candidate, and component proofs do not close open system VCs.
