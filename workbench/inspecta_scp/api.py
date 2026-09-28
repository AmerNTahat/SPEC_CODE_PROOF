"""Loopback HTTP client of shared services; no separate workflow engine."""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import json
from pathlib import Path
import re
import secrets
import threading
from urllib.parse import urlsplit, parse_qs

from .approvals import Approvals
from .config import PolicyError, defaults
from .controller import Controller
from .knowledge import Knowledge
from .sources import Sources


class Application:
    def __init__(self, state_dir, profiles, library_roots):
        self.state_dir = Path(state_dir).absolute()
        self.profiles = {p.stem: p.resolve() for p in map(Path, profiles)}
        if len(self.profiles) != len(profiles):
            raise PolicyError("Profile names must be unique")
        self.library_roots = {str(i): str(Path(p).absolute()) for i, p in enumerate(library_roots)}

    def call(self, method, route, body=None, query=None):
        body, query = body or {}, query or {}
        controller = Controller(self.state_dir)
        try:
            library = Knowledge(controller.store)
            if method == "GET" and route == "/api/overview":
                rows = controller.store.db.execute("SELECT id FROM runs ORDER BY created DESC LIMIT 50").fetchall()
                return {"runs": [controller.status(r[0]) for r in rows],
                        "profiles": [{"id": key, "config": json.loads(p.read_text())} for key, p in self.profiles.items()],
                        "library_roots": self.library_roots, "paid_execution": "AUTHORIZATION_REQUIRED_PER_CAMPAIGN",
                        "defaults": {mode: defaults(mode) for mode in ("user", "learning")},
                        "approvals": [Approvals(controller.store).get(r["id"]) for r in controller.store.records("approval")],
                        "capabilities": {"rule_import": True, "source_viewer": True, "prepare_run": True,
                                         "isolated_typecheck": True, "model_execution": True,
                                         "live_demo": False, "independent_transfer_validation": False}}
            if method == "GET" and route == "/api/library":
                return library.catalog()
            if route.startswith('/api/learning'):
                from .learning import Learning
                service = Learning(controller)
                if method == 'GET' and route == '/api/learning':return service.catalog()
                if route.startswith('/api/learning/evidence-review'):
                    from .evidence_review import EvidenceReview
                    review=EvidenceReview(controller)
                    if method=='GET':return review.catalog()
                    if method=='POST':
                        if route.endswith('/semantic-policy'):return review.set_semantic_policy(body.get('review_id'),body.get('max_distance'),body.get('reviewer'))
                        if route.endswith('/quick-decision'):return review.quick_decision(body.get('review_id'),body.get('targets'),body.get('action'),body.get('reviewer'),body.get('expected_fingerprint'),body.get('edits'),body.get('accept',False))
                        if route.endswith('/suggest'):return review.propose(body.get('result_id'),body.get('policy','partial'),body.get('note',''))
                        if route.endswith('/exclude'):return review.exclude(body.get('review_id'),body.get('target'),body.get('reason_code'),body.get('reason'),body.get('revisit'))
                        if route.endswith('/accept'):return review.accept(body.get('review_id'))
                        if route.endswith('/note'):return review.note(body.get('review_id'),body.get('text'),body.get('reviewer'))
                        if route.endswith('/repair'):return review.repair(body.get('review_id'),body.get('target'),body.get('campaign_id'))
                if route in {'/api/learning/rulebook-scope','/api/learning/rulebook-bulk-review','/api/learning/rulebook-scopes'}:
                    from .scoped_rulebooks import ScopedRulebooks
                    scoped=ScopedRulebooks(controller)
                    if method=='GET' and route.endswith('rulebook-scopes'):return scoped.catalog()
                    if method=='POST' and route.endswith('rulebook-scope'):return scoped.create(body.get('result_id'),body.get('title'),body.get('gates'))
                    if method=='POST' and route.endswith('rulebook-bulk-review'):return scoped.prepare_batch(body.get('scope_ids'),body.get('comment'))
                if method == 'POST' and route == '/api/learning/capability-scope':
                    from .capability_scope import CapabilityScope
                    return CapabilityScope(controller).propose(body['preparation_id'],body['tool_run_id'],body['items'])
                if method == 'POST' and route == '/api/learning/supplement-context':
                    from .data_preparation import DataPreparation
                    return DataPreparation(controller).supplement_context(body['preparation_id'],body['passages'],body['rationale'])
                if method == 'POST' and route in {'/api/learning/prepare-data','/api/learning/revise-prepared-data'}:
                    from .data_preparation import DataPreparation
                    preparation=DataPreparation(controller)
                    if route.endswith('revise-prepared-data'):return preparation.revise(body.get('proposal_id'),body.get('english'))
                    if body.get('english_context_id'):return preparation.prepare_from_context(body.get('plan_id'),body.get('role'),body.get('item_index'),body.get('english_context_id'),body.get('english_start'),body.get('english_end'))
                    return preparation.prepare(body.get('plan_id'),body.get('role'),body.get('item_index'),body.get('campaign_id'),body.get('style_context_id'),body.get('existing_english'))
                if method == 'POST' and route in {'/api/learning/context-inventory','/api/learning/context-select','/api/learning/context-upload'}:
                    from .context_materials import ContextMaterials
                    materials=ContextMaterials(controller.store)
                    if route.endswith('context-inventory'):return materials.inventory(body.get('directory'))
                    if route.endswith('context-select'):return materials.select(body.get('root_id'),body.get('files'))
                    return materials.upload(body.get('name'),body.get('base64'))
                if method == 'POST' and route == '/api/learning/examples':
                    from .config import resolve
                    profile=self.profiles.get(body.get('profile_id'))
                    if profile is None:raise PolicyError('Choose a registered example profile')
                    config=resolve(json.loads(profile.read_text()),{'dataset_assignment':None,'dataset_task':None},profile.parent)['config']
                    sources=Sources(controller.store);root=sources.register_root(config['project'],'learning')
                    files=[]
                    for name in config['input_files']:
                        if name.startswith('aadl-lib/'):continue
                        source=sources.register(root['id'],name);view=sources.view(source['id'])
                        files.append({'source_id':source['id'],'path':name,'lines':view['end_line'],'text':view['text']})
                    return {'files':files,'profile_id':body['profile_id'],'scope':'Human selection only; no model context exported'}
                if method == 'POST' and route in {'/api/learning/unit-suggest','/api/learning/unit-revise'}:
                    from .unit_definitions import UnitDefinitions
                    units=UnitDefinitions(controller.store)
                    return units.suggest(body.get('plan_id'),body.get('campaign_id')) if route.endswith('unit-suggest') else units.revise(body.get('proposal_id'),body.get('definition'))
                if method == 'POST' and route == '/api/learning/development-revise-rules':
                    from .development import Development
                    return Development(controller).revise_rules(body.get('result_id'),body.get('candidate_ids'))
                if method == 'POST' and route == '/api/learning/behavior-review':
                    from .behavior_acceptance import BehaviorAcceptance
                    return BehaviorAcceptance(controller).prepare(body.get('result_id'))
                if method == 'POST' and route == '/api/learning/development-graph':
                    from .development import Development
                    return Development(controller).compare_graph(body.get('result_id'))
                if method == 'POST' and route == '/api/learning/export-books':
                    return Knowledge(controller.store).export_learned_books()
                if method == 'GET' and route == '/api/learning/book':
                    return Knowledge(controller.store).read_learned_book(query.get('export_id',[''])[0])
                if method == 'POST' and route == '/api/learning/development-prepare':
                    from .development import Development
                    profile=self.profiles.get(body.get('profile_id'))
                    if profile is None:raise PolicyError('Choose a registered evaluation project')
                    return Development(controller).prepare(json.loads(profile.read_text()),body.get('target_file'),body.get('shared_files',[]),body.get('requirements'),body.get('candidate_ids'),body.get('plan_id'),profile.parent,body.get('validation_plan_id'),body.get('predecessor_task_id'),body.get('prepared_requirements_id'),body.get('revision_reason'),body.get('capability_scope_id'))
                if method == 'GET' and route == '/api/learning/development-result':
                    from .development import Development
                    return Development(controller).inspect(query.get('result_id',[''])[0])
                if method == 'POST' and route == '/api/learning/repair-guidance':
                    from .validation_repair import ValidationRepair
                    return ValidationRepair(controller).guidance(body.get('result_id'),body.get('suggestion'),body.get('reviewer'),body.get('expected_attempts'))
                if method == 'POST' and route in {'/api/learning/development-run','/api/learning/development-cycle'}:
                    from .development import Development
                    development=Development(controller)
                    action=development.validate_cycle if route.endswith('development-cycle') else development.generate_and_check
                    return action(body.get('task_id'),body.get('campaign_id'),body.get('previous_result_id'))
                if method == 'POST' and route == '/api/learning/refine':
                    return service.refine(body.get('candidate_id'),body.get('development_result_id'),body.get('campaign_id'))
                if method == 'POST' and route == '/api/learning/workflow-failure':
                    return service.learn_workflow_failure(body.get('plan_id'),body.get('campaign_id'),body.get('context_ids'),body.get('run_id'),body.get('generated_result_id'),body.get('strategy'),body.get('prior_candidate_id'))
                if method == 'POST' and route == '/api/learning/extract-remaining':
                    return service.extract_remaining(body.get('plan_id'),body.get('campaign_id'),body.get('focus','full_stack'))
                if method == 'POST' and route == '/api/learning/campaign-control':
                    from .campaign import Campaign
                    return Campaign(controller.store).control(body.get('campaign_id'),body.get('action'))
                if method == 'POST' and route == '/api/learning/extract':
                    return service.extract(body.get('plan_id'),body.get('campaign_id'),body.get('batch_index',0),focus=body.get('focus','full_stack'))
                if method == 'POST' and route == '/api/learning/plan':
                    from .learning_plan import LearningPlan
                    return LearningPlan(controller.store).propose(body.get('context_ids',[]),body.get('training'),body.get('validation'),body.get('epsilon',0.1))
                if method == 'POST' and route == '/api/learning/inspect':
                    profile = self.profiles.get(body.get('profile_id'))
                    library_directory = self.library_roots.get(body.get('library_root_id'))
                    if profile is None or library_directory is None:
                        raise PolicyError('Choose an inspected project and registered rulebook directory')
                    return service.inspect(json.loads(profile.read_text()), library_directory,
                                           body.get('budget'), body.get('assistance', 'automatic'), profile.parent)
            if route.startswith('/api/datasets'):
                from .datasets import Datasets
                service = Datasets(controller.store)
                if method == 'GET' and route == '/api/datasets':
                    return service.catalog()
                if method == 'POST' and route == '/api/datasets/register-profile':
                    profile = self.profiles.get(body.get('profile_id'))
                    if profile is None or body.get('role') not in {'learning', 'development'}:
                        raise PolicyError('Choose a server-approved project profile and source role')
                    from .config import resolve
                    data = json.loads(profile.read_text())
                    # Register the inspected allowlist, not a previous workflow's assignment.
                    resolved = resolve(data, {'dataset_assignment': None, 'dataset_task': None}, profile.parent)['config']
                    sources = Sources(controller.store)
                    root = sources.register_root(resolved['project'], body['role'])
                    return {'root_id': root['id'], 'source_ids': [sources.register(root['id'], path)['id']
                                                               for path in resolved['input_files']],
                            'files': resolved['input_files'], 'source_files_modified': 0}
                if method == 'POST' and route == '/api/datasets/propose':
                    return service.propose(body)
                if method == 'POST' and route == '/api/datasets/request-review':
                    return service.request_review(body.get('dataset_id'))
            if method == "POST" and route == "/api/library/import":
                root = self.library_roots.get(body.get("root_id"))
                if root is None:
                    raise PolicyError("Library root was not approved when the server started")
                return library.import_books(root)
            metrics_match = re.fullmatch(r"/api/metrics/([0-9a-f]{32})", route)
            if method == "GET" and metrics_match:
                from .metrics import Metrics
                return Metrics(controller).report(metrics_match[1])
            trace_match = re.fullmatch(r'/api/runs/([0-9a-f]{32})/(trace|input|evidence)(?:/([0-9a-f]{64}))?', route)
            if method == 'GET' and trace_match:
                from .traceability import Traceability
                service = Traceability(controller)
                run_id, action, evidence_id = trace_match.groups()
                if action == 'trace' and evidence_id is None:
                    return service.report(run_id)
                if action == 'input' and evidence_id is None:
                    return service.input(run_id, query.get('path', [''])[0])
                if action == 'evidence' and evidence_id:
                    return service.evidence(run_id, evidence_id)
                raise PolicyError('Invalid traceability request')
            if method == "GET" and route == "/api/repairs":
                from .repairs import Repairs
                return Repairs(controller).catalog()
            repair_diff = re.fullmatch(r"/api/repairs/([0-9a-f]{64})/diff", route)
            if method == "GET" and repair_diff:
                from .repairs import Repairs
                return Repairs(controller).diff(repair_diff[1])
            if method == "POST" and route == "/api/repairs/stage":
                from .repairs import Repairs
                return Repairs(controller).stage(body.get("run_id"), body.get("issue"), body.get("patch"), body.get("parent_id"))
            if method == "POST" and route == "/api/repairs/validate":
                from .repairs import Repairs
                return Repairs(controller).validate(body.get("candidate_id"))
            if method == "GET" and route == "/api/engineering":
                return {"snapshots": controller.store.records("architecture_snapshot"),
                        "policies": controller.store.records("architecture_policy"),
                        "ledgers": controller.store.records("requirement_ledger")}
            if method == "POST" and route == "/api/architecture/propose":
                from .architecture import Architecture
                return Architecture(controller).propose(body.get("snapshot_id"), body.get("changes"))
            if method == "POST" and route == "/api/architecture/request-review":
                from .architecture import Architecture
                return Architecture(controller).request_review(body.get("policy_id"))
            if method == "POST" and route == "/api/requirements/propose":
                from .requirements import Requirements
                return Requirements(controller.store).propose(body)
            if method == "POST" and route == "/api/requirements/request-review":
                from .requirements import Requirements
                return Requirements(controller.store).request_review(body.get("ledger_id"))
            source_match = re.fullmatch(r"/api/source/([0-9a-f]{64})", route)
            if method == "GET" and source_match:
                return Sources(controller.store).view(source_match[1], "human",
                    int(query.get("start", [1])[0]), int(query["end"][0]) if "end" in query else None)
            if method == "POST" and route in {"/api/resolve", "/api/runs"}:
                profile = self.profiles.get(body.get("profile_id"))
                if profile is None:
                    raise PolicyError("Unknown server-approved profile")
                allowed = {"mode", "assistance", "task_operation", "budget", "dataset_assignment", "dataset_task"}
                overrides = body.get("overrides", {})
                if not isinstance(overrides, dict) or not set(overrides) <= allowed:
                    raise PolicyError("UI override not permitted; review project/source scope via a saved profile")
                data = json.loads(profile.read_text())
                if route == "/api/resolve":
                    from .config import resolve
                    return resolve(data, overrides, profile.parent)
                return controller.create(data, overrides, profile.parent)
            run_match = re.fullmatch(r"/api/runs/([0-9a-f]{32})(?:/(logs|pause|resume|stop|execute|budget))?", route)
            if run_match:
                run_id, action = run_match.groups()
                if method == "GET" and action is None:
                    return controller.status(run_id)
                if method == "GET" and action == "logs":
                    return {"events": controller.store.events(run_id)}
                if method == "POST" and action in {"pause", "resume", "stop"}:
                    return controller.control(run_id, action)
                if method == "POST" and action == "budget":
                    if "approval_id" in body:
                        return controller.amend_budget(run_id, body["approval_id"])
                    return controller.request_budget(run_id, body.get("aggregate_model_tokens"), body.get("wall_seconds"))
                if method == "POST" and action == "execute":
                    if controller.status(run_id)["state"] != "READY":
                        raise PolicyError("Only a READY run can start")
                    def worker():
                        c = Controller(self.state_dir)
                        try:
                            c.execute(run_id)
                        except (PolicyError, OSError) as exc:
                            c.store.event(run_id, "worker_error", {"error": str(exc)})
                        finally:
                            c.close()
                    threading.Thread(target=worker, daemon=True).start()
                    return {"run_id": run_id, "status": "EXECUTION_REQUESTED"}
            approval_match = re.fullmatch(r"/api/approvals/([0-9a-f]{64})", route)
            if approval_match and method == "POST":
                return Approvals(controller.store).decide(approval_match[1], body.get("expected_digest"),
                                    body.get("decision"), body.get("reviewer"))
            raise PolicyError("Unknown route")
        finally:
            controller.close()


def make_server(application, port=0, token=None):
    secret = token or secrets.token_urlsafe(32)
    frontend = Path(__file__).resolve().parents[1] / "frontend"
    assets = {
        "/": (frontend / "index.html", "text/html; charset=utf-8"),
        "/assets/app.js": (frontend / "dist/app.js", "text/javascript"),
        "/assets/style.css": (frontend / "style.css", "text/css"),
        "/assets/react.js": (frontend / "node_modules/react/umd/react.production.min.js", "text/javascript"),
        "/assets/react-dom.js": (frontend / "node_modules/react-dom/umd/react-dom.production.min.js", "text/javascript"),
    }

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Never put tokens, source content or request bodies into access logs.

        def send(self, code, value, mime="application/json"):
            payload = value if isinstance(value, bytes) else json.dumps(value, allow_nan=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(payload)

        def handle_request(self, method):
            self.connection.settimeout(5)
            host = "127.0.0.1:" + str(self.server.server_port)
            if self.headers.get("Host") != host:
                return self.send(403, {"error": "Invalid local host"})
            parsed = urlsplit(self.path)
            if method == "GET" and parsed.path in assets:
                path, mime = assets[parsed.path]
                if not path.is_file():
                    return self.send(503, {"error": "Frontend is not built; run npm ci --ignore-scripts then npm run build in workbench/frontend"})
                return self.send(200, path.read_bytes(), mime)
            if not hmac.compare_digest(self.headers.get("Authorization", ""), "Bearer " + secret):
                return self.send(401, {"error": "Local session token required"})
            origin = self.headers.get("Origin")
            if (origin is not None and origin != "http://" + host) or (method == "POST" and origin is None):
                return self.send(403, {"error": "Same-origin request required"})
            body = {}
            try:
                if method == "POST":
                    size = int(self.headers.get("Content-Length", "0"))
                    if size < 0 or size > (24 if parsed.path == '/api/learning/context-upload' else 1) * 1024 * 1024:
                        return self.send(413, {"error": "Request size limit exceeded"})
                    if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                        return self.send(415, {"error": "JSON requests only"})
                    body = json.loads(self.rfile.read(size))
                    if not isinstance(body, dict):
                        raise PolicyError("Object request required")
                result = application.call(method, parsed.path, body, parse_qs(parsed.query))
                self.send(200, result)
            except (PolicyError, ValueError, TypeError, KeyError, OSError) as exc:
                self.send(400, {"error": str(exc)})

        def do_GET(self):
            self.handle_request("GET")

        def do_POST(self):
            self.handle_request("POST")

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    return server, secret


def serve(state_dir, profiles, library_roots, port=8765):
    server, token = make_server(Application(state_dir, profiles, library_roots), port)
    print("Local Workbench: http://127.0.0.1:" + str(server.server_port) + "/#token=" + token, flush=True)
    print("Paid execution needs bounded authorization and a validated worker. Keep this local access URL private.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
