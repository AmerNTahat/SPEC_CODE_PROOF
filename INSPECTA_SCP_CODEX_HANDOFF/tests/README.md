# tests

Purpose:
Automated tests for the supplied helper code. They do not establish that Astra, HAMR, Logika, Verus, live UI or end-to-end learning work.

How to use:
Read the file cards below. Start the overall workflow from the root HOW_TO_USE.md; do not execute every file.

## README.md

Open:
[README.md](README.md)

What it does:
Explain this directory and its immediate files.

Why it exists:
Provide a readable entry point and file rationale.

Status and limits:
Documentation.

## test_integrated_handoff.py

Open:
[test_integrated_handoff.py](test_integrated_handoff.py)

What it does:
Tests for bundled helper behavior and failure cases.

Why it exists:
Catch regressions in the support utilities.

Status and limits:
Executed within PACKAGE_VALIDATION scope; not full engineering tests.

## test_support_tools.py

Open:
[test_support_tools.py](test_support_tools.py)

What it does:
Tests for bundled helper behavior and failure cases.

Why it exists:
Catch regressions in the support utilities.

Status and limits:
Executed within PACKAGE_VALIDATION scope; not full engineering tests.

Return:
[Package README](../README.md)

## test_tool_reuse.py

Open:
[test_tool_reuse.py](test_tool_reuse.py)

What it does:
Tests executable selection, pinning, no-npm reuse, Sireum preservation, image reuse, and error handling.

Why it exists:
Prevent regressions that silently reinstall a working CLI or claim compatibility from discovery alone.

Status and limits:
Synthetic local tests; no live Codex, HAMR, Logika, Verus, Docker pull, or npm installation.
