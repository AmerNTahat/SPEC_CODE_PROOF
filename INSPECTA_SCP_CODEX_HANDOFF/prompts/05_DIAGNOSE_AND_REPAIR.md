# Diagnose and apply a scoped cross-stack repair

Inputs:
Actual fresh tool diagnostics, current artifact hashes, requirement/change scope, stage dependencies, compatible approved repair patterns, previous failed attempts and remaining allowance.

Diagnosis:
Identify where the failure appeared and candidate causes. Distinguish incorrect source formalization, missing architecture, API/precondition misuse, implementation error, missing proof support, profile/tool limitation, stale evidence or environment failure. A proof timeout is not proof that the property is false.

Reuse:
Match tool/profile/operation/obligation/structure, not wording alone. Bind the pattern to current roles. Inspect a discriminating observation before choosing among ambiguous repairs. Allow no applicable repair. Do not repeat an identical unsuccessful repair against unchanged context.

Action:
Propose a minimal patch to authorized model/code/proof regions. Preserve source requirements, contract intent, unaffected archetypes and names. Do not weaken guarantees or add unjustified assumptions, disable tests or mark functions trusted to make checks pass. Regenerate owned artifacts appropriately.

Output:
Diagnosed cause/hypothesis, selected rule and bindings, patch, preserved invariants, checks to rerun, expected evidence and unresolved questions. Testing occurs in a candidate workspace. User Mode queues lessons for future learning without changing the frozen release. Confidence is a forecast, not proof.
