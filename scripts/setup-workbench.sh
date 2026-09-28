#!/bin/sh
set -eu
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$repo_dir"
python_bin=${INSPECTA_PYTHON:-python3}
"$python_bin" -c 'import sys; assert sys.version_info >= (3,11), "Python 3.11+ required; set INSPECTA_PYTHON"'
if [ ! -x .venv/bin/python ]; then "$python_bin" -m venv .venv; fi
.venv/bin/python -m pip install -r workbench/requirements.lock
cd workbench/frontend
npm ci --ignore-scripts --no-audit --no-fund
npm run build
