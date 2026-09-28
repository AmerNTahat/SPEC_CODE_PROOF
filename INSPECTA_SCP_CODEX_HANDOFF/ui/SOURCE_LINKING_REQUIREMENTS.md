# Source-linked UI: required implementation contract

**Status: specification for Codex, not an implemented repository backend.** This extends the consolidated UI and traceability goals without changing model, budget, acceptance, or approval boundaries.

## Three different artifacts
- `SCP_WORKBENCH_PREVIEW.png` is a static screenshot. It has no clickable behavior.
- `SCP_WORKBENCH_PREVIEW.html` is an offline synthetic prototype. The Sources & help page contains real relative links to the bundled documentation. Its run controls do not operate tools, browse the filesystem, or call a model.
- The finished Workbench must use registered, permission-checked project sources and actual run records. It must never present the prototype's synthetic content as real evidence.

## Required interactions

### Requirement ID

Actual source to open:
Approved source document revision and passage/page/line/anchor, plus ledger entry.

Why:
Review the intent and whether its formalization is faithful.


### Principle or rule

Actual source to open:
Source example/interaction, scope, counterexample, approved revision, confidence question, and observed results.

Why:
Inspect the origin and limits of the abstraction.


### Rule application

Actual source to open:
Target requirement IDs, concrete role/parameter bindings, and required gates.

Why:
See how abstract roles became model elements.


### Architecture difference

Actual source to open:
Parsed element identities and the approved-versus-candidate diff, with source positions where available.

Why:
Distinguish authorized extensions from accidental damage.


### Repair

Actual source to open:
Before/after diff, protected obligations, proposal/approval, and real tool diagnostic.

Why:
Understand and control the actual change.


### Test/proof/build result

Actual source to open:
Tool identity, command, result, artifact hashes, and logs tied to that run.

Why:
Avoid trusting a model summary instead of tool evidence.


### Evidence/attestation

Actual source to open:
Exact artifact set, signed statement, trusted-policy verification, and freshness state.

Why:
Separate integrity from engineering acceptance.


## Backend requirements
1. Create registered source IDs that bind project, revision/digest, source kind, display name, and permitted location. Use code/document viewers and explicit unsupported-format states; do not invent page or line references.
2. Resolve references by ID through a permission-checked service, not an arbitrary absolute-path URL supplied by an agent or browser.
3. Enforce approved roots, symlink/path-traversal protection, file-size limits, and read-only viewing. Sanitize rendered Markdown/HTML and never execute source content as instructions or scripts.
4. Distinguish human reviewer access from generator access. A visible human review must not automatically add a held-out reference or its contents to model context.
5. Bind links to exact versions. Missing or changed files show BROKEN or STALE; do not silently resolve to a different current version.
6. Provide a safe compare view for approved/candidate artifacts. Human feedback attaches to the actual repair episode and does not approve new rule scope by itself.
7. Keep frontend navigation, backend decisions, and evidence on the shared controller used by the CLI.

## Acceptance tests
Test correct passage navigation; missing/broken and stale references; unauthorized roots; symlinks and traversal; secret/reference visibility boundaries; escaped source HTML; changing artifact hashes; actual diagnosis/diff navigation; and CLI/UI consistency. A PNG or a prototype link into this handoff does not satisfy these runtime tests.
