# Research concepts carried into the implementation
## Verbalization
The user-supplied author page led to Gurnee et al., *Verbalizable Representations Form a Global Workspace in Language Models*, arXiv:2607.15495v1 (July 16, 2026). The paper studies internal representations through its interpretability method. SCP instead elicits explicit engineering decision records and tests their usefulness on separate tasks. It does not claim to recover actual neural causes or implement J-space, activation interventions or reflection fine-tuning. Structured verbalization is now a required learning operation, with event-driven elicitation and fresh-session transfer tests.

## Preference modeling
The exact supplied paper is Foster et al., *AI Research Preference Models*, arXiv:2608.13940v2 (August 25, 2026). The optional adaptation is to rank permitted unexecuted alternatives or bounded pilots before expensive engineering work. It is not a local-embedding algorithm or an acceptance gate. Its use of offline evaluation does not itself mean disconnected inference. Default implementation leaves this hook off; no additional model/fine-tuning is required.

## Operational decomposition
The useful design idea from prior Jev discussion is implemented without Jev: ordinary code handles fully specified operations; the model answers scoped questions only when judgment is required. Include none-applicable/insufficient-evidence outcomes. This is not permission to introduce an excluded model.

## Confidence and reuse scope
Retain the user's exact confidence concept: model-reported belief about rulebook success based on context seen. Record before outcomes and compare with evidence later. Do not automatically average individual rules or claim empirical calibration.

The presentation's reuse/generalization scope and the helper's relative-improvement epsilon are different quantities. Local lexical cosine is a diagnostic, and correctness/architecture policy stays fixed. Generalization and specialization operate on a rule's supported scope with explicit evidence.

## Evidence boundary
Historical DASC numbers remain in their original artifacts. No numeric gain, completed run, universal rule validity, proof of natural-language faithfulness, or novel scientific outcome is implied by this handoff. The complete papers should be read from primary sources for any new research claim; only metadata was rechecked during packaging.
