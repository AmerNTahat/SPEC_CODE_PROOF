"""CLI client for the shared Workbench services. No implicit paid execution."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from .config import PolicyError, resolve
from .controller import Controller
from .storage import sha_file
from .vendor.local_compare import compare_text
from .vendor.split_dataset import assign, approve


def read_json(path):
    return json.loads(Path(path).read_text())


def parser():
    p = argparse.ArgumentParser(prog="inspecta-scp", description="INSPECTA/SCP controller foundation; see onboard for capability status")
    p.add_argument("--state-dir", type=Path, default=Path(".scp-workbench/app"))
    p.add_argument("--json", action="store_true", help="Emit the same structured result used by clients")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("onboard", help="Show implemented capabilities and remaining gates")
    sub.add_parser("doctor", help="Inspect selected local tools without installing or invoking models")
    config = sub.add_parser("resolve", help="Resolve configuration without creating a run")
    config.add_argument("--config", type=Path, required=True)
    config.add_argument("--time-limit-seconds", type=int)
    config.add_argument("--token-limit", type=int)
    for name in ("check", "run", "learn"):
        q = sub.add_parser(name)
        q.add_argument("--config", type=Path, required=True)
        q.add_argument("--time-limit-seconds", type=int)
        q.add_argument("--token-limit", type=int)
        q.add_argument("--prepare-only", action="store_true")
        if name == "check":
            q.add_argument("--offline", action="store_true", help="No model calls or downloads (also the default)")
    for name in ("status", "report", "logs", "pause", "resume", "stop", "execute"):
        q = sub.add_parser(name)
        q.add_argument("run_id")
    q = sub.add_parser("compare", help="Offline lexical comparison; never acceptance")
    q.add_argument("left", type=Path)
    q.add_argument("right", type=Path)
    q = sub.add_parser("dataset", help="Lineage grouping of reviewed metadata; no semantic independence claim")
    q.add_argument("action", choices=("inspect", "propose", "approve"))
    q.add_argument("--input", type=Path, required=True)
    q.add_argument("--fractions", type=float, nargs=3)
    q.add_argument("--seed", default="0")
    q.add_argument("--reviewer")
    return p


def dispatch(args):
    if args.command == "onboard":
        return {"status": "IMPLEMENTATION_IN_PROGRESS", "paid_execution": "DISABLED",
                "implemented": ["config resolution", "allowlisted snapshots", "durable runs/events",
                                "pause/stop requests", "resume without resetting budgets", "typecheck adapter",
                                "lexical diagnostics", "metadata-level dataset proposals"],
                "remaining": ["generation/learning isolation", "rulebook import/release service", "transactional repairs",
                              "proof/build and architecture adapters", "React UI", "attestation", "live demonstrations"],
                "start": "./inspecta-scp --json doctor; ./inspecta-scp --json check --offline --config workbench/profiles/producer-consumer.check.json",
                "limits": "Nested worker isolation may be unavailable in this Codex sandbox. Failure blocks; it never runs without isolation."}
    if args.command == "doctor":
        repo = Path(__file__).resolve().parents[2]
        sireum = os.environ.get("SIREUM_BIN") or (str(Path(os.environ["SIREUM_HOME"]) / "bin/sireum") if os.environ.get("SIREUM_HOME") else None)
        paths = {"codex": os.environ.get("CODEX_BIN", str(repo / "codex-155")), "sireum": sireum,
                 "python": sys.executable, "worker_sandbox": str(repo / "tools/codex-runtime-v0.155.1/codex-resources/bwrap")}
        return {"status": "INVENTORY_ONLY", "tools": {key: {"path": value,
                    "exists": bool(value and Path(value).is_file()),
                    "sha256": sha_file(value) if value and Path(value).is_file() else None}
                    for key, value in paths.items()}, "model_calls": 0,
                "engineering_compatibility": "NOT_ESTABLISHED", "hard_token_cap": "NOT_VALIDATED",
                "installations": 0}
    if args.command == "compare":
        return compare_text(args.left.read_bytes().decode(), args.right.read_bytes().decode())
    if args.command == "dataset":
        data = read_json(args.input)
        if args.action == "approve":
            return approve(data, args.reviewer or "")
        return assign(data, "propose_grouped" if args.action == "propose" else "user_assigned", args.fractions, args.seed)
    if args.command in {"check", "run", "learn", "resolve"}:
        overrides = {}
        if args.command == "check":
            overrides["task_operation"] = "verify-only"
        elif args.command == "learn":
            overrides["mode"] = "learning"
        if args.time_limit_seconds is not None:
            overrides.setdefault("budget", {})["wall_seconds"] = args.time_limit_seconds
        if args.token_limit is not None:
            overrides.setdefault("budget", {})["aggregate_model_tokens"] = args.token_limit
        profile = read_json(args.config)
        base = args.config.resolve().parent
        if args.command == "resolve":
            return resolve(profile, overrides, base)
    controller = Controller(args.state_dir)
    try:
        if args.command in {"check", "run", "learn"}:
            run = controller.create(profile, overrides, base)
            return run if args.prepare_only else controller.execute(run["id"])
        if args.command in {"status", "report"}:
            return controller.status(args.run_id)
        if args.command == "logs":
            return {"events": controller.store.events(args.run_id)}
        if args.command == "execute":
            return controller.execute(args.run_id)
        return controller.control(args.run_id, args.command)
    finally:
        controller.close()


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        result = dispatch(args)
        print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
        return {"FAILED": 1, "BLOCKED": 3, "BUDGET_EXHAUSTED": 4,
                "CANCELLED": 5}.get(result.get("state"), 0)
    except (PolicyError, OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"status": "CONFIGURATION_ERROR", "error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
