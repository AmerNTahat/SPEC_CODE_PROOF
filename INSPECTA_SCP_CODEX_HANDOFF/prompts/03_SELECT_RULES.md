# Select applicable knowledge within budget

Inputs:
Resolved operation, profile, reviewed requirements/change scope, protected baseline, eligible rule metadata and current diagnostic/context. Only approved exported knowledge may be retrieved in User Mode.

Task:
Compatibility-filter first using deterministic rules. Use local lexical/structural signals as relevance aids. If semantic ambiguity remains, choose the smallest compatible bundle with required dependencies. Explain the binding-relevant reasons briefly. Allow NONE_APPLIES or INSUFFICIENT_EVIDENCE. Do not treat confidence/cosine as acceptance or reuse a patch solely because error text resembles an old message.

Output:
Selected exact IDs/revisions, role bindings needed, excluded conflicts, required checks, alternative diagnosis if unresolved, and budgeted next action. Distinguish code-only/proof-only completion from whole-system construction. Unrelated system reconstruction is never an automatic fallback.
