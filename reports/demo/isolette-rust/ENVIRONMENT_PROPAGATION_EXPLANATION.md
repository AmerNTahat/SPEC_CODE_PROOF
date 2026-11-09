# What it means to propagate an environmental assumption

The user's additional25-minute window is recorded in ENVIRONMENT_PROPAGATION_TIME_EXTENSION.json. No stronger assumption or change to the accepted heat repair was inferred from the question.

An approved environmental assumption can be used throughout the proof wherever it refers to the same quantities. We do not need software to prove the external world obeys it. Copying or renaming a quantity does not require inventing a new environmental assumption.

The PDF distinguishes two quantities:

- External Desired Temperature Range: ordered by EA-OI-6, explicitly an environmental assumption (PDF102/printedA11).
- Internal Desired Range: copied from the external range when Regulator Interface Failure is False (REQ-MRI-8). When that flag is True, the internal range is UNSPECIFIED and should not be used (REQ-MRI-9, PDF108/printedA17).

The original PDF page was re-extracted into FAA_MRI_PAGE_A17.txt. This is also present in the exact selected generation English at lines143–151. The generated Regulate contract reflects MRI8 conditionally; its MRI9 documentation explicitly preserves unspecified failure outputs. Thus globally assuming every internal output is ordered would strengthen the model beyond the external premise and could hide an implementation or invalid-data-use defect.

## Executed diagnostic

CVC5 checked a manual transcription of the environmental ordering, MRI8 and the internal TableA7 domains:

1. Healthy interface, copying the same values, but unordered internal output: **UNSAT**. Under the copying contract, the approved assumption already gives the desired result.
2. Failed interface, external97<100 and internal101/97: **SAT**. Those internal values lie in TableA7 domains and MRI9 does not constrain them to be ordered.

Commands, outputs and times are in ENVIRONMENT_PROPAGATION_DIAGNOSIS.json. This is a contract-level diagnostic, not proof that a running Isolette actually produces or consumes this bad pair. It does not establish scheduling reachability or a whole-system failure.

## Consequence for validation

Keep EA-OI-6 as an approved environmental premise, available wherever the same operator settings are referenced. The remaining internal check is narrowly about the validity/copying path: can the heat controller consume unspecified internal bounds during initialization/interface failure? The local heat proof still succeeds under its explicitly approved ordered-input premise. That premise does not itself prove the system never passes unspecified values to it.

Possible conforming implementations can preserve an ordered fallback during unspecified states, or prevent the consumer from using those values. No such new implementation or stronger assumption was silently applied in this investigation. Original golden, current checked repair, accepted case count and all proof results remain unchanged.

No paid calls were made. The campaign cap remains14M, charged6,256,540 (1,256,540measured +5Mestimated), continuation remaining1,737,838. M07 remains in progress.
