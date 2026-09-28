# Data preparation before learning and validation

The pipeline is: select and approve materials/split → prepare English descriptions
and requirements → learn from training English/model pairs → formalize held-out
English with rules → execute KSU gates → learn/generalize/specialize patterns and
repair strategies → validate revisions → review publication. User releases stay frozen.

KSU supplies the engineering workflow. The Miller/FAA guidebook supplies the English
writing style; it does not override KSU or supply missing facts about a system.
The preparation prompt asks for supported system purpose/boundary, atomic identified
requirements, conditions, quantities/units, initialization/state, assumptions and
unresolved questions. Unknown behavior and timing bounds must not be invented.

In the UI choose **Learning → Data preparation**. The latest approved material split
is preselected. Choose a training or validation component and its approved style
guide. Extract missing English with Astra, paste existing English, or select an exact
line range from an approved context document without a model call. Unchanged
source excerpts inherit the existing source authorization, explicitly recorded as
source reuse only. Edits and model interpretations require their own review. Edit the document if necessary, save a revision, and review its exact
content. Source line ranges and quotations remain available for human checking;
matching a quotation does not establish that the English interpretation is faithful.

Models longer than120 source lines are processed in bounded100-line obligation windows,
with the full selected model supplied only as interpretation context. Successful
batches are retained for resume; a failed batch leaves preparation incomplete.
The combined document remains subject to completeness and fidelity review.

New rule extractions require reviewed English for every training item. They receive
those English documents, their original training models, and approved guide/workflow
context. Prepared validation English and validation models are excluded. Prior
extractions remain historical; they do not count as completed batches for a new
prepared-English revision.

For validation choose **Reviewed prepared English for validation**. The controller
binds its identity to the exact split, role and golden source hash. A changed or
revoked English revision blocks execution. Formalization receives the reviewed
English plus selected rules and permitted shared context; source quotations and the
golden model are excluded. Existing task records retain their older provenance.
Legacy CLI tasks supplying explicit English remain supported; the guided UI routes
new tasks through preparation.

Preparation of a validation description intentionally sees the selected source.
That is explicitly recorded as model-derived reconstruction data. It is not evidence
of transfer from independent stakeholder English. Final-transfer references remain
outside this development preparation API.

Readable immutable outputs live at
`.scp-workbench/app/prepared-data/<revision>/requirements.md` and `provenance.json`.
SQLite records bind the proposal, model call, exact source, source claims, English
revision, usage and review. These files are not original rulebooks or User releases.

CLI commands (same services as the UI):

```sh
./inspecta-scp learning prepare-data --help
./inspecta-scp learning revise-prepared-data --help
./inspecta-scp --json learning prepare-data --plan PLAN --role training \
  --item-index 0 --style-context GUIDE_DOCUMENT --campaign CAMPAIGN
./inspecta-scp --json learning prepare-data --plan PLAN --role validation \
  --item-index 0 --existing-english /path/to/requirements.md
```

Preparation does not reset repair counts, publish a rule, prove requirements,
replace source files, or authorize changing a system constraint. Training Mode may
propose workflow/meta-rule revisions from actual outcomes; acceptance gates remain
in force and benefit must be measured rather than assumed.

For this live material selection, the FAA guidebook already supplies Isolette
English: Monitor lines5086–5317 and Regulator lines4811–5085 in the registered
text extraction. These are retained as primary English. The model-derived drafts
are supplementary and cannot silently replace guidebook obligations absent from
the model (such as Regulator heat-command retention). Producer/Consumer uses the
model-derived English case authorized by the user.
