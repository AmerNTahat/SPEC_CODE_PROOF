# Reuse existing tools before installing anything

## The user's selection

Use the downloaded **Codex v_155 binary**. The default expected executable version is `0.155.*`; verify what the selected binary actually reports with `--version`. The filename alone is not evidence. This preference overrides older instructions to always download the globally latest Codex. Do not install another Codex through npm, Homebrew, a standalone installer, or a new container when the selected binary is usable.

Reuse an existing Sireum CLI and any other required tool when it passes the selected KSU/Loonwerks workflow checks. A fresh Workbench workspace or a current-validated profile does NOT require reinstalling an already suitable tool.

The handoff does not claim that v_155 remains the globally latest release. It intentionally follows the user's selected version. A later change requires an explicit version/path choice, compatibility checks, and a new recorded identity.

## 1. Supply the actual existing paths

Run from the extracted handoff directory. Paths below are examples; substitute your own executable paths. `--codex` selects the downloaded executable, not its containing directory or archive.

```bash
python3 start.py inspect \
  --repo /absolute/path/to/INSPECTA-Spec-Code-Proof-Copilot \
  --codex /absolute/path/to/your/codex-v_155 \
  --sireum-home /absolute/path/to/Sireum
```

This inspects paths without executing the selected binaries or downloading tools.
An existing Codex can be named differently from `codex` and can be outside PATH.
No Node/npm installation is required to reuse the standalone Codex binary.

Alternative environment settings:

```bash
export CODEX_BIN="/absolute/path/to/your/codex-v_155"
export SIREUM_HOME="/absolute/path/to/Sireum"
python3 start.py inspect --repo /absolute/path/to/your/repository
```

`SIREUM_BIN` or `--sireum` can select the exact launcher instead of a home directory.
These variables are for your current shell; the scripts do not edit shell startup files.

To locate a download whose path you do not remember:

```bash
python3 start.py inspect --search-dir "$HOME/Downloads"
```

The scan is shallow and bounded. Matches are listed only: no discovered download is executed, unpacked, moved, or trusted automatically. Select the correct extracted executable explicitly afterward.

## 2. Validate and register, without reinstalling

```bash
python3 start.py prepare \
  --codex /absolute/path/to/your/codex-v_155 \
  --sireum-home /absolute/path/to/Sireum \
  --apply
```

Without `--apply`, this prints a plan. With it, the helper checks Codex's actual version and the CLI features the launcher uses, fingerprints the selected binaries, and writes a local selection record and receipt.

By default, Sireum is inspected but not invoked. Its launcher may initialize/download resources. Explicitly add `--probe-sireum` only when permitting Sireum version/HAMR-help probes and their possible initialization behavior. A source checkout without `bin/sireum.jar` is preserved and reported as needing bootstrap review, rather than executed or replaced.

Probe status is not full compatibility. Authentication/model availability and KSU parser, codegen, Logika, Verus, GumboX, solver and build smoke checks remain separate.

Default local records:

```text
~/.local/share/inspecta-scp-handoff/tool-selection.json
~/.local/share/inspecta-scp-handoff/receipts/
```

`--tool-selection PATH` chooses another record. The record contains paths, versions, fingerprints, and probe outcomes, not credentials. It is not a signed publisher-authenticity claim or an engineering toolchain lock.

## 3. Start Codex using those tools

```bash
python3 start.py start \
  --repo /absolute/path/to/INSPECTA-Spec-Code-Proof-Copilot \
  --codex /absolute/path/to/your/codex-v_155 \
  --sireum-home /absolute/path/to/Sireum
```

The launcher checks Codex before starting it. The exact selected paths and the reuse-first policy are included in the build request; the child process receives `CODEX_BIN`, `SIREUM_BIN`, and `SIREUM_HOME` as applicable. Codex must use those selections instead of independently installing another binary.

The launcher saves the approved selection. Subsequent starts may omit the paths if the same selection file is in use. It checks recorded fingerprints again. If an executable changes, explicitly reselect it after review instead of silently accepting a new identity.

## Selection order

1. Explicit CLI executable or home argument.
2. Explicit environment (`CODEX_BIN`, `SIREUM_BIN`, or `SIREUM_HOME`).
3. Saved local selection, with identity checking.
4. Existing PATH candidates.
5. Known user-local installation locations, including earlier handoff installations.

An invalid explicit/environment/saved selection blocks execution. It must not silently fall back to a different binary. For unpinned PATH candidates, the launcher may find a compatible v_155 instance after an incompatible one; it reports the actual selected path. Downloads scanning never enters that automatic execution path.

## What counts as satisfying the installation requirements?

For Codex: executable runs on this host; actual version matches the user-selected family; required interactive/non-interactive CLI options are present. Authentication, authorized Astra model access, JSONL event semantics, cancellation, and budget capabilities must be validated separately by the build.

For Sireum: launcher/source installation is preserved; active libraries, parser, HAMR generation and required Logika checks pass under the selected profile. Required solver and runtime availability is tested rather than inferred from `--version`.

For Rust/Verus/Microkit/JVM/Node/Python and other dependencies: inspect the existing tool, required version/feature constraints, selected target, and real smoke result. Reuse when compatible. Install only missing components. A missing solver, model library, Rust target or cache is not a reason to reinstall Sireum or Codex.

Status vocabulary:

```text
DISCOVERED_NOT_VALIDATED
REUSE_CLI_READY                     # Codex CLI surface only
REUSE_CANDIDATE_NEEDS_SMOKE_TESTS    # Sireum before actual checks
CLI_PROBED_PROJECT_VALIDATION_REQUIRED
PRESERVE_NEEDS_BOOTSTRAP_REVIEW
BLOCKED
REUSED_COMPATIBLE                   # Reserved for real profile smoke evidence
```

## KSU/Loonwerks adoption behavior

Read the inspected source before invoking an installer:

- `loonwerks/INSPECTA-models/provers-env/readme.md`
- `loonwerks/INSPECTA-models/provers-env/bin/sireum.sh`
- `loonwerks/INSPECTA-models/provers-env/bin/versions.sh`
- The selected KSU example's build, verification, testing, and library configuration.

The inspected `sireum.sh` captures an explicitly supplied `SIREUM_HOME` and adopts it when it contains `bin/sireum.jar` OR `bin/build.cmd`. It deliberately does not overwrite an existing source checkout. A checkout is not automatically a usable built installation.

Do not blindly run the whole native setup to add one missing dependency. Inspect the relevant step and its effects; skip disk/LVM modification, IDE installation, cache deletion, shell rewrites, and unrelated upgrades. An adoption guard can also cause an alleged upgrade to do nothing: verify the actual resulting identity, not only the install command's exit code. Do not invent unimplemented installer flags.

If an existing tool genuinely cannot satisfy the selected profile, report the failing capability and propose a compatible side-by-side installation or worker. Do not replace the original installation. Derive the installer and version choice from the current supported KSU/Loonwerks instructions, not an unrelated newest-version collection.

## Explicit fresh-install fallback

Only when Codex is missing:

```bash
python3 start.py prepare --install-codex --apply
```

The helper checks existing selections first. A valid standalone v_155 is reused without npm or a network version lookup. An incompatible existing/selected executable causes a diagnostic, not automatic installation. If genuinely missing, npm is an optional fallback that resolves only `@openai/codex@0.155.*`, not `latest`, and installs in a new user-local version directory.

A deliberately separate installation requires `--install-codex --fresh-codex --apply` and an explicit changed `--codex-version X.Y.Z` if moving versions. Existing directories are not overwritten. Review/authentication/model checks remain required.

## Containers: use what is already available

`prepare --pull-reference --apply` inspects the selected image locally first. If present, it records the identity without pulling again or running a container. It pulls only a missing image. A daemon/permission error is not treated as missing. An explicit `--refresh-reference` requests a pull of the named reference and retains a receipt; no pruning occurs.

A suitable existing native profile may be the current-validated profile. A preserved existing worker image may also be adopted after smoke tests. Fresh build is a fallback or an explicitly selected reproducibility exercise—not a default obligation to redo installations.

## Limits and testing

The included scripts implement discovery, bounded Codex checks, optional Sireum probes, saved selection, child-process path linkage, and optional missing Codex/reference preparation. They do not implement the Workbench or prove real KSU compatibility. M01 must run and record the real profile checks.

Synthetic test executables validate selection, no-reinstall behavior, failure handling and propagation. They are not evidence that your downloaded binary, installed Sireum, or engineering examples have run successfully here.

Return:
[Installation directory](README.md)
