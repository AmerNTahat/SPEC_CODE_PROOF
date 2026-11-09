# Human-approved heat-contract dependency amendment

Applies to the isolated Isolette heat-control repair only. Retain REQ-MHS-1 through REQ-MHS-5 and heat-history commit unchanged.

**Environmental premise:** The Lower Desired Temperature is strictly less than the Upper Desired Temperature whenever the heat-control compute contract is invoked.

**Rationale and citation:** FAA AR-08-32 EA-OI-6 discusses desired-bound ordering and warns of ambiguous On/Off behavior with reversed bounds (PDF102/printedA11; extracted in reports/demo/behavior-review/PREPARED_ENGLISH_WITH_DEPENDENCIES.md lines426–430). Original golden Regulate.sysml lines384–393 has conflicting guards when that dependency is absent. The user approved this strict-ordering correction and its separate human-curated golden-defect classification.

**Scope:** This is the reviewed dependency amendment to the selected heat English. It is not a silent replacement of the earlier English preparation or approval of all pending FAA amendments. The precise possible one-degree margin is not asserted here. Producer/system enforcement must still be proved or declared as an explicit environmental assumption at the system boundary.
