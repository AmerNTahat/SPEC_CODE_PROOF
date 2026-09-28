# How to build the software, then run learning and validation

## What this ZIP is

This is an integrated Codex build handoff plus working support utilities. It is NOT a prebuilt, independently validated SCP Workbench. The launcher starts Codex to implement it on your workstation. The final real demo is a required build milestone, not a result already achieved here. Installation/authentication and bounded paid-demo approvals may require your input.

Only one launcher is needed. You do not need to read or invoke every file. Do not run the two goal documents directly before the app exists.

## 1. Extract and verify

Extract the ZIP to a normal directory. Keep the `INSPECTA_SCP_CODEX_HANDOFF` folder intact. Open a terminal there. Python 3.10+ is required for the supplied launcher; selected toolchains may impose additional requirements.

```bash
python3 scripts/verify_package.py
python3 start.py inspect --repo /absolute/path/to/INSPECTA-Spec-Code-Proof-Copilot
```

The inspection does not install tools or call a model. Do not run the launcher as root. Keep evidence and learning runs outside the handoff directory so its checksums remain meaningful.

No checkout yet? With Git installed, this opt-in helper can acquire the main public repository without resetting an existing checkout:

```bash
python3 scripts/fetch_sources.py --destination "$HOME/scp-sources" --only INSPECTA-Spec-Code-Proof-Copilot
python3 scripts/fetch_sources.py --destination "$HOME/scp-sources" --only INSPECTA-Spec-Code-Proof-Copilot --apply
```

Use the resulting checkout path for `--repo`. Source acquisition does not execute scripts or initialize submodules; Codex reviews those during setup.

## 2. Reuse your installed Codex and Sireum first

Use the existing downloaded **Codex v_155** executable. The helper verifies its actual `0.155.*` version and required CLI features; it does not assume the filename proves its version. A standalone binary needs no npm installation.

```bash
# Substitute the actual executable and installation paths.
# Inspection only: does not invoke these tools or download anything.
python3 start.py inspect \
  --repo /absolute/path/to/INSPECTA-Spec-Code-Proof-Copilot \
  --codex /absolute/path/to/your/codex-v_155 \
  --sireum-home /absolute/path/to/Sireum

# Optional: probe Codex and save the existing selections; no install flag.
python3 start.py prepare \
  --codex /absolute/path/to/your/codex-v_155 \
  --sireum-home /absolute/path/to/Sireum \
  --apply
```

`--codex` accepts an executable anywhere, even outside PATH or with a different filename. You may instead set `CODEX_BIN`; Sireum supports `SIREUM_BIN`, `SIREUM_HOME`, or explicit `--sireum`/`--sireum-home`. If Sireum is not installed, omit that option and let M01 inspect/install the missing approved components.

To locate downloaded candidates without executing them:

```bash
python3 start.py inspect --search-dir "$HOME/Downloads"
```

Sireum is not invoked by default, because its launcher may initialize dependencies. `prepare --probe-sireum --apply` is an explicit optional local probe; actual project compatibility remains an M01 engineering check. An unbuilt Sireum checkout is preserved, not automatically bootstrapped or replaced.

A usable existing binary is reused even when `--install-codex` is supplied. An incompatible explicit selection causes a clear stop; no silent download, replacement, or upgrade. Authenticate with the selected executable only if it is not already authenticated. The scripts do not overwrite auth/config files.

Only when there is no suitable existing Codex available, the explicitly authorized fallback is:

```bash
python3 start.py prepare --install-codex          # plan only
python3 start.py prepare --install-codex --apply  # install only if missing
```

That optional npm route requires Node/npm and resolves the selected `0.155.*` family, not globally `latest`. A deliberately different version/fresh side-by-side installation requires explicit options and review. Full details are in [Reuse existing tools](installation/REUSE_EXISTING_TOOLS.md).

Optional reference image preparation:

```bash
python3 start.py prepare --pull-reference
python3 start.py prepare --pull-reference --apply
```

This reuses a local image when present and records identity; it pulls only when absent. `--refresh-reference` deliberately requests a fresh pull. Neither path runs the image or establishes its engineering compatibility. M01 tests existing Sireum/solver/project dependencies and prepares only missing approved pieces; a whole fresh build is not compulsory.

## 3. Start the guided build

```bash
python3 start.py start \
  --repo /absolute/path/to/INSPECTA-Spec-Code-Proof-Copilot \
  --codex /absolute/path/to/your/codex-v_155 \
  --sireum-home /absolute/path/to/Sireum
```

The launcher revalidates and passes the selected tool paths into the Codex build request, preserves user-pinned versions, inspects the repository, asks you to identify your available GPT/Astra profile, shows what will run, and asks permission before calling Codex. It stages a checksum-checked handoff copy under `.scp-handoff/` without overwriting your repository's AGENTS.md. Codex reads the master instructions and the revised goals, audits existing work, reuses suitable installed tools, installs only missing authorized dependencies, builds the actual software, runs tests, and works toward the live demo.

To supply a known model ID explicitly:

```bash
python3 start.py build --repo /absolute/path/to/repo --model YOUR_AVAILABLE_GPT_ASTRA_MODEL_ID
```

Replace the placeholder with a real available GPT ID; the launcher deliberately does not guess it. Do not pass an unavailable or third-party model. Interactive mode is recommended for the first build because installation/credentials/approvals can block batch execution.

The launcher has a configurable two-hour build-session wall cap, not a promised completion duration. It does NOT enforce a hard model-token cap for the build session. Review your Codex account/model spending controls. Runtime learning/user budgets are separate and must be enforced by the software being built. Never confuse a usage report with strict token enforcement.

Use `--plan-only` to inspect the proposed launch without model calls. `--batch` is optional, requires an explicit model ID, and cannot silently approve installations or research runs. No automatic unlimited retries occur.

## 4. Follow milestone updates

Codex must print and save an update after each completed milestone or blocker:

Achieved:
Actual implemented behavior.

In progress:
The current implementation/test work.

Remaining:
Outstanding milestones.

Evidence and budget:
Commands, logs, hashes, measured usage, and any limitations.

Blockers/approvals:
Exactly what needs attention.

Read the latest persisted state with:

```bash
python3 start.py status --repo /absolute/path/to/repo
```

Progress is stored in `IMPLEMENTATION_PROGRESS.md` and `reports/build/milestones.jsonl`. A nonzero status while implementation is incomplete is expected. Rerunning the launcher starts a new build session that must inspect existing progress and continue without resetting the codebase. It does not silently extend the previous budget.

## 5. The required demo at the end

The build must attempt the authorized M07 live demo: real Isolette learning, approval of a scoped rule release, a fresh User application, actual validation, an additional selected KSU workflow, explicit creation/rename tests, plots and evidence integrity checks. Demo authorization is bounded and separate from permission to build the app.

Expected deliverables:
`reports/demo/DEMO_REPORT.md`, actual run manifests/logs, plots and data, traceability, UI captures, an attestation result and a replay derived from the real run.

If unavailable credentials/tools or budget block it, Codex must say so, leave M07 incomplete, deliver the partial work and give an exact recovery command. A mock or the included synthetic report must not be passed off as the live demo. A final receipt lives at `.scp-workbench/BUILD_RESULT.json`.

## 6. After the app is built, run real cycles

These are commands the handoff requires Codex to implement. They are not already provided by `start.py`. The launcher delegates to the executable recorded by the completed build:

```bash
python3 start.py app --repo /absolute/path/to/repo -- onboard
python3 start.py app --repo /absolute/path/to/repo -- ui
```

Onboard should guide you through source permissions, available model/toolchain, existing rulebook import, operation, manual versus proposed data split, assistance and budget. Select separate learning/development collections, inspect and approve them, then start a bounded cycle.

Representative post-build usage:

```bash
inspecta-scp learn --config /path/to/approved-learning.json
inspecta-scp validate RUN_ID
inspecta-scp rules review RELEASE_ID
inspecta-scp rules publish RELEASE_ID
inspecta-scp run --config /path/to/approved-user.json
inspecta-scp plot RUN_ID --preset dasc
inspecta-scp demo replay --run-id LIVE_DEMO_RUN_ID
```

Codex must verify exact implemented commands and replace examples in the final handover with commands that actually work in your checkout. `validate` does not edit source files; `run` follows the declared operation. Existing project continuation is not replaced with creation.

The UI and CLI share one resolved configuration. Changing a budget or split does not require editing goal text. Every amendment preserves consumed budget and invalidates dependent evidence when needed. User Mode pins an immutable rule release; new lessons go to the next Learning cycle.

## 7. Try a no-model support demo now

```bash
python3 start.py support-demo --output /tmp/scp-support-demo
```

Open `/tmp/scp-support-demo/index.html`. It plots clearly labeled SYNTHETIC normalized records; it does not run HAMR, generate SysML or prove contracts. Plotting requires Matplotlib. Use `--no-plots` for a standard-library-only HTML/JSON/CSV demonstration.

## Recommended first use

Use public permitted Isolette/KSU material in an isolated development checkout. Establish a working static baseline, then enable learning. Start with one vertical slice and keep broader transfer/fine-tuning out of its critical path. Approve data, model and budgets once per declared scope, not after every harmless operation; preserve approval for publication and requirement/scope changes.

## Optional support-test dependencies

The launcher, catalog, split helper and no-plot report use Python's standard library. Schema checks require jsonschema; chart export requires Matplotlib. Install only in an approved virtual environment, not globally:

```bash
python3 -m venv /path/to/scp-support-venv
/path/to/scp-support-venv/bin/python -m pip install -r requirements-support.txt
/path/to/scp-support-venv/bin/python -B start.py test --schemas
```

The support requirements are version bounds, not the experiment's final lock. Codex must record resolved dependency versions in the Workbench lock. Do not run tests without `-B` in the immutable distribution if you want to keep bytecode files out of its checksum inventory.
