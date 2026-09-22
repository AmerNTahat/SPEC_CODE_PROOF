# INSPECTA/SCP Workbench — implementation in progress

Implementation in progress. This is executable application code, separate from
handoff support utilities. It does not yet implement a complete Workbench or live
learning demonstration. `onboard` lists actual capabilities and missing stages.

Run from the repository root:

```sh
./inspecta-scp onboard
./inspecta-scp --json doctor
./inspecta-scp --json resolve --config workbench/profiles/producer-consumer.check.json
./inspecta-scp --json check --offline --config workbench/profiles/producer-consumer.check.json
./inspecta-scp --json status RUN_ID
./inspecta-scp --json logs RUN_ID
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
generation. No learned release, model execution, complete formal gate adapter, evidence signature, or live demonstration is claimed by this version.

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

Paid demonstrations are deferred by user instruction. Generation, transactional
repair, complete engineering gate adapters, independent rule transfer, attestation,
and full split/repair UI flows remain unfinished. No live demonstration or complete
Workbench acceptance is claimed.
