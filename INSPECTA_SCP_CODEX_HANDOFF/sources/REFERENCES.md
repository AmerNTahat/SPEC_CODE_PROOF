# Primary-source register

Prepared September 21, 2026. Resolve current paths and versions at implementation time. Documentation inspection is not installation or validation. No third-party tool binaries, weights or paper PDFs are redistributed.

## R01 — Loonwerks environment overview
https://github.com/loonwerks/INSPECTA-models/blob/main/provers-env/readme.md

Shared installation recipes, profiles, platform guidance; checked during packaging.

## R02 — Loonwerks container guide
https://github.com/loonwerks/INSPECTA-models/blob/main/provers-env/docker/readme.md

Reference image, contents, missing solvers/caches, build/update path; checked during packaging.

## R03 — Loonwerks version configuration
https://github.com/loonwerks/INSPECTA-models/blob/main/provers-env/bin/versions.sh

Resolve and audit at installation; no assumed latest version.

## R04 — Loonwerks native/VM guide
https://github.com/loonwerks/INSPECTA-models/blob/main/provers-env/vagrant/readme.md

Platform-specific setup and appliances; recheck before choosing backend.

## R05 — SCP source repository
https://github.com/loonwerks/INSPECTA-Spec-Code-Proof-Copilot

Inspect the actual extension checkout and preserve source history.

## R06 — KSU agent-training project
https://github.com/santoslab/HAMR-agent-configuration-experiments

Locate current workflow/examples; preserve source and exposure provenance.

## R07 — KSU testing guide
https://github.com/santoslab/HAMR-agent-configuration-experiments/blob/main/hamr-claude-training/doc/testing-guide.md

Three test styles, oracle caveats, serial host testing; opening section checked during packaging.

## R08 — KSU build and verification guide
https://github.com/santoslab/HAMR-agent-configuration-experiments/blob/main/hamr-claude-training/doc/build-and-verification-commands.md

Inspect exact selected target commands and prerequisites at implementation.

## R09 — KSU tool interface guide
https://github.com/santoslab/HAMR-agent-configuration-experiments/blob/main/hamr-claude-training/doc/mcp-tools.md

Map documented semantics to actual supported Sireum CLI operations.

## R10 — OpenAI Codex source README
https://github.com/openai/codex/blob/main/README.md

Official current installation routes; checked during packaging.

## R11 — OpenAI Codex CLI documentation
https://developers.openai.com/codex/cli/

Current official entry point; may redirect to ChatGPT Learn. Recheck at install.

## R12 — OpenAI Codex noninteractive documentation
https://developers.openai.com/codex/noninteractive/

Structured events, schema output, sandbox/auth boundaries; checked during packaging.

## R13 — Codex instructions
https://developers.openai.com/codex/guides/agents-md/

Instruction scope/loading; use intentionally for controlled experiments.

## R14 — Codex skills
https://developers.openai.com/codex/skills/

Procedural instructions, scripts/references; recheck conventions at implementation.

## R15 — Sireum official setup
https://sireum.org/getting-started/

Resolve official CLI capabilities and distribution on target machine.

## R16 — KSU HAMR tutorials
https://github.com/santoslab/hamr-tutorials

Supplementary current examples/CI; inspect exact revision.

## R17 — Requirements Engineering Management Handbook
https://www.faa.gov/sites/faa.gov/files/aircraft/air_cert/design_approvals/air_software/AR-08-32.pdf

Lempia and Miller, DOT/FAA/AR-08/32, 2009; source material, not automatically a machine oracle.

## R18 — Verbalizable Representations Form a Global Workspace in Language Models
https://arxiv.org/abs/2607.15495v1

Gurnee et al.; arXiv metadata verified, July 16, 2026. Verbalization motivation, not a claimed implemented neural mechanism.

## R19 — AI Research Preference Models
https://arxiv.org/abs/2608.13940v2

Foster et al.; v2 August 25, 2026 metadata verified. Optional candidate ranking, not semantic embeddings.

## R20 — in-toto Statement
https://in-toto.io/Statement/v1

Attestation subject digests and predicate identity; confirm maintained implementation.

## R21 — SLSA artifact verification guidance
https://slsa.dev/spec/v1.2/verifying-artifacts

Signer and expected-configuration verification; no certification/level claim.

## R22 — Docker build best practices
https://docs.docker.com/build/building/best-practices/

Reproducible builds, image identity and digest pinning.

## R23 — Docker security
https://docs.docker.com/engine/security/

Daemon authority and container boundaries; do not give agents the socket.

## Reuse-first source check — September 22, 2026

Loonwerks shared environment recipe:
https://github.com/loonwerks/INSPECTA-models/blob/main/provers-env/readme.md

Sireum adoption guard (inspected blob c0611491b5fb4492d791039dd3c23e569ba19487):
https://github.com/loonwerks/INSPECTA-models/blob/main/provers-env/bin/sireum.sh

The source explicitly preserves a supplied SIREUM_HOME containing bin/sireum.jar or bin/build.cmd; an unbuilt checkout is not a verified runtime. Read the actual revision used at setup, including its adoption/upgrade caveat. Do not invent a force/adopt option absent from that revision.

Codex CLI interface and automation references (inspect selected binary help as source of truth):
https://developers.openai.com/codex/cli/reference/
https://developers.openai.com/codex/noninteractive/

The v_155 version preference is from the user, not a verified claim about the globally newest release. The helper validates the selected executable's real version instead of using its name as evidence.
