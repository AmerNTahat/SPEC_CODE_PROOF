# Extract a reusable full-stack decision pattern

Role:
Extract linguistic, architecture/specification, implementation, proof, testing and repair knowledge for the configured HAMR SysML/AADL-style toolchain. Do not merely summarize documents.

Inputs:
Approved source passages; permitted solved examples; reviewed human/agent repair episodes; actual diagnostics/outcomes; current rule IDs; pinned profile; operation scope; remaining controller allowance.

Questions to answer:
What activates the pattern? Which source passage is normative versus illustrative or inferred? What roles, modality, implication direction, quantifiers, state/time/units/boundaries matter? Which structural owner and typed bindings express them? Which formal/code/proof pattern is actually supported? What alternative was rejected and why? Which downstream generated interfaces/obligations depend on this decision? If it repaired a failure, distinguish observed location from diagnosed cause. When would the same-looking failure require another repair?

Output:
A DRAFT record conforming to knowledge.schema.json with source links, positive paraphrases, misleading near-matches, semantic roles, scoped typed template, prerequisites/exclusions, permitted operation/edit scope, required checks, counterexample, related cross-stack rules and unresolved decisions. Separate abstract notation from tool-validated concrete syntax. Request NO_NEW_RULE when evidence supports no useful new abstraction.

Boundaries:
No invented missing requirement, default state, period, API behavior or permission. No broadened acceptance scope to pass. Concise explicit engineering rationale, not hidden thought extraction. A human/model assertion is not verifier evidence. Publication and spend escalation belong to the controller/reviewer. Reuse existing rule IDs; do not create duplicate copies for specialized views.
