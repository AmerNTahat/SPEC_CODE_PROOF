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
                        "library_roots": self.library_roots, "paid_execution": "DEFERRED_BY_USER",
                        "defaults": {mode: defaults(mode) for mode in ("user", "learning")},
                        "approvals": [Approvals(controller.store).get(r["id"]) for r in controller.store.records("approval")],
                        "capabilities": {"rule_import": True, "source_viewer": True, "prepare_run": True,
                                         "isolated_typecheck": True, "model_execution": False,
                                         "live_demo": False, "independent_transfer_validation": False}}
            if method == "GET" and route == "/api/library":
                return library.catalog()
            if method == "POST" and route == "/api/library/import":
                root = self.library_roots.get(body.get("root_id"))
                if root is None:
                    raise PolicyError("Library root was not approved when the server started")
                return library.import_books(root)
            source_match = re.fullmatch(r"/api/source/([0-9a-f]{64})", route)
            if method == "GET" and source_match:
                return Sources(controller.store).view(source_match[1], "human",
                    int(query.get("start", [1])[0]), int(query["end"][0]) if "end" in query else None)
            if method == "POST" and route in {"/api/resolve", "/api/runs"}:
                profile = self.profiles.get(body.get("profile_id"))
                if profile is None:
                    raise PolicyError("Unknown server-approved profile")
                allowed = {"mode", "assistance", "task_operation", "budget"}
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
                    if size < 0 or size > 1024 * 1024:
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
    print("Paid execution deferred. Keep this local access URL private.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
