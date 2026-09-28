# Selective checkpoint build verification — 27 September 2026

Scope: build and start the application from the selected Git files. No paid model calls, new engineering demonstrations, database migration or UI performance changes were performed.

Executed checks:

- Installed Python dependencies in a new isolated virtual environment and pinned the resolved dependency set in `workbench/requirements.lock`.
- Installed frontend dependencies from `package-lock.json`; TypeScript build passed.
- Application suite: 209 tests passed in the isolated checkout.
- Actual Firefox smoke: 35 checks passed using synthetic application fixtures.
- Exported the staged Git file set to an unrelated `/tmp` path, without `.venv`, `node_modules`, original SQLite state, tool binaries or untracked project inputs.
- Executed the documented `scripts/setup-workbench.sh` from that export; dependency installation and frontend build passed.
- Application suite from the clean export: 209 tests passed; `pip check` found no broken requirements.
- Started the actual `inspecta-scp ui --port 0` CLI from the clean export. Home, overview, Learning and Rulebooks HTTP endpoints returned 200 with the default starter profile and empty state. The temporary test server was stopped afterward.

Host tools reused: Python 3.11.11, Node 10.19.0, npm 6.14.4 and Firefox. This validates this host's application setup, not every supported operating system or a production multi-user deployment. See `docs/DEPENDENCIES.md` for the legacy Node limitation and separately required engineering tools.

Public export review: source selection and inherited remote history were scanned for common credential/key patterns and forbidden private-state/cache paths. No pattern matches were found. This is not a guarantee that all sensitive content can be detected automatically; the exact selection remains subject to owner review before pushing.

Original source tree, HEAD and index were preserved. Existing public remote history is inherited. Draft rulebook records retain draft status; source/evidence references point to the private provenance archive and do not grant verification or release acceptance.
