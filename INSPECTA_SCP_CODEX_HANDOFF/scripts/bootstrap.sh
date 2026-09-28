#!/usr/bin/env bash
# Reuse-first preparation. Default is a plan; no downloads, installs, or model calls.
# Python helper handles explicit paths, CODEX_BIN/SIREUM_HOME, capability checks,
# saved selections, user-local fallback installs, and local image reuse.
set -euo pipefail
base="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
command -v python3 >/dev/null || { echo 'BLOCKED: Python 3.10+ required.' >&2; exit 2; }
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 2)' || exit 2
exec python3 -B "$base/prepare_tools.py" "$@"
