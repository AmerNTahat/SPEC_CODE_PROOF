# INSPECTA/SCP Workbench — controller foundation

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
The controller itself has no third-party Python dependencies. The vendor directory
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
generation. No learned release, approval service, model adapter, React UI, formal
gate adapter, evidence signature, or live demonstration is claimed by this version.

Exit codes: 0 completed command (inspect returned state), 1 checker rejection,
2 invalid configuration, 3 blocked, 4 exhausted, 5 cancelled.

Test application logic independently of handoff support tests:

```sh
PYTHONPATH=workbench .venv/bin/python -m unittest discover -s workbench/tests -v
```
