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

Additional executed offline preparation (not a live demonstration):

- Seven real Producer/Consumer structural checks exercised unchanged models,
  wiring/contract failures and exact reviewed consistent renaming. See
  `reports/build/real-structure-integration.json`.
- A real bounded repair branch rejected a broken connection and checked its
  corrected child while preserving the original source and run result. See
  `reports/build/real-repair-integration.json`.
- The KSU Simple Isolette source emitted 12 port-direction warnings with both
  the reused March Sireum and a separate digest-checked August reference CLI.
  A disposable candidate moved direction annotations onto the 12 typed features;
  the reused March tool then passed type checking and architecture capture.
  This syntax migration remains provisional and unapproved, with no source
  promotion or behavioral-equivalence claim. See
  `reports/build/ksu-isolette-migration.json` for exact diffs and evidence.
- Offline metrics generated CSV/JSON and 18 plot files. A separate verifier
  validated a real DSSE signature made with an ephemeral test-only key, returning
  INCOMPLETE (exit 3) because engineering acceptance was not established.
  See `reports/build/real-reporting-integration.json`. No production trust setup
  or verified-unit denominator was inferred.

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
