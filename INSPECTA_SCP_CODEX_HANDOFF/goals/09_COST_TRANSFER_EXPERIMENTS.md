# Evidence-backed evaluation and DASC-style visualization

## Existing sources to migrate

Inspect, do not blindly reuse:
`SCP-extention-artificats/isolette_io_extnded/tools/evaluate_plans.py`, `show_codex_metrics.py`, `visualize_metrics.py`, `self_adapt.py`, and demo-artifact variants. Link exact revisions and fixes in a migration register.

Read the original DASC LaTeX metric definitions and `SCP_IEEE_Documentation/revision_round22_June_2026/figures/results_chart_pgfplots.tex`. Historical charts are historical data, not new evidence. Do not infer verification from a list of contracts or the phrase Verification succeeded. Do not treat a generic final_metric as tokens, missing runtimes as zero, or repeat plan labels as distinct restored snapshots.

## Unit registry

Declare benchmark version and target IDs before execution. A unit is a reviewed proof-bearing target linked to source obligations, specification targets, implementation methods and required formal gates. Reconstruct the historical 42-unit membership from evidence before claiming the DASC denominator; do not manufacture it from a reported count. Each KSU task uses its own scoped registry.

Verified unit:
At least one registered required formal obligation exists and all required formal checks passed for current artifacts under the declared profile. No timeout/unknown/skipped/stale unit counts.

Accepted unit:
Verified plus additional requirement-fidelity, architecture, independent test and review gates.

End-to-end success:
All required units accepted and project-level integration/build/policy gates pass. A pass of an incomplete contract is not full requirement validity.

Count unique units, not retries, methods accidentally duplicated, solver messages or test cases. Preserve stable IDs across renames. Invalidate affected units when dependencies change; live counts may decrease. Deliberately subdividing units cannot inflate throughput.

## Calculations

For fixed U, verified V, wall minutes T, normalized total tokens N and cost C:
coverage = |V|/|U|; throughput = |V|/T; tokens/unit = N/|V|; dollars/unit = C/|V|.

With zero verified units, per-unit values are undefined/null (not zero). Missing time/usage/cost is unknown. Normalize provider totals: cached input is usually a subset of total input and reasoning output may be part of total output. Record adapter version and raw categories. Do not sum overlapping categories. Prices are dated per-call assumptions; separate estimated equivalent cost from billing. Include all failed/retry/learning costs and avoid adding learning twice when the logged adjusted trace already contains it.

Compare matched target identities, not just equal counts. Different operation classes, toolchains, acceptance policies and partial verified subsets must be explicit. Record actual wall time rather than summing overlapping concurrent durations. Learning cost + sum of user costs is the total; report amortized reuse separately. Setup and cache warming are not hidden learning advantages.

## Plots and UI timing

Use Matplotlib for deterministic PNG/SVG/PDF exports, Plotly for interactive UI if useful, and one normalized metrics service for both CLI/UI. No agent calls to calculate or draw charts. Each exported figure has data/config/version provenance and a linked raw-data file.

Before execution:
Show registry, scope, budget, versions and missing prerequisites; no invented results.

During execution:
Show current verified/accepted counts versus time and tokens, usage, repairs, stale evidence and pending obligations. Label provisional data. Do not announce savings without a comparable baseline.

After each development cycle:
Show candidate rule results, applicability failures, confidence forecast versus observations and cost; do not call these final held-out results.

After termination including failures:
Persist report, units, usage, plots and unresolved gates.

After matched comparison:
DASC views: token classes, verified throughput, coverage, tokens/unit, dollars/unit. Additional plots: progress curves, learning/application cost and amortization, human interventions, lexical/structural diagnostics and rule/task-family transfer. Use separate axes/figures for quantities with unlike units. A conceptual acceptance cone stays labeled conceptual.

Click a chart -> contributing units -> requirements -> rule/binding -> model/code -> actual tool evidence. Respect evaluator access boundaries. PNG is static; HTML/report supplies navigation. Export CSV/JSON plus figure files and a source manifest.

## Experimental conditions

K0 static KSU; K1 same fixed knowledge with coded operations; S1 one-pass extracted rules; S2 development-refined rules. All may repair the current task; only persistence/evolution differs. Add summary/example retrieval controls and selected ablations. Hold model/toolchain/acceptance/budget/context permissions fixed, run fresh target sessions, repeat important comparisons and retain failures. Protect final evaluation and report limited transfer claims accurately.

## Starter-tool status

`scripts/evaluation_tools.py` provides a tested normalized-record calculator and local chart exporter. It does not parse HAMR/Logika results or prove units. `demos/synthetic-runs.json` is labeled synthetic and tests report plumbing only. Codex must implement trusted adapters and real trace ingestion before using this layer for engineering claims.
