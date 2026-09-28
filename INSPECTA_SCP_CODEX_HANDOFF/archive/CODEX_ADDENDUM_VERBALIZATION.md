# Proposed Codex Addendum: Verbalization-Centered Rule Learning

**Status:** Proposed refinement for review; not an implementation report.
**Date:** September 21, 2026.
**Companion goal:** `CODEX_GOAL_INSPECTA_SCP_WORKBENCH.md`.
**Main sections affected:** 6, 11, 12, 15, 18, and 19.

The original goal remains unchanged. Apply this addendum only as an approved refinement. Preserve its installation strategy, CLI/UI parity, GPT/Astra-only policy, exclusions, budget enforcement, protected references, independent engineering checks, and release-approval rules.

## 1. Purpose and research boundary

The central learning operation is not generic summarization. It is structured verbalization of a reusable engineering decision, followed by abstraction, new-task instantiation, and independent evaluation.

Use the user's DASC formulation as the operational definition:

> Capture the decision, not the text: identify the trigger, semantic choice, structural placement, and repair gate that connect the source context to an appropriate engineering transformation.

Relevant background: Gurnee et al., *Verbalizable Representations Form a Global Workspace in Language Models*, arXiv:2607.15495v1 (2026), especially Sections 2, 3.1-3.5, 7, and 9.1. The paper motivates the investigation; it does not establish this SCP implementation's mechanism or performance.

Do not implement a Jacobian lens, activation extraction/intervention, or reflection fine-tuning in this scope. Do not claim that prompt-generated rules reveal the actual neural cause of a model response. Do not identify local cosine vectors with the paper's J-space. Request concise, source-grounded engineering decision records, not hidden chain-of-thought transcripts.

## 2. Make verbalization an explicit operation

Replace the underspecified extraction stage with this learning sequence:

```text
Approved source context / observable development episode
    -> VERBALIZE_DECISION
    -> ABSTRACT_AND_SCOPE
    -> RECORD_CONFIDENCE_FORECAST
    -> INSTANTIATE_ON_DEVELOPMENT_TASK
    -> INDEPENDENT_CHECKS
    -> COUNTEREXAMPLE / TRANSFER / REGRESSION TESTS
    -> SPECIALIZE, GENERALIZE, SPLIT, MERGE, OR REJECT
    -> REVIEW_AND_PUBLISH
```

These are logical operations in the existing controller, not a requirement to create separate services or issue a new model call for every label. Batch compatible operations within a bounded call when appropriate. Do not increase the parent budget.

A verbalization response must answer:

1. What requirement wording, context feature, structural condition, or diagnostic makes this pattern relevant? Point to the evidence.
2. What engineering relationship or design principle must be preserved?
3. What semantic/formalization choice implements that relationship, and under which prerequisites?
4. Which role owns the behavior or state, and where should the resulting SysML/GUMBO construct belong?
5. What plausible alternative would be wrong or out of scope, and what observable distinction separates it?
6. Which independent checks can challenge the proposed interpretation and detect an inappropriate application?

Do not ask the model to certify its own interpretation as correct. Allow unresolved alternatives and insufficient evidence.

## 3. Preserve relationships, not just concept keywords

Make each principle a relational, scoped proposition. A list such as `state, threshold, alarm` is insufficient.

A candidate record should include:

```text
id / revision / source_episode
source_references / source_artifact_hashes
elicitation_question_version / model_configuration
assessment_timing: before_action | after_feedback | retrospective
available_context_manifest
trigger
principle
semantic_choice
structural_placement_role
prerequisites / exclusions
parameters / engineering_role_bindings
preserved_obligations
counterexample_and_expected_difference
validation_gate_ids
evidence_status
confidence_forecast_reference
```

Extend existing rule records instead of creating a disconnected rule identity system. Maintain the combined and specialized books as consistent views of these records.

Distinguish source-stated knowledge, human-supplied rationale, and model-inferred generalization. Record whether the outcome was visible when the explanation was elicited. An after-the-fact explanation is useful candidate knowledge, but is not a pre-outcome prediction or independent validation.

## 4. Separate elicitation, abstraction, and application

The source-specific decision and the reusable rule are related but different artifacts.

During abstraction, remove incidental names and values only when they are legitimate parameters. Preserve sign, order, timing, units, ownership, direction, quantification, and applicability conditions. Unknown source decisions must remain unresolved rather than be invented for completeness.

During application, generate a compact instantiation record linking the selected rule to the new task:

```text
rule_revision -> target_requirement_ids
role/parameter_bindings -> target_model_elements
preserved_obligations -> required_check_ids
```

Bindings must be checked against the reviewed requirement ledger and approved architecture. Correct prose does not excuse an incorrect placement or connection.

Use the same learned principle to guide different authorized operations where appropriate: specification, contract construction, test planning, diagnosis, or repair. Independent acceptance tests and references must not be generated solely from that same principle.

## 5. Proposed illustrative test family

Use a reviewed state-retention task as an initial example; the following is a derived test design, not a quotation from the handbook:

> A requirement that explicitly preserves the previous output in a specified region requires a representation of prior state and source-defined transitions and initialization.

Extract the general principle and test it on a distinct development task with changed identifiers, parameters, and component roles. Verify where the state belongs, whether the original architecture permits that representation, and whether required initial/mode behavior is specified.

Create an incompatible task with similar vocabulary but a stateless requirement. A successful rule-selection test should avoid adding unjustified state. Missing initialization requirements should produce a request for a reviewed design decision, not a fabricated default.

Keep the source task, its variants, and any solution-bearing material within the appropriate data split. Broader cross-system claims require independent target families beyond this illustrative pair.

## 6. Event-driven capture and assistance

Do not request expansive reflection after every command. Capture candidate lessons at bounded decision points: an approved expert example, a significant human correction, a novel diagnostic, a verified repair, or a proposed scope change.

Automatic assistance may elicit and test draft lessons within approved development scope. Interactive assistance presents the trigger, proposed principle, alternative, and structural implications for human editing.

For User Mode, use only the approved frozen release. Permit compact task-local instantiation and normal repair; queue new lessons for the next release rather than mutating shared knowledge.

Code continues to own deterministic operations, permissions, budgets, validation, and publication. The model retains judgment where choices are genuinely ambiguous. Do not ask a model to make a decision already fully resolved by explicit policy.

## 7. Add a transfer test that isolates the verbalized knowledge

Use fresh Codex sessions and isolated workspaces to apply the frozen release to target tasks. Do not carry over learning-session conversations, resume identifiers, opaque persisted state, or unapproved auto-memory. Keep common target inputs, permitted general documentation, instructions, tools, and budgets consistent.

For the rule-only transfer condition, the source-specific completed solution and its interaction history must be inaccessible. State clearly when a separate experiment additionally permits source-example retrieval. Do not remove necessary target requirements merely to make a condition 'rule only.'

Add focused ablations within the existing baseline study:

- Static operational/KSU baseline with the common permitted information.
- Token-budget-matched source summary or example-retrieval condition.
- Structured verbalized principles and scoped rules, frozen before target application.
- The same framework after approved development-feedback refinement.

On selected cases, compare removal of an individual principle while keeping the rest of the bundle fixed. A selected rule is not automatically a useful rule. Count every extraction, application, repair, validation, and rejected attempt.

The minimum research claim is behavioral usefulness and transfer of the external knowledge artifact, not causal identification of the generator's neural computation. Report no improvement or negative results honestly.

## 8. Counterexamples, independence, and generalization

Test both of the following:

- Meaning-preserving changes: wording, approved renaming, or supported equivalent notation should preserve applicability and the required result.
- Meaning-changing changes: negation, boundary strictness, statefulness, timing, port direction, or component role should cause the appropriate change or rejection.

Expected outcomes must be justified by reviewed task specifications and independent checks, not simply by the same model that proposed the rule. Model-generated tests may assist development; they are not independent evidence by construction.

Require all applicable checks already specified in the main goal: coverage, parsed structural conformance, supported GumboX/manual tests, formal checks, and builds. A passed candidate does not establish universal validity of its natural-language rule.

## 9. UI, CLI, evidence, and budget updates

Add a 'Principle and application' view to the existing learning/repair workspace. Show source evidence, the four core fields, scope changes, a counterexample, model confidence, and observed validation separately. Avoid a new mandatory setup wizard.

Expose verbalization and instantiation events through the existing CLI logs and JSON run records. An optional extraction-profile setting may select structured verbalization versus the summary baseline; it must not create a second workflow engine.

Extend traceability:

```text
source/episode -> verbalized decision -> principle/rule revision
              -> target instantiation -> artifact -> validation evidence
```

Bind these records and their versions into the existing attestation bundle. Attestation covers their identity and provenance, not whether they faithfully reconstruct hidden model reasoning.

All elicitation and re-elicitation calls charge the existing budget. Preserve the final-validation reserve. Use cacheable records keyed by source/context, prompt, model, rule version, and configuration; do not reuse stale assessments after those change.

Keep the user's confidence definition unchanged: model-reported belief about rulebook success given the material seen. This addendum does not turn the score into a calibrated probability or proof of introspective access.

## 10. Acceptance criteria for this refinement

A complete demonstration must show a source-linked verbalized decision, a scoped abstraction, application in a fresh session to a separate task, rejection or correction on a discriminating counterexample, and unchanged requirement/architecture gates.

Deliver test fixtures and a matched comparison that distinguishes abstraction-based reuse from source-summary retrieval. Report setup, learning, and application costs separately under the existing accounting policy.

Do not change infrastructure choices, add new models, expand total budgets, or start fine-tuning solely because of this paper. Preserve all original approval and isolation requirements.

## References

- Gurnee et al., arXiv metadata and version: https://arxiv.org/abs/2607.15495v1
- Full paper, HTML: https://arxiv.org/html/2607.15495v1
- Authors' publication: https://transformer-circuits.pub/2026/workspace/index.html
- Authors' overview: https://www.anthropic.com/research/global-workspace
- OpenAI reasoning interface and summaries: https://developers.openai.com/api/docs/guides/reasoning

**No implementation, model execution, or new validation result is implied by this addendum.**
