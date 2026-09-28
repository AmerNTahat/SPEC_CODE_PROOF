# Controlled upgrade runbook

Default is reuse, not upgrade. Keep the user-selected Codex v_155 and compatible Sireum in place. Follow this runbook only for an explicitly approved update or a demonstrated missing/incompatible capability. See [reuse policy](REUSE_EXISTING_TOOLS.md).
1. Preserve the last verified tool lock and reference image digest. Record current clean/dirty repository state.
2. Check selected existing versions against required KSU features first; when an update is necessary and approved, resolve requested official Sireum/Codex versions and inspect release/compatibility notes. Record exact source identities, not only 'latest'.
3. Create a separate proposed profile/image or user-local tool directory. Do not mutate active experiment tools.
4. Retain compatible Rust/Verus/Microkit pins unless the new feature requires a reviewed update. Add missing solvers and dependencies through a reproducible recipe.
5. Run environment/capability checks, example generation/proofs/tests, structure mutation tests, budget/event adapter conformance, and network-off checks.
6. Compare artifacts/diagnostics and report changed assumptions or supported constructs. Unknown/failed gates block adoption for their scope.
7. Approve the profile, store locks/digests and rollback instructions, and keep the old profile. Refresh evidence affected by changed tools.
8. Run every baseline/evolving condition on the same adopted environment. Report toolchain differences as a separate study.

Never automatically grow disk/LVM, prune shared caches, overwrite unrelated auth/configuration, disable certificate validation, publish images or repositories, or run an agent with the Docker socket. Treat development images and passwords/sudo defaults as things to harden, not acceptance boundaries.
