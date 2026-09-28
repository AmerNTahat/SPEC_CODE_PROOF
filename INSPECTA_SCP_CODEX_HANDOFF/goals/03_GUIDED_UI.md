# Goal 03 — Guided local UI, not a terminal wrapped in a browser
Use one local web UI over the controller; React/TypeScript and a small Python API are the preferred starting stack. Lock the dependencies. No second orchestration implementation.

## Screens
1. Home: Learning and User cards, recent projects, starter examples, recorded-demo replay, current execution machine.
2. Setup wizard: Materials -> Workflow -> Budget -> Review. Server-side approved-root browsing, inspect before paid execution, show actual paths and data visibility. User setup is smaller than learning setup. Advanced tool commands/paths stay collapsed.
3. Live run: current step; time, tokens, repairs and any spend estimate; explicit gate statuses; next decision; pause/stop and expandable logs. Never invent percentage progress for indeterminate model/tool work.
4. Repair panel: real diagnostic, before/after artifact diff, applicable rule/source, protected structure, next checks, allowance; Test/Edit/Reject actions. Human suggestions attach to the episode and cannot override protected policy.
5. Knowledge: combined book and individual rule views; source -> trigger/semantic choice/placement/repair gate -> applicability/counterexample -> validation. Separate a reusable principle from target bindings. Compare revisions; publish only with authorization.
6. Results: outcome, requirements/traceability, architecture, tests/proofs, attestation integrity, and cost. Distinguish mapped/checked/reviewed and accepted/blocked/budget-exhausted.
7. Experiments: matched baselines, source-summary versus abstraction, protected final split, learning/application/total costs. Do not report incomplete runs as savings.

## Mode controls
Learning/User and Automatic/Interactive are independent. Automatic within approved limits is default. New User Mode lessons queue for later, not active rule mutation. Generalize/specialize proposals show the exact scope delta and evidence. Mandatory correctness policies remain unchanged.

## Budget presets
User 20 minutes / 1M aggregate tokens; Learning 60 minutes / 3M. Repair/concurrency/reserve defaults match the core. Label caps, not predicted durations. Strict enforcement unsupported by the adapter must be visibly blocked; authorized best-effort cannot masquerade as hard-cap mode.

## Security/accessibility
Local bind by default, origin/CSRF protection, approved-root path checks, no secrets or unrestricted host browsing in the client. Backend enforces all permissions. Keyboard navigation, real form labels, focus visibility, text/icon status as well as color, readable responsive layout, screen-reader announcements for status without log spam.

## Prototype
ui/SCP_WORKBENCH_PREVIEW.html is a synthetic offline interaction reference, not implemented functionality. Use its layout to discuss flow, not as evidence that tools ran. No public CDN, uploads, network calls, real signature, or fabricated measured success in demo mode.

## Completion
Browser tests covering real setup, pause/resume, repair approval, knowledge review, blocked/failed runs, evidence inspection, reload recovery, and CLI parity. Demonstrate both assistance settings through the same backend.

## v2.0 required wiring
Select operation independently of mode and assistance. Use existing project as authorized; creation requires explicit choice. Materials page supports user-assigned directories or inspected/approved lineage-grouped proposals, with preview and no silent movement. Library page imports actual books and shows full-stack patterns/repair memory and release selection. All fields including budgets feed one backend resolver. Real source links carry revision/hash and access control. Read WORKFLOW_CONTRACT.md, MILESTONES.md and goals/09_COST_TRANSFER_EXPERIMENTS.md for result timing. The bundled PNG/HTML remains a design reference until wired; do not certify M05 from it.

## Tool selection and reuse
Show detected/saved Codex and Sireum locations and selected versions on setup. Accept an executable outside PATH. Display discovered, CLI-probed, and project-validated statuses separately. Honor user-selected Codex v_155. Reuse suitable installed dependencies; do not present fresh installation as compulsory. Share selection with CLI/controller and include exact identities in evidence.
