# Goal 04 — Controlled Codex/Astra integration and honest budgets
Inspect installed Codex help, official noninteractive documentation, capabilities, and authentication. Use supported `codex exec` structured events/output with least required permissions. Do not rely on deprecated flags, undocumented config keys, or guessed Astra identifiers.

## Boundary
The Codex adapter receives permitted task context, frozen rules, approved ledger/architecture, editable candidate scope, and remaining allowance. Deterministic operations run through trusted tool adapters. Candidate programs/tests cannot read model credentials, host secrets, evaluator references, or signer keys. Do not grant Docker-daemon authority to an agent.

## Default limits
User: 1200 seconds, 1M aggregate model tokens, 3 repairs/issue, 8 repairs/run.
Learning: 3600 seconds, 3M tokens, 5 repairs/issue, 20 repairs/run.
Concurrency 1; reserve 20% wall time for final checks and packaging. Adjustable by explicit run config/approval. Do not assume these caps finish full historical Isolette experiments.

All child calls, retries, confidence forecasts, extraction and repair count against the parent. Reserve before a call; reconcile actual usage after. Do not double-count cached-input or reasoning subsets. Unknown usage is not zero. Setup costs, active computation, human wait, and application costs are separate fields.

## Hard versus best-effort
Document and test whether the installed CLI/provider can enforce the advertised token bound. Post-turn totals and killing a process after a threshold are not proof of a hard in-flight limit. Strict mode refuses paid execution when required guarantees are unsupported. Best-effort mode needs recorded authorization and reports overshoot/cancellation uncertainty. Do not silently switch to another backend.

Time limits use monotonic deadlines within the run and persisted accounting across restarts. Pause does not reset the overall deadline or allowance. Report human waiting separately. Ask for an extension only when necessary, showing unresolved work and proposed allowance.

## Data and sessions
Use project-specific instructions and approved skills; scrub unrelated user memory/configuration in controlled experiments using supported mechanisms. Fresh final-transfer sessions must not inherit learning context or resumed session state. Agent-accessible generated tests are not evaluator-only tests. Enforce file/network isolation, not instructions alone.

## Completion
Adapter conformance tests on actual installed events, usage accounting, cancellation, auth redaction, source visibility, output-schema validation, no fake hard-cap guarantee, and no paid CI without authorization. Record Codex/model identity and every allowed capability.

## Build versus research execution
Building this software uses a separately authorized Codex session. The launcher can enforce a wall deadline and capture events; it does not claim request-level token enforcement. Real learning/user cycles must implement strict capability checks and refuse unsupported hard caps, or obtain explicit best-effort consent. Build usage, live demo campaign usage, and run usage are distinct ledgers with aggregate ceilings; no budget reset across resume or approval amendment. The exact available GPT/Astra identifier must be resolved at setup.
