#!/usr/bin/env python3
"""Read-only host inventory by default. Does not install, read credentials, or call models."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from typing import Any
sys.path.insert(0, str(Path(__file__).resolve().parent))
import tool_selection as toolsel

TOOLS = ("git", "python3", "node", "npm", "docker", "codex", "sireum", "cargo", "rustc", "cargo-verus", "make")
# Only simple version commands, explicitly requested; Sireum may bootstrap/download, so is not invoked here.
PROBE = {k: ["--version"] for k in ("git", "python3", "node", "npm", "docker", "codex", "cargo", "rustc", "make")}

def inventory(probe: bool = False, *, codex: str | None = None, sireum: str | None = None,
              sireum_home: str | None = None, selection_file: Path | None = None,
              codex_version: str = toolsel.DEFAULT_CODEX_VERSION, probe_sireum: bool = False,
              search_dirs: list[Path] | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "artifact_kind": "HOST_PREFLIGHT_NOT_TOOLCHAIN_VALIDATION",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "host": {"system": platform.system(), "machine": platform.machine(), "python": platform.python_version()},
        "disk_free_bytes_at_cwd": shutil.disk_usage(Path.cwd()).free,
        "tools": {}, "model_calls": 0, "installations_performed": False,
        "capabilities": {"astra_access": "NOT_CHECKED", "sireum_profile": "NOT_RUN", "docker_daemon": "NOT_CHECKED", "hard_token_cap": "UNKNOWN"},
    }
    saved=toolsel.read_selection(selection_file or toolsel.selection_path())
    for name in TOOLS:
        selected=[]
        if name in ('codex','sireum'):
            selected=toolsel.discover(name,codex if name=='codex' else sireum,
                                     sireum_home=sireum_home,saved=saved)
        path = selected[0]['path'] if selected else shutil.which(name)
        item: dict[str, Any] = {"found_on_path": path is not None, "path": path, "probe": "NOT_RUN"}
        if selected:
            item.update(candidates=selected, found_on_path=any(r['source']=='PATH' for r in selected),
                        found_existing=True, selection_source=selected[0]['source'])
        if name=='codex' and selected and probe:
            chosen,checked=toolsel.choose_codex(selected,codex_version)
            item.update(probe='COMPLETED', checks=checked, selected=chosen,
                        status='REUSE_CLI_READY' if chosen else 'BLOCKED')
            if chosen:item['path']=chosen['path']
        elif name=='sireum' and selected:
            sireum_result=toolsel.inspect_sireum(selected[0],allow_probe=probe_sireum)
            item.update(sireum=sireum_result,probe=sireum_result['probe'])
        elif path and probe and name in PROBE:
            try:
                # Do not pass model tokens to version subprocesses. Never inspect auth files.
                env = dict(os.environ)
                for key in ("OPENAI_API_KEY", "CODEX_API_KEY", "ANTHROPIC_API_KEY", "GITHUB_TOKEN", "GH_TOKEN"):
                    env.pop(key, None)
                run = subprocess.run([path, *PROBE[name]], capture_output=True, text=True, timeout=10, check=False, env=env)
                item.update(probe="COMPLETED", returncode=run.returncode,
                            version_output=(run.stdout+run.stderr).strip()[:1000])
            except (OSError, subprocess.TimeoutExpired) as exc:
                item.update(probe="FAILED", error=type(exc).__name__)
        result["tools"][name] = item
    result["notes"] = ["PATH discovery does not prove installation compatibility or authentication.",
                       "Sireum is not executed unless --probe-sireum is explicitly supplied; unbuilt checkouts are preserved.",
                       "No environment values, auth files, repositories, or private model context are collected."]
    result['tool_selection_policy']='REUSE_EXISTING_FIRST'
    result['codex_expected_version']=codex_version
    result['download_candidates']=toolsel.discover_downloads(search_dirs or [])
    result['notes'].append('Codex CLI readiness is not authentication, Astra access, or completed engineering validation.')
    return result

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", action="store_true", help="Run installed simple --version commands (no Sireum/bootstrap/model invocation).")
    parser.add_argument("--output", type=Path, help="Create new report; no overwriting.")
    parser.add_argument('--codex'); parser.add_argument('--sireum'); parser.add_argument('--sireum-home')
    parser.add_argument('--tool-selection',type=Path)
    parser.add_argument('--codex-version',default=toolsel.DEFAULT_CODEX_VERSION)
    parser.add_argument('--search-dir',action='append',type=Path,default=[])
    parser.add_argument('--probe-sireum',action='store_true',help='Explicitly allow initialized Sireum version/HAMR help probes, which may initialize dependencies; does not run engineering smoke tests.')
    args=parser.parse_args(argv)
    try:
        report=inventory(args.probe,codex=args.codex,sireum=args.sireum,sireum_home=args.sireum_home,
                         selection_file=args.tool_selection,codex_version=args.codex_version,
                         probe_sireum=args.probe_sireum,search_dirs=args.search_dir)
    except (ValueError,OSError) as exc:
        print('BLOCKED: '+str(exc),file=sys.stderr); return 2
    text=json.dumps(report, indent=2)+"\n"
    try:
        if args.output:
            with args.output.open("x", encoding="utf-8") as f: f.write(text)
        else: sys.stdout.write(text)
    except OSError as exc:
        print(f"Cannot write report: {exc}", file=sys.stderr); return 2
    return 0
if __name__ == "__main__": raise SystemExit(main())
