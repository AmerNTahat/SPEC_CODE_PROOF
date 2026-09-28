# Handoff status and continuation guide

Prepared for the proposed `workbench-v0.1-baseline` tag: the application and original handoff before UI scaling work. This is a development baseline, not a production release or rulebook acceptance. The private campaign archive is excluded and has not yet been prepared or restore-tested.

## Read this before the original handoff

The application already exists. Continue the shared Python controller, CLI/API and React UI rather than restarting implementation. Read the repository [README](../README.md), [dependency guide](DEPENDENCIES.md), [build verification](../reports/checkpoint/BUILD_VERIFICATION.md), and [historical engineering results](../reports/checkpoint/RESULTS.md) first.

The [original handoff](../INSPECTA_SCP_CODEX_HANDOFF/START_HERE.md) is preserved byte-for-byte, including its integrity manifest. Read its workflow contract, master goal, milestones, and both revised Learning/User goals for the original requirements. Its `archive/` is historical, not active instruction. UI previews and walkthrough images express design intent, not current screenshots or verification evidence.

Resolve handoff-document references relative to `INSPECTA_SCP_CODEX_HANDOFF/`. Resolve target application paths such as `workbench/`, `reports/`, and `.scp-workbench/` relative to the repository root. Historical profile templates contain placeholders and are not usable campaign restoration configurations.

For current build/start instructions and checkpoint completion, use this guide and the repository README. Original requirements remain applicable except where later owner-approved decisions refine them. A conflict is not permission to weaken a gate. Preserve existing code, rulebooks, DASC artifacts and local changes. Work in the current implementation session. Do not invoke `start.py start` to launch another session; the launcher is retained as original source history.

## What is implemented and checked

The checkpoint contains controller/CLI/API/UI code, learning/data preparation, rulebook and approval handling, architecture comparison, scoped evidence reporting, adapters, schemas and tests. These modules do not imply completion of every handoff milestone.

The preceding application export passed 209 unit tests, 35 Firefox checks, frontend build, clean dependency setup and actual empty-state CLI/UI startup. Those checks used the unchanged application code and do not constitute a new live engineering campaign. This handoff addition changes documentation and packaging only.

Historical Isolette and Producer/Consumer results and their limitations are reported separately in the linked results summary. Their detailed evidence and approvals remain local and are not restored by cloning this repository. Full-system acceptance, independent rule transfer/release, and the complete fresh frozen User demonstration remain incomplete; M07/M08 must not be declared complete based on this package.

`PACKAGE_VALIDATION.json` inside the handoff records checks performed when that package was prepared. Its synthetic fixtures, fake tool dispatch and old implementation-state statements are historical packaging evidence, not current application results. `SHA256SUMS` verifies package integrity only, not authenticity or engineering acceptance.

## Later owner-approved workflow direction

These decisions guide continuation; this summary does not grant execution authorization or assert every requested behavior is complete.

- Preserve KSU engineering workflows. Prepare reviewed English system requirements from selected source material when needed, before formalization. Guidebook-style descriptions supplement KSU procedures; they do not replace them. Record source lineage and approved training/development/evaluator roles.
- Learn reusable system structure, requirement allocation, contracts, implementation and proof/testing practices as well as error-triggered repair strategies. Keep candidates, revisions, source provenance and human curation. Independent transfer stays in progress until actually executed and passed.
- Epsilon is a cosine-distance threshold: start at 0.1, with an approved maximum of 0.3. Distinguish retrieval from the post-architecture comparison gate and from stopping rules. Contract-feature cosine is not semantic-equivalence proof and cannot replace formal verification.
- Compare directed architectures under a consistent node correspondence, respecting roles, directions and required properties. Names alone are not acceptance criteria. Preserve approved reference abstractions and structural placement, and report exact approved adaptations.
- Report each verification gate and its scope: parsing/type checks, architecture, similarity, HAMR generation, component proofs including Verus, GUMBOX/tests, integration/system checks, and runtime monitoring when configured. A bounded QEMU observation is only evidence for its stated observation window. Missing R2U2 or other checks remain explicitly unrun.
- Let a human review proposed verification units, scopes and exclusions. Retain successful rulebooks with explicit scoped acceptance and linked exclusions, separate scores and coverage denominators. Excluded, deferred, unsupported, failed and unrun checks must remain distinguishable; exclusions receive no passing credit. Formal checks remain mandatory within the accepted scope.
- A requirement absent from a golden reference is a golden-coverage gap, not proof of a tool limitation. Record both categories separately, with evidence. Preserve uncovered English requirements in reports for later scope expansion.
- Diagnose failed repairs and learn from them. The owner increased the campaign repair-attempt policy to six; enforce the configured budget and retry limits and request human guidance when exhausted. This historical choice does not authorize new retries on an exhausted run.
- A human-approved repair of a demonstrated golden contradiction needs the contradiction, source citation, changed premise/specification, review and resulting evidence recorded. An environmental assumption at a system boundary does not automatically prove its propagation through internal processing. Track remaining composition and propagation checks separately.

Case-specific approvals, exact source membership, tool identities, budget consumption and time extensions must be restored from campaign records before resuming that campaign. They are not conveyed by this public summary. New projects require their own configuration and approvals.

## Next implementation work

Large-history Learning/Rulebooks views rebuild and return too much evidence and can appear unresponsive. The known problem remains in this baseline. Prioritize lightweight summaries, pagination, lazy details and non-overlapping polling, while preserving strict evidence freshness checks before approval. Then separately design and validate multi-user identity, PostgreSQL/shared artifact storage, durable workers and transactional budgets. These are future changes, not existing production capabilities.

Application setup remains independent of private campaign restoration. The default starter is a UI fixture with an empty database and no configured Sireum; unavailable formal checks do not pass. Preserve suitable installed tools, check compatibility and pin identities using the dependency guide. Do not automatically reinstall Codex or replace working tools.

## Publication and authorization boundaries

The original handoff is not a license to execute installations, paid model calls, demonstrations, reference changes or rule releases. Historical budgets and time authorizations do not renew when code is cloned or restored. Preserve measured and estimated debits in any later private restoration. Credentials, private signing keys, raw model conversations, private evidence and the database are not part of this baseline.

The earlier `pre-workbench-update-20260927` tag identifies remote master before the application checkpoint. The proposed `workbench-v0.1-baseline` tag identifies the application-plus-handoff development baseline. Neither tag indicates engineering acceptance. UI scaling should proceed on a separate branch after the baseline is published.
