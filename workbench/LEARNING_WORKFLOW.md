# Learning and development workflow

Open the local Workbench and choose **Learning**. The saved FAA/Monitor training split and the approved requirement-based unit definition are selected when available. The stored approval applies to that exact revision; editing creates a new reviewable revision.

1. Select a context folder or upload PDF/text/Markdown/JSON documents. Context is separate from worked training examples and held-out implementations. PDF extraction uses the existing `pdftotext` in an isolated worker.
2. Select training and validation source passages. Review membership, source revisions, and cosine-distance ε. Matching means `1 − cosine_similarity <= ε`, default 0.1 and maximum 0.3. The current representation uses lexical token counts, not semantic embeddings.
3. Approve the exact split, then extract one batch or all remaining context batches using an authorized campaign. Completed batches are skipped on resume. Use **Pause model work** to interrupt an active call and stop subsequent batches; the clock continues, and **Resume model work** preserves all usage. Drafts preserve source provenance and model confidence. Extraction does not validate or publish a rule.
4. Ask Astra to suggest a unit definition, edit it, and approve it. The current approved definition counts one atomic requirement with its assumptions and guarantees or structural constraints. Structural conformance and behavioral proof have separate counts. A reviewed mapped inventory is still needed before coverage can be reported.
5. Prepare a development task: choose the learned rule, held-out target, shared files, and English requirements. The target implementation is evaluator-only. Shared syntax guidance and required external interfaces must be sufficient for the task. Review and approve this concrete scope.
6. Generate and run declared gates. Inspect the generated file, original golden, actual tool output, and architecture comparison. Parser success or text similarity does not establish behavioral correctness.
7. On failure, **Repair generated model using its tool diagnostics** creates another isolated generation. **Propose a rule revision from this failure** creates a new draft rule. Both consume the same campaign allowance and retain prior results. Use **Prepare refined-rule test** to review a revision on the same English task and validation reference; this retains repair lineage. Select a distinct approved held-out validation split when testing Monitor-trained rules against another KSU project. Golden text and graph differences are excluded from these model requests.
8. A frozen User release still requires validated supporting/contrasting transfer evidence and release approval. Those acceptance adapters are incomplete; current drafts cannot be published as verified releases.

CLI and UI use the same services. These read-only commands work from the repository root:

```sh
./inspecta-scp onboard
./inspecta-scp --json learning catalog
./inspecta-scp learning extract --help
./inspecta-scp learning extract-remaining --help
./inspecta-scp learning prepare-validation --help
./inspecta-scp learning validate --help
./inspecta-scp --json trace b47d2bfc9a884b539fe8e3d6755ad7ee
```

To reopen the UI on an available port:

```sh
./inspecta-scp ui --port 8767 \
  --profile workbench/profiles/isolette.check.json \
  --profile workbench/profiles/producer-consumer.engineering.check.json \
  --profile reports/demo/isolette-migrated-reference.profile.json
```

Open the private localhost URL printed by that command. Its token authorizes the local UI; it is not an OpenAI password. Saved provider credentials stay in the isolated model transport and are not passed to engineering tools. SHA-256 values identify the exact reviewed files and evidence; normal UI operation does not require typing them.

Paid replay requires a campaign with remaining time and tokens. With actual approved IDs, the CLI forms are:

```sh
./inspecta-scp learning extract --plan PLAN_ID --campaign CAMPAIGN_ID --batch-index 0
./inspecta-scp learning validate --task TASK_ID --campaign CAMPAIGN_ID
./inspecta-scp learning validate --task TASK_ID --campaign CAMPAIGN_ID --previous-result FAILED_RESULT_ID
./inspecta-scp learning refine --candidate CANDIDATE_ID --development-result FAILED_RESULT_ID --campaign CAMPAIGN_ID
```

Placeholders are identifiers from the catalog, not literal executable examples. An exhausted campaign is rejected; retrying never renews its allowance. Best-effort accounting separates measured usage, reservations and explicitly authorized estimates for failures without usage totals. Actual billing is not inferred.

The live evidence is in `reports/demo/DEMO_REPORT.md`. Application tests and synthetic boundary tests are identified separately from real model and engineering results. Existing source projects and original rulebooks are preserved.

Read the latest actual Isolette result without spending tokens:

```sh
./inspecta-scp --json learning inspect-validation --result 46099f1c2bc9e5ca7a4592b46d7333685886cad1e724f4fd456201994e23ab17
```

This replays saved evidence, not a fresh engineering execution. Inspect the full gate output through **View runs and results**; the Learning page displays generated and golden source and comparison results. A refined-rule test stays pending until its exact task is approved. Reusing a failed result preserves the repair allowance.


Readable learned books and KSU stage locations are documented in [KSU_WORKFLOWS.md](KSU_WORKFLOWS.md).
In Learning, use **Export versioned learned rulebook**, expand its snapshot, then
**Read learned book**. Exports are immutable draft snapshots, not User releases.
Choose the extraction focus explicitly when seeking whole-system architecture or
workflow rules; previous generic batches do not count as coverage of those focuses.

From a development result, inspect its evidence and choose **Compare directed
architecture graphs ignoring names**. Saved graph assessments are also selectable.
See [GRAPH_EQUIVALENCE.md](GRAPH_EQUIVALENCE.md) for the precise scope, known gaps and
why cosine assistance cannot establish behavior correctness. Historical exact
syntax differences remain available, clearly labeled separately.

Data preparation now precedes new rule extraction. In **Learning → Data preparation**,
select the already approved materials, choose existing English or extract missing
English, then review the source-linked document. The Miller guidebook controls
presentation only; KSU remains the engineering workflow. Validation selects the
reviewed English from this stage and supplies it with the selected rules to
formalization. See [DATA_PREPARATION.md](DATA_PREPARATION.md). Existing learned books
and demonstration records remain historical, not silently relabeled as outputs of
this new stage.
