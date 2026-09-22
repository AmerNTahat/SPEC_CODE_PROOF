"""Local controller approvals bind a decision to exact immutable content.

Reviewer text records attribution, not cryptographic identity. This service belongs
outside candidate/model workspaces; the HTTP client must authenticate requests.
"""
import time

from .config import PolicyError, digest


class Approvals:
    ACTIONS = {"publish_release", "increase_budget", "promote_patch", "approve_dataset", "approve_architecture", "approve_requirements", "approve_registry"}

    def __init__(self, store):
        self.store = store

    def request(self, action, subject):
        if action not in self.ACTIONS:
            raise PolicyError("Unsupported approval action")
        request = self.store.record("approval", {"action": action, "subject": subject,
                                                  "subject_digest": digest(subject)})
        return self.get(request["id"])

    def get(self, request_id):
        request = self.store.read_record("approval", request_id)
        row = self.store.db.execute("SELECT * FROM decisions WHERE request_id=?", (request_id,)).fetchone()
        return {**request, "status": row["decision"] if row else "PENDING",
                "reviewer": row["reviewer"] if row else None,
                "decided_at": row["decided"] if row else None}

    def decide(self, request_id, expected_digest, decision, reviewer):
        if decision not in {"APPROVED", "REJECTED", "REVOKED"}:
            raise PolicyError("Unknown review decision")
        if not isinstance(reviewer, str) or not reviewer.strip():
            raise PolicyError("Reviewer identity required")
        self.store.db.execute("BEGIN IMMEDIATE")
        try:
            request = self.get(request_id)
            if request["subject_digest"] != expected_digest:
                raise PolicyError("Review does not match the requested subject")
            if decision == "REVOKED":
                if request["status"] != "APPROVED":
                    raise PolicyError("Only an approved request can be revoked")
                self.store.db.execute("UPDATE decisions SET decision=?,reviewer=?,decided=? WHERE request_id=?",
                                      (decision, reviewer, time.time(), request_id))
            else:
                if request["status"] != "PENDING":
                    raise PolicyError("Decision already recorded; create a new subject revision")
                self.store.db.execute("INSERT INTO decisions VALUES(?,?,?,?)",
                                      (request_id, decision, reviewer, time.time()))
            self.store.event("approval:" + request_id, "decision", {
                "decision": decision, "reviewer": reviewer, "subject_digest": expected_digest})
            self.store.db.execute("COMMIT")
        except BaseException:
            self.store.db.execute("ROLLBACK")
            raise
        return self.get(request_id)

    def require(self, request_id, action, subject):
        request = self.get(request_id)
        if request["status"] != "APPROVED" or request["action"] != action or request["subject_digest"] != digest(subject):
            raise PolicyError("Exact current approval required")
        return request
