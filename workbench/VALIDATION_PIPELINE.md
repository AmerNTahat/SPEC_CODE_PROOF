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
