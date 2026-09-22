"""Opt-in real worker checks; no model calls. Run from repository root.

Uses the existing producer-consumer profile and disposable source copies.
Never relaxes worker isolation when namespaces are unavailable.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

from inspecta_scp.config import resolve
from inspecta_scp.controller import Controller


def main():
    repo = Path.cwd()
    profile_path = repo / "workbench/profiles/producer-consumer.check.json"
    profile = json.loads(profile_path.read_text())
    config = resolve(profile, base_dir=profile_path.parent)["config"]
    profile["project"] = config["project"]
    results = []
    with tempfile.TemporaryDirectory(prefix="inspecta-integration-", dir=repo / ".scp-workbench") as temp:
        root = Path(temp)
        controller = Controller(root / "state")
        try:
            run = controller.create(profile)
            good = controller.execute(run["id"])
            assert good["state"] == "CHECKED", good
            assert not good["result"]["engineering_accepted"]
            results.append({"case": "real_valid_producer_consumer", "state": good["state"],
                            "events": controller.store.events(run["id"])})
            mutated = root / "invalid-project"
            for rel in profile["input_files"]:
                dest = mutated / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(Path(profile["project"]) / rel, dest)
            with (mutated / profile["model_file"]).open("a") as stream:
                stream.write("\npackage IntentionallyBroken { part def\n")
            bad_profile = {**profile, "project": str(mutated)}
            run = controller.create(bad_profile)
            bad = controller.execute(run["id"])
            assert bad["state"] == "FAILED", bad
            results.append({"case": "real_seeded_syntax_failure", "state": bad["state"],
                            "events": controller.store.events(run["id"])})
            run = controller.create(profile)
            env = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "PYTHONPATH": str(repo / "workbench"),
                   "PYTHONDONTWRITEBYTECODE": "1"}
            with (root / "worker.log").open("w") as output:
                worker = subprocess.Popen([str(repo / ".venv/bin/python"), "-m", "inspecta_scp.cli",
                                           "--state-dir", str(root / "state"), "execute", run["id"]],
                                          stdout=output, stderr=output, env=env)
                try:
                    deadline = time.monotonic() + 15
                    while controller.status(run["id"])["state"] == "READY" and time.monotonic() < deadline:
                        time.sleep(0.01)
                    requested = controller.control(run["id"], "pause")
                    assert requested["state"] == "PAUSE_REQUESTED", requested
                    worker.wait(timeout=15)
                    paused = controller.status(run["id"])
                    assert paused["state"] == "PAUSED", paused
                    resumed = controller.control(run["id"], "resume")
                    assert resumed["deadline"] == run["deadline"]
                    controller.control(run["id"], "stop")
                    results.append({"case": "real_pause_acknowledgement_and_resume", "state": "PASS",
                                    "events": controller.store.events(run["id"])})
                finally:
                    if worker.poll() is None:
                        worker.terminate()
                        worker.wait(timeout=5)
            # Export referenced objects before disposing the integration workspace.
            evidence_dir = repo / "reports/build/real-worker-evidence"
            evidence_dir.mkdir(exist_ok=True)
            for obj in (root / "state/objects").glob("*.json"):
                target = evidence_dir / obj.name
                if target.exists():
                    assert target.read_bytes() == obj.read_bytes()
                else:
                    shutil.copy2(obj, target)
            result = {"scope": "Real typechecker and worker control integration only; not a live learning demo",
                      "model_calls": 0, "cases": results, "evidence_directory": str(evidence_dir.relative_to(repo))}
            (repo / "reports/build/real-worker-integration.json").write_text(json.dumps(result, indent=2) + "\n")
            print(json.dumps({"cases_passed": len(results), "model_calls": 0}))
        finally:
            controller.close()


if __name__ == "__main__":
    main()
