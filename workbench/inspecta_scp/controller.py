"""Trusted run controller. Unsupported gates and adapters fail closed."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
import signal
import subprocess
import time

from .config import PolicyError, digest, resolve
from .storage import Store, safe_child, sha_file
from .approvals import Approvals


TERMINAL = {"CHECKED", "BLOCKED", "FAILED", "CANCELLED", "BUDGET_EXHAUSTED"}


class Controller:
    def __init__(self, state_dir):
        self.store = Store(state_dir)

    def close(self):
        self.store.close()

    def request_budget(self, run_id, token_limit, wall_seconds):
        run = self.status(run_id)
        if type(token_limit) is not int or type(wall_seconds) is not int:
            raise PolicyError("Budget caps must be integers")
        if token_limit < run["config"]["budget"]["aggregate_model_tokens"] or wall_seconds < run["config"]["budget"]["wall_seconds"]:
            raise PolicyError("An extension cannot reduce existing caps")
        return Approvals(self.store).request("increase_budget", {
            "run_id": run_id, "config_hash": run["config_hash"],
            "aggregate_model_tokens": token_limit, "wall_seconds": wall_seconds})

    def amend_budget(self, run_id, approval_id):
        approvals = Approvals(self.store)
        request = approvals.get(approval_id)
        self.store.db.execute("BEGIN IMMEDIATE")
        try:
            run = self.status(run_id)
            subject = {**request["subject"], "run_id": run_id, "config_hash": run["config_hash"]}
            approvals.require(approval_id, "increase_budget", subject)
            if run["state"] not in {"READY", "PAUSED", "BUDGET_EXHAUSTED"}:
                raise PolicyError("Pause active work before amending its budget")
            if run["reserved_tokens"]:
                raise PolicyError("Reconcile in-flight reservations before budget amendment")
            config = run["config"]
            if subject["aggregate_model_tokens"] < config["budget"]["aggregate_model_tokens"] or subject["wall_seconds"] < config["budget"]["wall_seconds"]:
                raise PolicyError("Approval cannot reduce prior allowance")
            config["budget"].update({key: subject[key] for key in ("wall_seconds", "aggregate_model_tokens")})
            new_hash = digest(config)
            if new_hash == run["config_hash"]:
                raise PolicyError("Amendment must change a cap")
            self.store.db.execute("UPDATE runs SET config=?,config_hash=?,deadline=?,state='PAUSED',result=NULL,version=version+1 WHERE id=?",
                                  (json.dumps(config), new_hash, run["created"] + subject["wall_seconds"], run_id))
            self.store.event(run_id, "budget_amendment", {"approval_id": approval_id,
                "previous_config_hash": run["config_hash"], "config_hash": new_hash,
                "previous_result": run["result"], "used_tokens_preserved": run["used_tokens"],
                "usage_unknown_preserved": bool(run["usage_unknown"]), "prior_evidence_invalidated": True})
            self.store.db.execute("COMMIT")
        except BaseException:
            self.store.db.execute("ROLLBACK")
            raise
        return self.status(run_id)

    def _validate_policies(self, config):
        if config.get('dataset_assignment'):
            from .datasets import Datasets
            Datasets(self.store).validate_run(config)
        if config.get("architecture_policy"):
            from .architecture import Architecture
            Architecture(self).approved(config["architecture_policy"])
        if config.get("requirement_ledger"):
            from .requirements import Requirements
            ledger = Requirements(self.store).approved(config["requirement_ledger"])
            mandatory = {g for o in ledger["record"]["obligations"] for g in o["required_gate_ids"]}
            if not mandatory <= set(config["required_gates"]):
                raise PolicyError("Run omits acceptance gates required by approved obligations")

        if config.get("unit_registry"):
            from .metrics import Metrics
            registry = Metrics(self).approved(config["unit_registry"])["record"]
            if registry["ledger_id"] != config.get("requirement_ledger"):
                raise PolicyError("Run ledger differs from frozen unit registry")
            for unit in registry["units"]:
                if not set(unit["implementation_files"]) <= set(config["input_files"]):
                    raise PolicyError("Registered implementation file missing from run input scope")
                if not set(unit["formal_gate_ids"]) <= set(config["required_gates"]):
                    raise PolicyError("Run omits registered formal gates")

    def create(self, profile, overrides=None, base_dir=None):
        resolved = resolve(profile, overrides, base_dir)
        config = resolved["config"]
        self._validate_policies(config)
        source = Path(config["project"] or "")
        if not config["project"] or not source.is_dir():
            raise PolicyError("Existing project directory required for this controller version")
        if source == self.store.root or self.store.root in source.parents:
            raise PolicyError("A run state directory cannot be a project")
        inputs = {}
        for rel in config["input_files"]:
            p = safe_child(source, rel)
            if not p.is_file():
                raise PolicyError("Missing declared input: " + rel)
            if p.stat().st_size > 16 * 1024 * 1024:
                raise PolicyError("Input exceeds 16 MiB inspection limit: " + rel)
            inputs[rel] = sha_file(p)
        run_id = self.store.create(resolved)
        self.store.change(run_id, {"CREATED"}, "INSPECTING")
        folder = self.store.root / "runs" / run_id
        candidate = folder / "candidate"
        candidate.mkdir()
        try:
            for rel, expected in inputs.items():
                original = safe_child(source, rel)
                data = original.read_bytes()
                import hashlib
                if hashlib.sha256(data).hexdigest() != expected:
                    raise PolicyError("Source changed while snapshotting: " + rel)
                dest = safe_child(candidate, rel)
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
            manifest = {"source_root": str(source), "files": inputs,
                        "scope": "Explicit authorized input allowlist, including dirty/untracked content"}
            ref = self.store.object(manifest)
            (folder / "input-workspace-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
            self.store.event(run_id, "snapshot", ref)
            self.store.change(run_id, {"INSPECTING"}, "READY")
        except BaseException as exc:
            self.store.change(run_id, {"INSPECTING"}, "BLOCKED", {"reason": str(exc)})
            raise
        return self.status(run_id)

    def status(self, run_id):
        result = self.store.get(run_id)
        config = result["config"]
        if digest(config) != result["config_hash"]:
            raise PolicyError("Resolved configuration was modified")
        folder = self.store.root / "runs" / run_id
        manifest_path = safe_child(folder, "input-workspace-manifest.json")
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text())
            snapshots = [e["payload"] for e in self.store.events(run_id) if e["kind"] == "snapshot"]
            if not snapshots or digest(manifest) != snapshots[-1]["sha256"]:
                raise PolicyError("Input manifest was modified")
            changed = []
            for rel, expected in manifest["files"].items():
                try:
                    original = safe_child(Path(config["project"]), rel)
                    if sha_file(original) != expected:
                        changed.append(rel)
                except (OSError, PolicyError):
                    changed.append(rel)
            result["source_changed"] = changed
            result["evidence_current_for_source"] = not changed
        if result["result"]:
            for gate in result["result"]["gates"]:
                ref = gate.get("evidence")
                if ref:
                    p = safe_child(self.store.root, ref["path"])
                    if not p.is_file() or sha_file(p) != ref["sha256"]:
                        raise PolicyError("Evidence missing or modified")
        try:
            self._validate_policies(config)
            result["policy_current"] = True
        except PolicyError as exc:
            result["policy_current"] = False
            result["policy_problem"] = str(exc)
            result["evidence_current_for_source"] = False
        return result

    def control(self, run_id, action):
        run = self.store.get(run_id)
        state = run["state"]
        if action == "pause":
            if state == "READY":
                self.store.change(run_id, {state}, "PAUSED")
            else:
                self.store.change(run_id, {"RUNNING", "CHECKING"}, "PAUSE_REQUESTED", worker=run["worker"])
        elif action == "stop":
            if state in {"READY", "PAUSED"}:
                self.store.change(run_id, {state}, "CANCELLED")
            else:
                self.store.change(run_id, {"RUNNING", "CHECKING", "PAUSE_REQUESTED"}, "STOP_REQUESTED", worker=run["worker"])
        elif action == "resume":
            next_state = "READY" if run["remaining_seconds"] > 0 else "BUDGET_EXHAUSTED"
            self.store.change(run_id, {"PAUSED"}, next_state,
                              {"budget_reset": False, "deadline": run["deadline"]})
        else:
            raise PolicyError("Unknown control action")
        return self.status(run_id)

    def _sandbox_command(self, config, candidate, operation="parse_type", output=None):
        exe = Path(config["sireum"] or "")
        if not config["sireum"] or not exe.is_file() or not os.access(exe, os.X_OK):
            raise PolicyError("Selected Sireum executable is unavailable")
        if not config["sireum_sha256"] or sha_file(exe) != config["sireum_sha256"]:
            raise PolicyError("Sireum fingerprint missing or changed")
        home = exe.parent.parent
        has_jar = (home / "bin/sireum.jar").is_file()
        has_native = (home / "bin/linux/sireum").is_file()
        if exe.name != "sireum" or exe.parent.name != "bin" or not (has_jar or has_native):
            raise PolicyError("This adapter requires an initialized native or JVM Sireum home; no bootstrap is permitted")
        repo = Path(__file__).resolve().parents[2]
        bwrap = repo / "tools/codex-runtime-v0.155.1/codex-resources/bwrap"
        if not bwrap.is_file() or sha_file(bwrap) != "77360cb751ccedc5971391444ac86a8a33c15b04d6b4a6fe45f5d25496e62c4c":
            raise PolicyError("Verified worker sandbox resource unavailable")
        command = [str(bwrap), "--unshare-all", "--die-with-parent", "--new-session"]
        for directory in ("/usr", "/bin", "/lib", "/lib64"):
            if Path(directory).exists():
                command.extend(["--ro-bind", directory, directory])
        command.extend(["--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp",
                        "--dir", "/etc", "--dir", "/opt", "--ro-bind", str(home), "/opt/sireum",
                        "--ro-bind", str(candidate), "/work", "--chdir", "/work",
                        "--clearenv", "--setenv", "PATH", "/usr/bin:/bin",
                        "--setenv", "HOME", "/tmp", "--setenv", "LANG", "C.UTF-8"])
        cache = Path("/etc/ld.so.cache")
        if cache.is_file():
            command.extend(["--ro-bind", str(cache), str(cache)])
        adapter = None
        if operation == "architecture_capture":
            if not has_jar:
                raise PolicyError("Architecture adapter needs initialized JVM Sireum; tested native evaluator cannot resolve the CLI APIs")
            # Distributions can contain both runtimes. This adapter imports JVM
            # CLI APIs; select the JVM explicitly and avoid a write to read-only
            # tool storage for optional AOT training.
            command.extend(["--setenv", "SIREUM_NATIVE", "false", "--setenv", "SIREUM_NO_AOT", "true"])
            adapter = repo / "workbench/adapters/export_architecture.sc"
            if output is None or not adapter.is_file():
                raise PolicyError("Architecture adapter or output directory missing")
            command.extend(["--ro-bind", str(adapter), "/export_architecture.sc",
                            "--bind", str(output), "/output",
                            "/opt/sireum/bin/sireum", "slang", "run"])
            command.extend(["/export_architecture.sc", "/work", "/output"])
        elif operation == "parse_type":
            command.extend(["/opt/sireum/bin/sireum", "hamr", "sysml", "tipe",
                            "--sourcepath", "/work", "/work/" + config["model_file"]])
        elif operation in {"hamr_codegen", "integration_constraints"}:
            if output is None:
                raise PolicyError('Isolated tool output directory required')
            if has_jar:
                # The released native image can lack reflection metadata used
                # by Microkit reporting. The matching JVM is the compatible
                # execution path; keep both identities in recorded evidence.
                command.extend(["--setenv", "SIREUM_NATIVE", "false", "--setenv", "SIREUM_NO_AOT", "true"])
            command.extend(['--bind', str(output), '/output'])
            if operation == 'hamr_codegen':
                cache = Path(output) / 'model-cache'
                cache.mkdir(exist_ok=True)
                # HAMR writes resolved AIR under workspace/.slang. Only this
                # cache is writable; every model source remains read-only.
                command.extend(['--bind', str(cache), '/work/.slang'])
                command.extend(['/opt/sireum/bin/sireum', 'hamr', 'sysml', 'codegen', '--sourcepath', '/work', '--platform', config.get('hamr_platform','JVM'),
                                '--output-dir', '/output', '--workspace-root-dir', '/work',
                                '--no-proyek-ive', '/work/' + config['model_file']])
            else:
                command.extend(['/opt/sireum/bin/sireum', 'hamr', 'sysml', 'logika', '--sourcepath', '/work', '--feedback', '/output/feedback',
                                '--log-vc-dir', '/output/vc', '--stats'])
                solver=config.get('integration_solver','auto')
                if solver!='auto':
                    command.extend(['--solver-sat',solver,'--solver-valid',solver])
                command.append('/work/' + config['model_file'])
        else:
            raise PolicyError("Unknown trusted operation")
        identity = {"launcher_sha256": sha_file(exe), "jar_sha256": sha_file(home / "bin/sireum.jar") if has_jar else None,
                    "sandbox_sha256": sha_file(bwrap), "network": "unshared", "home": "empty_tmpfs",
                    "candidate_mount": "read_only", "profile": "sireum-tipe-v1"}
        identity["runtime_files"] = {rel: sha_file(home / rel) for rel in
                                     ("bin/linux/sireum", "bin/linux/java/bin/java")
                                     if (home / rel).is_file()}
        if adapter:
            identity.update(adapter_sha256=sha_file(adapter), profile="sireum-architecture-v1")
        elif operation in {'hamr_codegen', 'integration_constraints'}:
            identity['profile'] = 'sireum-' + operation + '-v1'
            identity['solver_files'] = {rel: sha_file(home / rel)
                                       for rel in ('bin/linux/z3/bin/z3', 'bin/linux/z3/bin/libz3.so',
                                                   'bin/linux/cvc5', 'bin/linux/cvc', 'bin/linux/alt-ergo')
                                       if (home / rel).is_file()}
        return command, identity

    def _run_tool(self, run_id, config, folder, operation):
        if not config["model_file"]:
            raise PolicyError("No root model selected")
        output = None
        if operation in {"architecture_capture", "hamr_codegen", "integration_constraints"}:
            import tempfile
            output = Path(tempfile.mkdtemp(prefix=operation + "-", dir=folder))
        candidate = folder / "candidate"
        input_derivation = None
        if operation == "hamr_codegen":
            from .codegen_inputs import execution_view
            candidate = folder / ("codegen-input-" + output.name)
            input_derivation = execution_view(folder / "candidate", candidate, config['input_files'])
        argv, identity = self._sandbox_command(config, candidate, operation, output)
        start = time.monotonic()
        interrupted = None
        stdout, stderr = folder / (operation + ".stdout"), folder / (operation + ".stderr")
        # Only the trusted parser is invoked; never candidate scripts or model commands.
        with stdout.open("wb") as out, stderr.open("wb") as err:
            proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                    start_new_session=True, env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"})
            try:
                while proc.poll() is None:
                    run = self.store.get(run_id)
                    if run["state"] in {"PAUSE_REQUESTED", "STOP_REQUESTED"}:
                        interrupted = "PAUSED" if run["state"] == "PAUSE_REQUESTED" else "CANCELLED"
                    elif run["remaining_seconds"] <= 0 or time.monotonic() - start >= 120:
                        interrupted = "BUDGET_EXHAUSTED"
                    elif stdout.stat().st_size + stderr.stat().st_size > 16 * 1024 * 1024:
                        interrupted = "BLOCKED"
                    if interrupted:
                        os.killpg(proc.pid, signal.SIGTERM)
                        try:
                            proc.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            os.killpg(proc.pid, signal.SIGKILL)
                            proc.wait()
                        break
                    time.sleep(0.05)
            finally:
                if proc.poll() is None:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait()
        out_text, err_text = stdout.read_text(errors="replace"), stderr.read_text(errors="replace")
        _, final_identity = self._sandbox_command(config, candidate, operation, output)
        if final_identity != identity:
            raise PolicyError("Tool identity changed during checking")
        record = {"command": argv, "tool_identity": identity, "input_derivation": input_derivation, "exit_code": proc.returncode,
                  "stdout": out_text, "stderr": err_text, "elapsed_seconds": time.monotonic() - start,
                  "interrupted": interrupted, "config_sha256": self.store.get(run_id)["config_hash"],
                  "input_manifest_sha256": digest(json.loads((folder / "input-workspace-manifest.json").read_text())),
                  "scope": "Real type checking only; not behavioral, proof, or architectural acceptance"}
        return record, output, interrupted

    def _parse_type(self, run_id, config, folder):
        record, _, interrupted = self._run_tool(run_id, config, folder, "parse_type")
        out_text, err_text = record["stdout"], record["stderr"]
        status, reason = "UNKNOWN", "No validated success marker"
        if interrupted:
            reason = "Execution interrupted: " + interrupted
        elif "bwrap:" in err_text:
            reason = "Worker sandbox could not start; no unsandboxed fallback"
        elif record["exit_code"] != 0:
            status, reason = "FAIL", "Checker process rejected the model"
        elif re.search(r'^\s*-\s*\[\d+,\s*\d+\]\s+(?:TypeChecker|Instantiation) Error:', out_text+'\n'+err_text, re.M):
            status, reason = "FAIL", "Type checker reported errors despite a zero process exit status"
        elif "Well-formed!" in out_text:
            status, reason = "PASS", "Type checker completed"
            if "MISSING_AADL_TYPE" in out_text or "Instantiation Warning" in out_text:
                status, reason = "UNKNOWN", "Unresolved instantiation warnings require review"
        return {"gate": "parse_type", "status": status, "reason": reason,
                "evidence": self.store.object(record)}, interrupted

    def execute(self, run_id):
        run = self.status(run_id)
        if run["state"] != "READY":
            raise PolicyError("Only READY runs can execute; resume does not launch work implicitly")
        if run.get("source_changed"):
            self.store.change(run_id, {"READY"}, "BLOCKED", {"reason": "Source changed since snapshot"})
            return self.status(run_id)
        if run["remaining_seconds"] <= 0:
            self.store.change(run_id, {"READY"}, "BUDGET_EXHAUSTED")
            return self.status(run_id)
        config = run["config"]
        try:
            self._validate_policies(config)
        except PolicyError as exc:
            self.store.change(run_id, {"READY"}, "BLOCKED", {"reason": str(exc)})
            return self.status(run_id)
        if config["resolved_operation"] != "verify-only":
            reason = "Use the reviewed learning/development services for bounded model work; frozen User application is not yet connected to this run operation"
            if config["budget"]["enforcement"] == "strict":
                reason += "; installed Codex CLI has no validated hard-token ceiling"
            self.store.change(run_id, {"READY"}, "BLOCKED", {"reason": reason})
            return self.status(run_id)
        folder = self.store.root / "runs" / run_id
        manifest = json.loads((folder / "input-workspace-manifest.json").read_text())
        actual = {p.relative_to(folder / "candidate").as_posix(): sha_file(p)
                  for p in (folder / "candidate").rglob("*") if p.is_file() and not p.is_symlink()}
        if actual != manifest["files"] or any(p.is_symlink() for p in (folder / "candidate").rglob("*")):
            raise PolicyError("Candidate snapshot was modified")
        self.store.change(run_id, {"READY"}, "CHECKING", worker=os.getpid())
        gates, interrupted = [], None
        try:
            for gate in config["required_gates"]:
                current = self.store.get(run_id)
                if current["state"] in {"PAUSE_REQUESTED", "STOP_REQUESTED"}:
                    interrupted = "PAUSED" if current["state"] == "PAUSE_REQUESTED" else "CANCELLED"
                    break
                if current["remaining_seconds"] <= 0:
                    interrupted = "BUDGET_EXHAUSTED"
                    break
                if gate == "parse_type":
                    result, interrupted = self._parse_type(run_id, config, folder)
                elif gate in {"architecture_capture", "architecture"}:
                    from .architecture import Architecture
                    if gate == "architecture" and not config.get("architecture_policy"):
                        result = {"gate": gate, "status": "NOT_RUN", "reason": "Reviewed architecture policy required"}
                    else:
                        result, interrupted = Architecture(self).capture(run_id, config, folder)
                        if gate == "architecture":
                            result = Architecture(self).check(config.get("architecture_policy"), result)
                elif gate == "requirements_coverage":
                    from .requirements import Requirements
                    architecture = next((g for g in gates if g["gate"] in {"architecture_capture", "architecture"}), None)
                    if config.get("requirement_ledger") and architecture is None:
                        from .architecture import Architecture
                        architecture, interrupted = Architecture(self).capture(run_id, config, folder)
                        gates.append(architecture)
                        self.store.event(run_id, "gate", architecture)
                    result = Requirements(self.store).coverage(config.get("requirement_ledger"), architecture)
                elif gate in {'hamr_codegen', 'integration_constraints'}:
                    from .engineering import Engineering
                    result, interrupted = Engineering(self).check(run_id, config, folder, gate)
                else:
                    result = {"gate": gate, "status": "NOT_RUN", "reason": "Trusted adapter not yet implemented"}
                gates.append(result)
                self.store.event(run_id, "gate", result)
                if interrupted:
                    break
            current = self.store.get(run_id)
            if current["state"] in {"PAUSE_REQUESTED", "STOP_REQUESTED"}:
                interrupted = "PAUSED" if current["state"] == "PAUSE_REQUESTED" else "CANCELLED"
            after = {p.relative_to(folder / "candidate").as_posix(): sha_file(p)
                     for p in (folder / "candidate").rglob("*") if p.is_file() and not p.is_symlink()}
            if after != manifest["files"] or any(p.is_symlink() for p in (folder / "candidate").rglob("*")):
                raise PolicyError("Candidate changed during checking; evidence invalidated")
            self._validate_policies(config)
            state = interrupted or ("FAILED" if any(g["status"] == "FAIL" for g in gates) else
                                    "CHECKED" if gates and all(g["status"] == "PASS" for g in gates) else "BLOCKED")
            result = {"gates": gates, "task_status": state, "project_status": "NOT_ASSESSED",
                      "engineering_accepted": False, "formally_verified_units": 0,
                      "model_calls": 0, "scope": "Selected checks only; no application or live-demo completion claim"}
            self.store.finish(run_id, result)
        except (PolicyError, OSError) as exc:
            self.store.change(run_id, {"CHECKING", "PAUSE_REQUESTED", "STOP_REQUESTED"}, "BLOCKED", {"reason": str(exc)})
        except Exception as exc:
            self.store.change(run_id, {"CHECKING", "PAUSE_REQUESTED", "STOP_REQUESTED"}, "BLOCKED",
                              {"reason": "Adapter failed unexpectedly: " + type(exc).__name__})
            raise
        return self.status(run_id)
