> Checkpoint packaging: use the repository-root README and docs/DEPENDENCIES.md for current installation and limitations. The following document retains earlier implementation history.

# INSPECTA/SCP Workbench — implementation in progress

Implementation in progress. This is executable application code, separate from
handoff support utilities. It now supports actual bounded Astra extraction, held-out generation and diagnostic repair, but does not yet complete the release/User acceptance cycle. See [the learning workflow](LEARNING_WORKFLOW.md). `onboard` lists actual capabilities and missing stages.

Run from the repository root:

```sh
./inspecta-scp onboard
./inspecta-scp --json doctor
./inspecta-scp --json resolve --config workbench/profiles/producer-consumer.check.json
./inspecta-scp --json check --offline --config workbench/profiles/producer-consumer.check.json
./inspecta-scp --json check --offline --config workbench/profiles/producer-consumer.engineering.check.json
./inspecta-scp --json status RUN_ID
./inspecta-scp --json logs RUN_ID
./inspecta-scp --json trace RUN_ID
./inspecta-scp --json trace RUN_ID --input-file relative/Model.sysml
```

The shell launcher reuses `.venv/bin/python` (Python 3.11+) or INSPECTA_PYTHON.
The core run controller uses the standard library; knowledge validation uses the pinned jsonschema dependency. The vendor directory
records unchanged handoff helper provenance. It has no model or download fallback.

Profiles resolve paths relative to their containing directory. Every input must
appear in an explicit relative file allowlist. Runs snapshot the bytes currently
present, including authorized dirty/untracked inputs; original files are untouched.
Hidden, secret-key and evaluator directory paths are excluded. A final source hash
check reports intervening changes. No source promotion is implemented yet.

SQLite stores immutable config identities, state events, deadline and usage ledger.
`--prepare-only` makes a READY run without executing tools. `pause RUN_ID`,
`resume RUN_ID`, `stop RUN_ID`, and `execute RUN_ID` share controller methods.
Resume does not renew deadlines or token allowances. For an active worker, pause
and stop first persist requests; only that worker acknowledges process cancellation.
An interrupted host process does not automatically restart or erase its budget.

The initial trusted adapter is `sireum hamr sysml tipe`. It runs inside a restricted
bubblewrap filesystem with no network, home credentials, evaluator tree or Docker
socket. Only the selected initialized Sireum installation and candidate models are
mounted along with system executables/libraries. A nested-namespace denial blocks
the check rather than disabling isolation. Other mandatory checks remain NOT_RUN.
CHECKED means only the selected checks passed. It never means formally verified
units, engineering acceptance, or complete system validation. Instantiation warnings
and substituted missing types currently produce UNKNOWN, pending a reviewed policy.

`run` and `learn` can resolve and snapshot inputs but explicitly BLOCK before model
generation. No learned release, model execution, complete formal gate adapter, engineering acceptance or live demonstration is claimed by this version.

Exit codes: 0 completed command (inspect returned state), 1 checker rejection,
2 invalid configuration, 3 blocked, 4 exhausted, 5 cancelled.

Test application logic independently of handoff support tests:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=workbench .venv/bin/python -m unittest discover -s workbench/tests -v
```

Open the local interface from the repository root:

```sh
./inspecta-scp ui
```

Open the private loopback URL printed by that command in your browser. Its
fragment token authenticates this local session; it is removed from the address
bar after connection. Closing the server leaves runs and imported records on disk.
The interface prepares runs, displays evidence/status, pauses/resumes/stops them,
imports the configured books, opens exact source revisions, and reviews requests
for budget extensions. It uses the same resolver and controller as the CLI.
Additional reviewed profiles can be selected with repeated `--profile PATH`;
source-book roots with repeated `--library-root PATH`. HTTP clients cannot choose
arbitrary filesystem roots. The default roots are the existing Isolette and
`rule-books_7` directories.

The frontend was built using the existing Node 10.19.0/npm 6.14.4 installation.
Dependencies are pinned in `frontend/package-lock.json`; no runtime CDN is used.
For a fresh checkout, install/build only the missing frontend dependencies:

```sh
cd workbench/frontend
npm ci --ignore-scripts --no-audit --no-fund
npm run build
```

Rule validation reuses jsonschema 4.25.1 in the existing Python environment.
`requirements.txt` pins that dependency if an isolated environment needs it.
Do not reinstall working Codex or Sireum tools to use this interface.

Inspect the imported knowledge without model calls:

```sh
./inspecta-scp --json rules import --directory isolette/sysml/rule-books
./inspecta-scp --json rules import --directory rule-books_7
./inspecta-scp --json rules catalog
./inspecta-scp --json source SOURCE_ID --start 1 --end 10
./inspecta-scp rules --help
./inspecta-scp approval --help
./inspecta-scp budget --help
```

Import preserves original text, rule IDs, JSON variants and confidence fields.
Markdown rule references are an index into exact documents, not a claim that all
prose has been converted into structured rules. Historical “final” or “verified”
titles do not grant approval. Candidate proposals require exact source hashes,
schema validation, applicability and a counterexample. Release drafts omit raw
source/archive fields; publication additionally requires independent validation.
The transfer-attestation adapter is still missing, so publication fails closed,
even after a local reviewer approves a draft. Local reviewer text is attribution,
not cryptographic identity. Human-only sources are not generator exports.

Run the opt-in browser test from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=workbench .venv/bin/python workbench/tests/run_browser_smoke.py
```

It starts actual Firefox with a disposable profile and loopback application server,
uses a synthetic project and never invokes a model. Socket restrictions in an
outer sandbox may require permission to run it from the ordinary host terminal.
The browser sandbox stays enabled. Its screenshot is application-test evidence,
not an Isolette/KSU engineering demonstration.

Paid demonstrations are deferred by user instruction. Generation, accepted source
promotion, complete engineering gate adapters, independent rule transfer, and full
cross-task learning workflows remain unfinished. Provisional repair and local attestation are described below. No live demonstration or complete
Workbench acceptance is claimed.

Dataset assignments use registered, hash-checked sources. Register only an explicit
allowlist; put reference answers in a separate evaluator root:

```sh
./inspecta-scp --json datasets register --directory /absolute/task/root --role learning --files Model.sysml requirements.md
./inspecta-scp --json datasets register --directory /absolute/reference/root --role evaluator --files Answer.sysml
./inspecta-scp --json datasets propose --input tasks.json
./inspecta-scp --json datasets catalog
./inspecta-scp --json datasets request-review DATASET_ID
```

`tasks.json` contains `tasks`, `strategy`, `fractions`, and a text `seed`. Each task
contains `id`, reviewed `family_id` and `lineage_id`, `role`, `source_ids`, and
`reference_ids`. Source IDs come from registration. Reference IDs must be
evaluator-only. Choose `user_assigned` with explicit learning/development/final
roles and null fractions, or `propose_grouped` with explicit three fractions
summing to one and null initial roles. The latter proposes membership for review;
it never moves files. Exact source and solution duplicates connect groups.
Unknown lineage blocks a proposal; provided metadata does not prove semantic
independence. The older singular `dataset` command is only a stateless manifest
utility; use plural `datasets` for durable reviewed assignments.

The Dataset assignments UI uses this same service and approval queue. A saved
profile or New workflow form can bind `dataset_assignment` and `dataset_task`.
Both are required together. Before snapshotting or executing, the controller
requires current approval, unchanged sources, and inputs drawn from that selected
task. Copies of registered evaluator answers are rejected even under a new name.
Final tasks cannot run in Learning mode. The service does not export any task
answers to a model, and it makes no final-transfer claim.

In New workflow, choose **No dataset — use this project directly** for an ordinary
project check. The optional assignment selector lists recorded proposals and
allows only current approved assignments. Then select one of that assignment's
tasks. **Use project without dataset** clears both fields together, including
values inherited from the saved profile. An incomplete pair is caught in Materials
before the Review step. A configuration error does not need a session token;
the reconnection form appears only for an actual authentication rejection.

Dataset assignments also has an **Add an inspected project** form. Select a saved
profile, enter the task name and reviewed family/lineage, and choose its role. The
backend registers only that profile's source allowlist and fills the inventory.
It cannot register arbitrary filesystem paths through HTTP. Review the populated
inventory before saving a manual or grouped proposal.

The `producer-consumer.engineering.check.json` profile executes `parse_type`,
`hamr_codegen`, and `integration_constraints` inside the existing sandbox.
Generation saves Slang/JVM artifacts separately from the source; it does not count
as compilation. Integration checking requires a nonempty set of claims, the
tool's success marker, and per-connection JSON feedback with an Unsat solver
result and the actual SMT query. A successful exit with no obligations is UNKNOWN.
These are connection-compatibility proofs only, not implementation correctness or
verified-unit acceptance. Full `configured_formal_verification`, build and
independent requirements tests remain separate required gates.

Run details now includes **Trace requirements and inputs** and per-gate evidence
buttons. The trace connects recorded obligations, architecture elements, registry
units, implementation files and executed gates. Missing registries or executed
rule bindings stay explicitly missing. Source links show the exact run snapshot,
with a warning if the original source has changed. The viewer rejects changed
snapshots, files outside the run allowlist and evidence not attached to that run.
CLI `trace --evidence SHA256` and the UI use the same service. These authenticated
human views are not generator context exports.

After updating this checkout, stop the previous UI server with Ctrl+C in its
terminal, rerun `./inspecta-scp ui`, and open its newly printed private URL. This
loads updated backend routes as well as the rebuilt frontend. Existing records
stay on disk. For the dataset-pairing error shown in the September 22 screenshot,
choose **Use project without dataset** in Materials, then proceed to Review and
resolve the configuration. No session token is needed to fix that configuration.

Requirement and structure checks now use the installed Sireum parser and HAMR
instantiator through `adapters/export_architecture.sc`. The adapter runs inside
the existing isolated worker, exports AIR plus resolved package declarations,
and binds them to input/config/tool hashes. `architecture_capture` records this
output; it does not approve the design. `architecture` compares both views with
an approved immutable policy. Position metadata is ignored, recognized time units
are normalized, and every other difference requires an exact reviewed delta.
Unknown instantiation warnings block conformance. Text similarity never decides
architecture equivalence.

```sh
./inspecta-scp --json check --offline --config workbench/profiles/producer-consumer.structure.check.json
./inspecta-scp architecture snapshot SNAPSHOT_ID
./inspecta-scp architecture propose SNAPSHOT_ID
./inspecta-scp architecture request-review POLICY_ID
./inspecta-scp requirements propose --input reviewed-draft.json
./inspecta-scp requirements request-review LEDGER_ID
```

These commands create review requests; they do not approve them. Use the UI review
queue or the exact-digest `approval` command for an actual human decision. Put
approved record IDs in the saved profile as `architecture_policy` and
`requirement_ledger`. Requirement sources must be exact registered revisions.
Duplicate IDs, fabricated citations, wrong owners and missing mapped guarantees
are rejected. Coverage means resolved mapping; proof and semantic fidelity remain
separate gates. Source changes or approval revocation invalidate dependent runs.

Provisional repair branches use the original run's deadline and attempt caps.
Set `repair_allowed_files` explicitly in the saved profile before creating the
run. A patch JSON maps each permitted path to `expected_sha256` and replacement
`text`; nothing outside this declared scope is editable.

```sh
./inspecta-scp repairs stage RUN_ID --issue ISSUE_ID --patch patch.json
./inspecta-scp repairs validate CANDIDATE_ID
./inspecta-scp repairs catalog --run-id RUN_ID
```

`--parent CANDIDATE_ID` stages a follow-up against an earlier provisional revision,
including a failed one. Repeated/no-change attempts are rejected. Checks preserve
the original project and prior run result, and never replenish its budget.
`CHECKED_PROVISIONAL` is only a result for the configured subset of checks. Source
promotion remains unavailable until the full engineering acceptance path exists.
The Repair revisions page shows exact diffs, parent identities and real results.

Metrics use `unit_registry`, a reviewed immutable record declared before a run.
`registry propose --input registry.json` validates obligation/formal/implementation
mappings; `registry request-review REGISTRY_ID` requests a human decision. Duplicate
formal targets cannot inflate the denominator. No registry means unknown coverage;
zero verified units means undefined per-unit costs, not zero. Formal checks must
report each registered obligation; a parser success or mapping is not counted.

```sh
./inspecta-scp metrics RUN_ID
./inspecta-scp plot RUN_ID --output reports/my-new-run
```

Plots export CSV/JSON, PNG/SVG/PDF and a digest manifest. They use Matplotlib 3.10.7;
missing plotting dependencies are pinned with wheel hashes in
`plotting-requirements.lock`. Historical DASC figures and the historical 42-unit
inventory were not found at the referenced repository paths and have not been
reconstructed from a count. Existing metrics scripts are preserved; their embedding
calls, assumed counts and generic result fields are not a verification source.

Local attestation uses securesystemslib 1.3.1 DSSE envelopes and in-toto Statement
v1. It reuses cryptography 46.0.3. The newer downloaded library required a crypto
upgrade, so it was not installed. Private signing keys must be outside the
repository, source workspace and controller state, with private file permissions.
There is no HTTP signing endpoint and no automatic production key generation.

```sh
./inspecta-scp attest policy RUN_ID > /trusted/location/run-policy.json
# Independently review this policy and select an external trust root before use.
./inspecta-scp attest create RUN_ID --key /trusted/location/private.pem --policy /trusted/location/run-policy.json --output reports/new-bundle
./inspecta-scp attest verify --bundle reports/new-bundle --policy /trusted/location/run-policy.json --trust /trusted/location/trust.json
```

The verifier can run without the controller database:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=workbench .venv/bin/python -m inspecta_scp.verify_attestation --bundle reports/new-bundle --policy /trusted/location/run-policy.json --trust /trusted/location/trust.json
```

Trust JSON contains `keys` (key ID to securesystemslib public-key object) and
`threshold`. Both trust and expected policy must be outside the bundle. Verification
checks signature, subjects, current source files, config/input/result/event identity,
required gate records and external requirement dependencies. A valid signature of
incomplete evidence reports `INCOMPLETE` and exit 3; it is not engineering acceptance,
certification or a SLSA claim. The committed reporting integration uses an explicitly
TEST ONLY ephemeral signer; its private key was deleted.
