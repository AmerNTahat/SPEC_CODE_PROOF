# Astra prompt contract — rulebook confidence (v1)
## Question
Based on the approved learning examples, interactions, and context you have seen, how strongly do you believe this exact rulebook release will successfully guide the specified workflow on a new task within the declared scope and budget?

## Inputs
Exact rulebook revision, complete available-context manifest, model settings, intended scope, budget, success definition and whether any relevant outcome is visible.

## Output
A confidence.schema.json record: score from 0 to 1 or INSUFFICIENT_EVIDENCE, concise justification, supporting source/example IDs, limitations, assessment time and outcome visibility. The score expresses your belief, not an empirically calibrated probability. Assess a combined book directly; do not average individual rule scores unless a separate analysis explicitly asks for that arithmetic.

Preserve the exact question/context and original forecast. A later assessment links to but does not overwrite it. Do not infer private examples not in the supplied manifest, invent observed successes, or use a high score to waive a check.


Integrated contract:
Use workflow_goals and WORKFLOW_CONTRACT.md. Full-stack patterns and operation-specific preservation are required. All calls share the controller budget. Source/result/forecast identity and timing must be recorded. Do not publish or modify User releases without approval.
