# Package guide and responsibilities

One user entry point:
`start.py`, with instructions in HOW_TO_USE.md. You do not execute every file.

Why there are multiple files:
Implementation goals, runtime workflow definitions, typed schemas, prompts, local utilities, tests and visual references have different responsibilities. One giant prompt would duplicate content on every model call and obscure which parts are executable. Directory READMEs explain individual files in multiline cards.

Authoritative workflow:
WORKFLOW_CONTRACT.md and workflow_goals/ define mode behavior and configuration. The master/focused goals define how to build it. Config files are drafts; they are not authorized runnable data. Prompts operate on narrow relevant context; rulebooks provide knowledge; controller code owns enforcement. Archive copies are inactive history.

Support utilities:
Executable helper code is real and tested within PACKAGE_VALIDATION scope. The split helper consumes reviewed metadata; it does not automatically discover semantic independence. The source catalog is not a trained library or a live importer. Metric tools consume normalized records, not raw proof evidence. The launcher invokes Codex rather than building the software by itself.

Installation:
prepare can obtain a current official Codex package or the reference container, with consent. Full Sireum/current-compatible engineering integration is M01 and is validated on the target workstation. Goal installation is a separate expected-hash operation. Neither support operation proves the engineering environment works.

Demonstrations:
ui/ and walkthrough/ are reference assets. support-demo is synthetic and free of model calls. M07 requires a LIVE Isolette/KSU demonstration with actual evidence, followed by a recorded replay captured from that live run. Do not mix these categories.

Reporting:
At every milestone and blocker print achieved/in-progress/remaining/evidence/budget. User runtime cycles emit the same structure through UI/CLI. Unknown evidence remains unknown. Cost savings are an empirical outcome, not a promised implementation result.

## Installation policy update — v2.1
Reuse the downloaded Codex v_155 and suitable existing Sireum before any installation. Supply executable paths through launcher arguments or CODEX_BIN/SIREUM_HOME. Only missing approved dependencies need KSU setup. [Reuse-first instructions](installation/REUSE_EXISTING_TOOLS.md) supersede earlier generic latest/fresh-install wording.
