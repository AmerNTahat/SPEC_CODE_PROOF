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
from .approvals import Approvals
from .knowledge import Knowledge
from .sources import Sources
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
    q = sub.add_parser('datasets', help='Review manual or seeded lineage-grouped dataset assignments')
    actions = q.add_subparsers(dest='dataset_action', required=True)
    a = actions.add_parser('propose'); a.add_argument('--input', type=Path, required=True)
    actions.add_parser('catalog')
    a = actions.add_parser('request-review'); a.add_argument('dataset_id')
    a = actions.add_parser('register', help='Register an explicit source allowlist without copying it to an agent')
    a.add_argument('--directory', type=Path, required=True)
    a.add_argument('--role', choices=('learning', 'development', 'evaluator'), required=True)
    a.add_argument('--files', nargs='+', required=True)
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
    q = sub.add_parser("rules", help="Import, inspect and review versioned knowledge without model calls")
    actions = q.add_subparsers(dest="rule_action", required=True)
    a = actions.add_parser("import")
    a.add_argument("--directory", type=Path, required=True)
    actions.add_parser("catalog")
    for name in ("propose", "forecast"):
        a = actions.add_parser(name)
        a.add_argument("--input", type=Path, required=True)
    a = actions.add_parser("retrieve")
    a.add_argument("--query", required=True)
    a.add_argument("--operation", required=True)
    a.add_argument("--profile", required=True)
    a.add_argument("--release")
    a = actions.add_parser("review")
    a.add_argument("candidate_id")
    a.add_argument("--supporting-run", required=True)
    a.add_argument("--contrasting-run", required=True)
    a = actions.add_parser("draft-release")
    a.add_argument("candidate_ids", nargs="+")
    a = actions.add_parser("request-publication")
    a.add_argument("draft_id")
    a = actions.add_parser("publish")
    a.add_argument("draft_id")
    a.add_argument("--approval", required=True)
    a = actions.add_parser("show-release")
    a.add_argument("release_id")
    q = sub.add_parser("source", help="Read an exact registered source revision")
    q.add_argument("source_id")
    q.add_argument("--audience", choices=("human", "generator"), default="human")
    q.add_argument("--start", type=int, default=1)
    q.add_argument("--end", type=int)
    q = sub.add_parser("approval", help="Local human review; never implicit model approval")
    q.add_argument("request_id")
    q.add_argument("--decision", choices=("APPROVED", "REJECTED", "REVOKED"))
    q.add_argument("--expected-digest")
    q.add_argument("--reviewer")
    q = sub.add_parser("budget", help="Request/apply an exact approved budget amendment")
    q.add_argument("run_id")
    q.add_argument("--token-limit", type=int)
    q.add_argument("--wall-seconds", type=int)
    q.add_argument("--approval")
    q = sub.add_parser("registry", help="Declare and review proof-bearing units before a run")
    actions = q.add_subparsers(dest="registry_action", required=True)
    a = actions.add_parser("propose")
    a.add_argument("--input", type=Path, required=True)
    a = actions.add_parser("request-review")
    a.add_argument("registry_id")
    q = sub.add_parser("metrics", help="Current metrics from actual run evidence")
    q.add_argument("run_id")
    q = sub.add_parser("plot", help="Export actual run metrics as CSV/JSON and PNG/SVG/PDF")
    q.add_argument("run_id")
    q.add_argument("--output", type=Path, required=True)
    q.add_argument("--no-plots", action="store_true")
    q = sub.add_parser("attest", help="Local signed evidence; independent policy and trust required")
    actions = q.add_subparsers(dest="attest_action", required=True)
    a = actions.add_parser("policy")
    a.add_argument("run_id")
    a.add_argument("--scope", choices=("record_integrity", "engineering_acceptance"), default="record_integrity")
    a = actions.add_parser("create")
    a.add_argument("run_id")
    a.add_argument("--key", type=Path, required=True)
    a.add_argument("--policy", type=Path, required=True)
    a.add_argument("--output", type=Path, required=True)
    a = actions.add_parser("verify")
    a.add_argument("--bundle", type=Path, required=True)
    a.add_argument("--policy", type=Path, required=True)
    a.add_argument("--trust", type=Path, required=True)
    q = sub.add_parser("repairs", help="Bounded provisional repair branches; never edit original source")
    actions = q.add_subparsers(dest="repair_action", required=True)
    a = actions.add_parser("stage")
    a.add_argument("run_id")
    a.add_argument("--issue", required=True)
    a.add_argument("--patch", type=Path, required=True)
    a.add_argument("--parent")
    a = actions.add_parser("validate")
    a.add_argument("candidate_id")
    a = actions.add_parser("catalog")
    a.add_argument("--run-id")
    q = sub.add_parser("architecture", help="Capture and review real HAMR structural baselines")
    actions = q.add_subparsers(dest="architecture_action", required=True)
    a = actions.add_parser("snapshot")
    a.add_argument("snapshot_id")
    a = actions.add_parser("propose")
    a.add_argument("snapshot_id")
    a.add_argument("--changes", type=Path)
    a = actions.add_parser("request-review")
    a.add_argument("policy_id")
    q = sub.add_parser("requirements", help="Source-backed obligation ledger and independent review")
    actions = q.add_subparsers(dest="requirements_action", required=True)
    a = actions.add_parser("propose")
    a.add_argument("--input", type=Path, required=True)
    for name in ("show", "request-review"):
        a = actions.add_parser(name)
        a.add_argument("ledger_id")
    q = sub.add_parser("ui", help="Open the authenticated loopback UI over the same controller")
    q.add_argument("--port", type=int, default=8765)
    q.add_argument("--profile", type=Path, action="append", default=[])
    q.add_argument("--library-root", type=Path, action="append", default=[])
    return p


def dispatch(args):
    if args.command == "attest" and args.attest_action == "verify":
        from .verify_attestation import verify_files
        return verify_files(args.bundle, args.policy, args.trust)
    if args.command == "ui":
        from .api import serve
        repo = Path(__file__).resolve().parents[2]
        profiles = args.profile or sorted((repo / "workbench/profiles").glob("*.check.json"))
        roots = args.library_root or [repo / "isolette/sysml/rule-books", repo / "rule-books_7"]
        serve(args.state_dir, profiles, roots, args.port)
        return {"status": "STOPPED"}
    if args.command == "onboard":
        return {"status": "IMPLEMENTATION_IN_PROGRESS", "paid_execution": "DEFERRED_BY_USER",
                "implemented": ["config resolution", "allowlisted snapshots", "durable runs/events",
                                "pause/stop requests", "resume without resetting budgets", "typecheck adapter",
                                "lexical diagnostics", "reviewed lineage-grouped dataset assignments and source invalidation", "legacy rulebook import",
                                "registered source passages", "exact-subject approvals", "budget amendments",
                                "candidate rules, bindings and release drafts", "authenticated local React UI",
                                "real HAMR AIR/declaration capture and reviewed structural comparison",
                                "source-backed requirement ledgers and mapped coverage", "bounded provisional repairs",
                                "reviewed unit registries and metrics/plots", "independent local DSSE verification",
                                "isolated HAMR Slang/JVM generation and Logika connection integration checks"],
                "remaining": ["generation/learning isolation", "independent rule transfer validation and publication readiness", "accepted source promotion",
                              "complete proof/build/independent-test adapters", "cross-task learning execution", "production attestation trust setup", "live demonstrations"],
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
        if args.command == 'datasets':
            from .datasets import Datasets
            service = Datasets(controller.store)
            if args.dataset_action == 'register':
                sources = Sources(controller.store)
                root = sources.register_root(args.directory, args.role)
                return {'root': root, 'sources': [sources.register(root['id'], path) for path in args.files]}
            if args.dataset_action == 'propose': return service.propose(read_json(args.input))
            if args.dataset_action == 'catalog': return service.catalog()
            return service.request_review(args.dataset_id)
        if args.command in {"registry", "metrics", "plot"}:
            from .metrics import Metrics
            service = Metrics(controller)
            if args.command == "metrics":
                return service.report(args.run_id)
            if args.command == "plot":
                return service.export(args.run_id, args.output, not args.no_plots)
            if args.registry_action == "propose":
                return service.propose(read_json(args.input))
            return service.request_review(args.registry_id)
        if args.command == "attest":
            from .attestation import Attestations
            service = Attestations(controller)
            if args.attest_action == "policy":
                return service.policy(args.run_id, args.scope)
            return service.create(args.run_id, args.key, read_json(args.policy), args.output)
        if args.command == "repairs":
            from .repairs import Repairs
            service = Repairs(controller)
            if args.repair_action == "stage":
                return service.stage(args.run_id, args.issue, read_json(args.patch), args.parent)
            if args.repair_action == "validate":
                return service.validate(args.candidate_id)
            return service.catalog(args.run_id)
        if args.command == "architecture":
            from .architecture import Architecture
            service = Architecture(controller)
            if args.architecture_action == "snapshot":
                return controller.store.read_record("architecture_snapshot", args.snapshot_id)
            if args.architecture_action == "propose":
                return service.propose(args.snapshot_id, read_json(args.changes) if args.changes else None)
            return service.request_review(args.policy_id)
        if args.command == "requirements":
            from .requirements import Requirements
            service = Requirements(controller.store)
            if args.requirements_action == "propose":
                return service.propose(read_json(args.input))
            if args.requirements_action == "show":
                return controller.store.read_record("requirement_ledger", args.ledger_id)
            return service.request_review(args.ledger_id)
        if args.command == "rules":
            library = Knowledge(controller.store)
            if args.rule_action == "import":
                return library.import_books(args.directory)
            if args.rule_action == "catalog":
                return library.catalog()
            if args.rule_action in {"propose", "forecast"}:
                return getattr(library, args.rule_action)(read_json(args.input))
            if args.rule_action == "retrieve":
                return {"matches": library.retrieve(args.query, args.operation, args.profile, args.release)}
            if args.rule_action == "review":
                return library.review(args.candidate_id, args.supporting_run, args.contrasting_run)
            if args.rule_action == "draft-release":
                return library.draft_release(args.candidate_ids)
            if args.rule_action == "request-publication":
                return library.request_publication(args.draft_id)
            if args.rule_action == "publish":
                return library.publish(args.draft_id, args.approval)
            return library.release(args.release_id)
        if args.command == "source":
            return Sources(controller.store).view(args.source_id, args.audience, args.start, args.end)
        if args.command == "approval":
            approvals = Approvals(controller.store)
            return (approvals.decide(args.request_id, args.expected_digest, args.decision, args.reviewer)
                    if args.decision else approvals.get(args.request_id))
        if args.command == "budget":
            return (controller.amend_budget(args.run_id, args.approval) if args.approval else
                    controller.request_budget(args.run_id, args.token_limit, args.wall_seconds))
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
                "CANCELLED": 5, "INCOMPLETE": 3}.get(result.get("state", result.get("status")), 0)
    except (PolicyError, OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"status": "CONFIGURATION_ERROR", "error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
