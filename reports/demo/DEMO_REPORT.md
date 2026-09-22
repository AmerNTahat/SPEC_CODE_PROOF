# Live demonstration status: DEFERRED BY USER / NOT RUN

No live model-driven Isolette learning -> release review -> fresh User cycle or
additional KSU learning/application demonstration has been run. No synthetic demo
has been substituted. Demo model calls: 0; model tokens: 0; actual billing: unknown
for this implementation session and not inferred from token prices.

Completed engineering preparation is recorded separately in reports/build:
real Isolette and Producer/Consumer type-check smoke commands, Isolette codegen
and Logika invocations, and three isolated application-worker integration checks.
The Logika invocations did not establish discharged obligations. These are not
live learning, behavior verification, whole-system acceptance, or transfer evidence.

The user explicitly deferred paid demonstrations and instructed implementation to continue.
No paid-demo approval is currently requested. M07 remains incomplete.

Prerequisites only if the user later resumes M07:
1. Complete the missing M01/M02-M06 application and engineering capabilities.
2. Establish a reviewed requirement/unit registry and compatible Isolette proof,
   build and independent test profile; resolve reported instantiation warnings.
3. Obtain bounded aggregate live-demo authorization. Strict Codex CLI token-cap
   capability is not validated. Best-effort execution needs explicit consent.
4. Validate live access to gpt-6-astra; cached model metadata and authenticated
   login are inventory evidence only.
5. Review the learned release before publication/application. No release is approved.

There is deliberately no fabricated live-demo recovery command: the live-demo
adapter is not implemented yet. Implement it before documenting an executable
M07 command. Available real preparation commands in this checkout are:

```sh
./inspecta-scp onboard
./inspecta-scp --json doctor
./inspecta-scp --json check --offline --config workbench/profiles/producer-consumer.check.json
```

The worker needs Linux namespace permissions. Run the check from the normal user
terminal if the outer Codex sandbox denies nested namespace creation; retain the
Workbench sandbox. Never enable an unsandboxed fallback.
