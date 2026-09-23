# Architecture equivalence and semantic review

The old development report compared normalized AIR plus declaration ASTs for exact
identity. Its 41/844 differences mixed names, order, expression spelling and actual
structure. Those numbers remain historical diagnostics, not architectural defect
counts. New graph assessments are separate immutable evidence records.

The new evaluator builds a directed attributed multigraph from instantiated AIR.
The projection version is `hamr-directed-structure-v2`. Vertices represent model
roots, components, ports, declared connections and resolved connection instances.
Edges represent containment, ownership, directed source/destination incidence and
reference-valued bindings. Resolved connection paths preserve ordered declaration
references, their contexts and parent relationships. Connection vertices retain parallel-edge multiplicity.
Names and declaration order do not color vertices. Component/port categories,
port directions, supported property keys and values do. One bijection must preserve
all these attributes and every directed edge. A returned witness is checked again
against the complete edge multiset. Equal vertex/edge counts alone cannot pass.
Unknown structures and exhausted search bounds return UNKNOWN, never a guessed pass.

This is a structural projection: payload type equivalence, modes/flows without an
adapter, GUMBO meaning, implementation, and tests require separate checks. Classifier
spellings are not used to force name equality; consequently the current projection
must not be presented as full data/type conformance. Graph equivalence does not
permit renaming an existing source project or automatically promote generated files.

After structural PASS, the evaluator reports cosine similarity over parsed
assume/guarantee expression features, retaining operators, literals and obligation
kinds while ignoring formatting/compiler attribute metadata. This is more relevant
than whole-file token cosine, but it is still an unordered feature diagnostic,
not semantic embeddings or a logical-equivalence proof. Helper definitions, state
transitions, variable correspondence and assumption discharge remain separate.
A high score cannot override any failing gate. Retrieval ε remains a separate
parameter and is not silently applied as an equivalence acceptance threshold.

Latest saved live models, reevaluated offline with this new checker:

| Example | Graph assessment | Contract feature cosine |
|---|---|---|
| Producer/Consumer | PASS: 15 vertices, 32 directed edges on each side; bijection saved | Approximately 0.9752, advisory; 3 obligations per side |
| Isolette | FAIL: 1162 vs 935 vertices, 3164 vs 2534 directed edges | Not run because structural equivalence failed |

These counts include ports/connections and all exported instantiated roots, not just
application components. The Isolette captures contain genuine decomposition/count
differences in this representation. Renaming alone cannot fix that mismatch.

Recommended acceptance sequence: typed directed graph equivalence → mapped payload
and requirement/contract fidelity → implementation/proof/tests. Use cosine to
prioritize review and propose correspondence, never as the final correctness test.
The current graph implementation searches exact compatible mappings without cosine
pruning, so a poor text score cannot hide a valid structural mapping.

Replay without a paid model call:

```sh
./inspecta-scp --json learning compare-graphs --result 4fe9c1472b5c297f80c5cf90468367f486c17a688217f1dc8e68a87a716887a9
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=workbench .venv/bin/python workbench/tests/run_graph_capture_checks.py
```

The second command includes explicit mutations of saved AIR to test consistent
renaming, reversed wiring and incorrect processor binding. Those fixtures are
checker tests, not additional live generated systems or behavioral proofs.
