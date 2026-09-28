"""Application tests. These are not model, proof, or live demonstration evidence."""
import argparse
import json
import tempfile
import time
import unittest
from pathlib import Path

from inspecta_scp.cli import dispatch, parser
from inspecta_scp.config import PolicyError, digest, resolve
from inspecta_scp.controller import Controller
from inspecta_scp.storage import Store, sha_file
from inspecta_scp.vendor.local_compare import compare_text
from inspecta_scp.vendor.split_dataset import assign, approve


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.project = self.root / "project"
        self.project.mkdir()
        (self.project / "Model.sysml").write_text("package Example {}\n")
        self.profile = {"project": str(self.project), "input_files": ["Model.sysml"],
                        "model_file": "Model.sysml", "task_operation": "verify-only"}
        self.state = self.root / "state"
        self.controller = Controller(self.state)

    def tearDown(self):
        self.controller.close()
        self.tmp.cleanup()

    def test_unexpected_adapter_error_does_not_leave_run_checking(self):
        run=self.controller.create({**self.profile,'required_gates':['parse_type']})
        def broken(*args):raise TypeError('synthetic adapter fault')
        self.controller._parse_type=broken
        with self.assertRaises(TypeError):self.controller.execute(run['id'])
        self.assertEqual(self.controller.status(run['id'])['state'],'BLOCKED')
        self.assertIsNone(self.controller.status(run['id'])['result'])

    def test_explicit_override_and_null_are_preserved(self):
        p = {**self.profile, "rule_release": "release", "budget": {"wall_seconds": 60}}
        r = resolve(p, {"rule_release": None, "budget": {"wall_seconds": 90}})
        self.assertEqual(r["config"]["budget"]["wall_seconds"], 90)
        self.assertIsNone(r["config"]["rule_release"])
        self.assertEqual(digest(r["config"]), r["config_sha256"])

    def test_cli_service_configuration_parity(self):
        path = self.root / "request.json"
        path.write_text(json.dumps(self.profile))
        args = parser().parse_args(["resolve", "--config", str(path), "--token-limit", "777"])
        expected = resolve(self.profile, {"budget": {"aggregate_model_tokens": 777}}, path.parent)
        self.assertEqual(dispatch(args), expected)

    def test_creation_is_not_implicit(self):
        auto = resolve({**self.profile, "task_operation": "auto"})
        self.assertEqual(auto["config"]["resolved_operation"], "continue-project")
        with self.assertRaises(PolicyError):
            resolve({**self.profile, "task_operation": "create-system"})

    def test_unapproved_rename_rejected(self):
        with self.assertRaises(PolicyError):
            resolve({**self.profile, "naming_policy": "consistent-internal-renaming"})

    def test_invalid_budget_values(self):
        for bad in [None, True, -1, 0, "20"]:
            with self.subTest(bad=bad), self.assertRaises(PolicyError):
                resolve(self.profile, {"budget": {"wall_seconds": bad}})

    def test_unknown_operation_and_fields_rejected(self):
        for extra in [{"task_operation": "delete-system"}, {"shell": "echo accepted"}]:
            with self.assertRaises(PolicyError):
                resolve({**self.profile, **extra})

    def test_dataset_overlap_rejected(self):
        with self.assertRaises(PolicyError):
            resolve({**self.profile, "learning_materials": str(self.project),
                     "development_validation": str(self.project / "child")})

    def test_snapshot_preserves_dirty_untracked_input(self):
        original = (self.project / "Model.sysml").read_bytes()
        run = self.controller.create(self.profile)
        self.assertEqual(run["state"], "READY")
        copy = self.state / "runs" / run["id"] / "candidate/Model.sysml"
        self.assertEqual(copy.read_bytes(), original)
        self.assertEqual((self.project / "Model.sysml").read_bytes(), original)

    def test_symlink_input_rejected(self):
        (self.project / "escape.sysml").symlink_to(self.root / "secret")
        (self.root / "secret").write_text("not permitted")
        with self.assertRaises(PolicyError):
            self.controller.create({**self.profile, "input_files": ["escape.sysml"], "model_file": "escape.sysml"})

    def test_hidden_and_evaluator_paths_rejected(self):
        for name in [".env", "golden_examples/answer.sysml", "../answer.sysml", "key.pem"]:
            with self.subTest(name=name), self.assertRaises(PolicyError):
                resolve({**self.profile, "input_files": [name], "model_file": None})

    def test_source_change_blocks_execution(self):
        run = self.controller.create(self.profile)
        (self.project / "Model.sysml").write_text("concurrent user edit")
        result = self.controller.execute(run["id"])
        self.assertEqual(result["state"], "BLOCKED")
        self.assertFalse(result["evidence_current_for_source"])
        self.assertEqual((self.project / "Model.sysml").read_text(), "concurrent user edit")

    def test_snapshot_tamper_rejected(self):
        run = self.controller.create(self.profile)
        (self.state / "runs" / run["id"] / "candidate/Model.sysml").write_text("changed")
        with self.assertRaises(PolicyError):
            self.controller.execute(run["id"])

    def test_manifest_tamper_rejected(self):
        run = self.controller.create(self.profile)
        (self.state / "runs" / run["id"] / "input-workspace-manifest.json").write_text('{"files":{}}')
        with self.assertRaises(PolicyError):
            self.controller.status(run["id"])

    def test_pause_resume_preserves_deadline_and_usage(self):
        run = self.controller.create(self.profile)
        self.controller.store.db.execute("UPDATE runs SET used_tokens=12 WHERE id=?", (run["id"],))
        self.controller.control(run["id"], "pause")
        resumed = self.controller.control(run["id"], "resume")
        self.assertEqual(resumed["deadline"], run["deadline"])
        self.assertEqual(resumed["used_tokens"], 12)
        self.assertEqual(resumed["state"], "READY")

    def test_restart_does_not_reset_allowance(self):
        run = self.controller.create(self.profile)
        second = Controller(self.state)
        try:
            self.assertEqual(second.status(run["id"])["deadline"], run["deadline"])
        finally:
            second.close()

    def test_expired_resume_fails_closed(self):
        run = self.controller.create(self.profile)
        self.controller.control(run["id"], "pause")
        self.controller.store.db.execute("UPDATE runs SET deadline=? WHERE id=?", (time.time() - 1, run["id"]))
        self.assertEqual(self.controller.control(run["id"], "resume")["state"], "BUDGET_EXHAUSTED")

    def test_stop_prepared_run_is_terminal(self):
        run = self.controller.create(self.profile)
        self.assertEqual(self.controller.control(run["id"], "stop")["state"], "CANCELLED")
        with self.assertRaises(PolicyError):
            self.controller.execute(run["id"])

    def test_active_stop_is_request_not_false_acknowledgement(self):
        run = self.controller.create(self.profile)
        self.controller.store.change(run["id"], {"READY"}, "CHECKING", worker=123)
        self.assertEqual(self.controller.control(run["id"], "stop")["state"], "STOP_REQUESTED")

    def test_missing_tool_blocks_without_source_edits(self):
        before = sha_file(self.project / "Model.sysml")
        run = self.controller.create(self.profile)
        result = self.controller.execute(run["id"])
        self.assertEqual(result["state"], "BLOCKED")
        self.assertEqual(sha_file(self.project / "Model.sysml"), before)

    def test_missing_gate_never_accepted(self):
        run = self.controller.create({**self.profile, "required_gates": ["architecture"]})
        result = self.controller.execute(run["id"])
        self.assertEqual(result["state"], "BLOCKED")
        self.assertEqual(result["result"]["gates"][0]["status"], "NOT_RUN")
        self.assertFalse(result["result"]["engineering_accepted"])

    def test_unsupported_paid_adapter_blocks_even_with_boolean(self):
        run = self.controller.create({**self.profile, "task_operation": "repair-system", "paid_runs_authorized": True})
        self.assertEqual(self.controller.execute(run["id"])["state"], "BLOCKED")
        self.assertEqual(self.controller.store.get(run["id"])["used_tokens"], 0)

    def running(self):
        run = self.controller.create({**self.profile, "budget": {"aggregate_model_tokens": 100}})
        self.controller.store.change(run["id"], {"READY"}, "RUNNING")
        return run["id"]

    def test_reservation_conservation_and_cached_subset(self):
        run_id = self.running()
        store = self.controller.store
        reserved = store.reserve(run_id, 80)
        with self.assertRaises(PolicyError):
            store.reserve(run_id, 21)
        with self.assertRaises(PolicyError):
            store.reserve(run_id, 1)
        store.settle(reserved, {"input_tokens": 30, "cached_input_tokens": 20, "output_tokens": 10})
        self.assertEqual(store.get(run_id)["used_tokens"], 40)
        self.assertEqual(store.get(run_id)["remaining_tokens"], 60)
        with self.assertRaises(PolicyError):
            store.settle(reserved, {"input_tokens": 30, "cached_input_tokens": 20, "output_tokens": 10})

    def test_overshoot_charges_actual_usage(self):
        run_id = self.running()
        store = self.controller.store
        ref = store.reserve(run_id, 20)
        store.settle(ref, {"input_tokens": 100, "cached_input_tokens": 0, "output_tokens": 5})
        self.assertEqual(store.get(run_id)["used_tokens"], 105)
        self.assertEqual(store.get(run_id)["remaining_tokens"], 0)
        with self.assertRaises(PolicyError):
            store.reserve(run_id, 1)

    def test_unknown_usage_is_not_zero(self):
        run_id = self.running()
        store = self.controller.store
        ref = store.reserve(run_id, 20)
        store.settle(ref, None)
        self.assertIsNone(store.get(run_id)["remaining_tokens"])
        with self.assertRaises(PolicyError):
            store.reserve(run_id, 1)

    def test_evidence_tamper_rejected(self):
        ref = self.controller.store.object({"gate": "FAIL"})
        (self.state / ref["path"]).write_text("forged")
        with self.assertRaises(PolicyError):
            self.controller.store.object({"gate": "FAIL"})

    def test_related_tasks_cannot_cross_roles(self):
        tasks = [{"id": "a", "family_id": "isolette", "lineage_id": "a", "role": "learning"},
                 {"id": "b", "family_id": "isolette", "lineage_id": "b", "role": "final"}]
        with self.assertRaises(ValueError):
            assign({"tasks": tasks})

    def test_modified_split_cannot_be_approved(self):
        proposal = assign({"tasks": [{"id": "a", "family_id": "one", "lineage_id": "a", "role": "learning"}]})
        proposal["tasks"][0]["role"] = "final"
        with self.assertRaises(ValueError):
            approve(proposal, "reviewer")

    def test_lexical_difference_and_empty_vector(self):
        self.assertIsNone(compare_text("", "")['cosine_similarity'])
        a = compare_text("a b c d", "a b c x")
        self.assertEqual(a["sequence_deleted_plus_inserted"], 2)
        self.assertEqual(a["semantic_equivalence"], "NOT_ESTABLISHED")


if __name__ == "__main__":
    unittest.main()
