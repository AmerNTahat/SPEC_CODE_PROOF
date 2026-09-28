# Goal 07 — Traceability, stale-evidence control and verified attestation
Record links continuously: source -> verbalized decision -> rule revision -> target instantiation -> SysML/GUMBO -> generated/developer implementation -> test/proof/build -> delivered artifact.

Add source hashes, tool/model/prompt/configuration identities, command IDs, timestamps, outcomes, budgets, and approvals. Generate readable change reports from structured records. Distinguish prospective requirements tests from post-hoc contract-derived tests.

## Freshness
A change to requirements, models, rules, dependencies, tool settings, evaluator policy or relevant implementation invalidates affected evidence. Record a dependency graph and conservative invalidation where precision is unavailable. Old green logs cannot approve new files. Preserve history rather than overwrite.

## Signing design
Use a maintained implementation of a standard statement/envelope, with a custom validation predicate that identifies its scope. Trusted controller/evidence service hashes immutable final artifacts and signs them outside the agent/candidate environment. Do not invent cryptography, place keys in the repository, or auto-publish to external transparency services. Local private trust is an acceptable first profile.

## Independent verification
Verifier takes an expected policy and trust root from outside the candidate bundle, checks signature/signer, digests, source/tool/ledger identity, mandatory results, approved exclusions and freshness. A candidate-supplied policy or trust root cannot approve itself. Signed failed/incomplete records must say so. Do not claim certification or a SLSA level.

## Threat boundary
Do not mount Docker sockets into Codex or candidate workers. Image users/sudo configurations are not containment. Restrict mounts, credentials, capabilities, resources and network. Reference answers, signing keys and model tokens are in separate trust zones. A Git worktree shares repository objects and is not adequate isolation from hidden Git history by itself. Test parent paths and symlinks.

## Demonstration tests
Modify a signed model/binary; replace a report with an older pass; omit a mandatory gate; change approved policy; substitute an untrusted key; change a source library; attempt path traversal. Each must fail for the correct reason. Test success on the unchanged approved bundle.

`verify_package.py` only checks this ZIP's checksums. It is not the application attestation verifier and must never be repurposed as proof of engineering acceptance.
