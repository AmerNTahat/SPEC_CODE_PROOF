"""SQLite event/state transactions and content-addressed evidence."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sqlite3
import time
import uuid
import re
import tempfile

from .config import PolicyError, canonical


def sha_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def safe_child(root, relative):
    root = Path(root).resolve()
    p = root / relative
    if Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise PolicyError("Path escapes root")
    for part in [p, *p.parents]:
        if part == root:
            break
        if part.is_symlink():
            raise PolicyError("Symlinks are not permitted in run inputs or state")
    try:
        p.resolve().relative_to(root)
    except ValueError as exc:
        raise PolicyError("Path escapes root") from exc
    return p


class Store:
    def __init__(self, root):
        self.root = Path(root).absolute()
        if any(p.is_symlink() for p in [self.root, *self.root.parents]):
            raise PolicyError("State path must not contain symlinks")
        self.root.mkdir(parents=True, exist_ok=True)
        for name in ("runs", "objects"):
            safe_child(self.root, name).mkdir(exist_ok=True)
        db = safe_child(self.root, "workbench.sqlite3")
        self.db = sqlite3.connect(db, timeout=10, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
          PRAGMA journal_mode=WAL;
          CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY, state TEXT NOT NULL, config TEXT NOT NULL,
            config_hash TEXT NOT NULL, created REAL NOT NULL, deadline REAL NOT NULL,
            used_tokens INTEGER NOT NULL DEFAULT 0, usage_unknown INTEGER NOT NULL DEFAULT 0,
            reserved_tokens INTEGER NOT NULL DEFAULT 0, worker INTEGER,
            result TEXT, version INTEGER NOT NULL DEFAULT 0);
          CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL,
            timestamp REAL NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS reservations (
            id TEXT PRIMARY KEY, run_id TEXT NOT NULL, tokens INTEGER NOT NULL,
            settled INTEGER NOT NULL DEFAULT 0);
          CREATE TABLE IF NOT EXISTS records (
            kind TEXT NOT NULL, id TEXT NOT NULL, payload TEXT NOT NULL,
            PRIMARY KEY(kind,id));
          CREATE TABLE IF NOT EXISTS decisions (
            request_id TEXT PRIMARY KEY, decision TEXT NOT NULL,
            reviewer TEXT NOT NULL, decided REAL NOT NULL);
          CREATE TABLE IF NOT EXISTS campaigns (
            id TEXT PRIMARY KEY, started REAL, used_tokens INTEGER NOT NULL DEFAULT 0,
            reserved_tokens INTEGER NOT NULL DEFAULT 0, usage_unknown INTEGER NOT NULL DEFAULT 0);
          CREATE TABLE IF NOT EXISTS campaign_usage (
            call_id TEXT PRIMARY KEY, complete INTEGER NOT NULL, known_tokens INTEGER NOT NULL);
          CREATE TABLE IF NOT EXISTS campaign_adjustments (
            call_id TEXT PRIMARY KEY, debit INTEGER NOT NULL, consent TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS campaign_calls (
            id TEXT PRIMARY KEY, campaign_id TEXT NOT NULL, reserved INTEGER NOT NULL,
            settled INTEGER NOT NULL DEFAULT 0);
        """)

    def close(self):
        self.db.close()

    def event(self, run_id, kind, payload):
        self.db.execute("INSERT INTO events(run_id,timestamp,kind,payload) VALUES(?,?,?,?)",
                        (run_id, time.time(), kind, canonical(payload)))

    def get(self, run_id):
        row = self.db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        if row is None:
            raise PolicyError("Unknown run")
        result = dict(row)
        result["config"] = json.loads(result["config"])
        result["result"] = json.loads(result["result"]) if result["result"] else None
        result["remaining_seconds"] = max(0, result["deadline"] - time.time())
        result["remaining_tokens"] = (None if result["usage_unknown"] else max(
            0, result["config"]["budget"]["aggregate_model_tokens"] - result["used_tokens"] - result["reserved_tokens"]))
        return result

    def create(self, resolved):
        run_id = uuid.uuid4().hex
        now = time.time()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.db.execute("INSERT INTO runs(id,state,config,config_hash,created,deadline) VALUES(?,?,?,?,?,?)",
                            (run_id, "CREATED", canonical(resolved["config"]), resolved["config_sha256"], now,
                             now + resolved["config"]["budget"]["wall_seconds"]))
            self.event(run_id, "created", resolved)
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
        folder = safe_child(self.root, "runs/" + run_id)
        folder.mkdir()
        (folder / "resolved-config.json").write_text(canonical(resolved) + "\n")
        return run_id

    def change(self, run_id, expected, state, payload=None, worker=None):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            old = self.get(run_id)
            if old["state"] not in expected:
                raise PolicyError("Transition is not valid from " + old["state"])
            self.db.execute("UPDATE runs SET state=?,worker=?,version=version+1 WHERE id=?",
                            (state, worker, run_id))
            self.event(run_id, "state", {"from": old["state"], "to": state, **(payload or {})})
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def finish(self, run_id, result):
        """Commit result and worker acknowledgement together; late controls win."""
        self.db.execute("BEGIN IMMEDIATE")
        try:
            run = self.get(run_id)
            if run["state"] not in {"CHECKING", "PAUSE_REQUESTED", "STOP_REQUESTED"}:
                raise PolicyError("Worker no longer owns finalization")
            state = result["task_status"]
            if run["state"] == "STOP_REQUESTED":
                state = "CANCELLED"
            elif run["state"] == "PAUSE_REQUESTED":
                state = "PAUSED"
            elif run["remaining_seconds"] <= 0:
                state = "BUDGET_EXHAUSTED"
            result = {**result, "task_status": state}
            self.db.execute("UPDATE runs SET result=?,state=?,worker=NULL,version=version+1 WHERE id=?",
                            (canonical(result), state, run_id))
            self.event(run_id, "state", {"from": run["state"], "to": state, "result_committed": True})
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def object(self, value):
        data = canonical(value).encode()
        digest = hashlib.sha256(data).hexdigest()
        p = safe_child(self.root, "objects/" + digest + ".json")
        fd, temporary = tempfile.mkstemp(dir=p.parent, prefix=".object-")
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(temporary, p)
            except FileExistsError:
                if p.is_symlink() or p.read_bytes() != data:
                    raise PolicyError("Content-addressed evidence was modified")
        finally:
            os.unlink(temporary)
        return {"sha256": digest, "path": str(p.relative_to(self.root))}

    def load_object(self, reference):
        key = reference.get("sha256", "")
        if not re.fullmatch(r"[0-9a-f]{64}", key):
            raise PolicyError("Invalid object digest")
        relative = "objects/" + key + ".json"
        if reference.get("path", relative) != relative:
            raise PolicyError("Object reference path does not match digest")
        path = safe_child(self.root, relative)
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != key:
            raise PolicyError("Evidence object was modified")
        return json.loads(data)

    def record(self, kind, value):
        ref = self.object(value)
        key = ref["sha256"]
        self.db.execute("INSERT OR IGNORE INTO records VALUES(?,?,?)", (kind, key, canonical(ref)))
        return {**value, "id": key}

    def read_record(self, kind, key):
        row = self.db.execute("SELECT payload FROM records WHERE kind=? AND id=?", (kind, key)).fetchone()
        if row is None:
            raise PolicyError("Unknown " + kind + " record")
        ref = json.loads(row["payload"])
        if ref["sha256"] != key:
            raise PolicyError("Record identity changed")
        return {**self.load_object(ref), "id": key}

    def records(self, kind):
        return [self.read_record(kind, row[0]) for row in self.db.execute(
            "SELECT id FROM records WHERE kind=? ORDER BY id", (kind,)).fetchall()]

    def events(self, run_id):
        self.get(run_id)
        return [{**dict(row), "payload": json.loads(row["payload"])} for row in
                self.db.execute("SELECT * FROM events WHERE run_id=? ORDER BY id", (run_id,))]

    def reserve(self, run_id, tokens):
        if type(tokens) is not int or tokens <= 0:
            raise PolicyError("Positive reservation required")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            run = self.get(run_id)
            if run["state"] != "RUNNING" or run["remaining_seconds"] <= 0:
                raise PolicyError("Run is not executing within its deadline")
            if self.db.execute("SELECT 1 FROM reservations WHERE run_id=? AND settled=0", (run_id,)).fetchone():
                raise PolicyError("A model reservation is already in flight")
            if run["remaining_tokens"] is None or tokens > run["remaining_tokens"]:
                raise PolicyError("Budget unavailable or exhausted")
            reservation = uuid.uuid4().hex
            self.db.execute("INSERT INTO reservations VALUES(?,?,?,0)", (reservation, run_id, tokens))
            self.db.execute("UPDATE runs SET reserved_tokens=reserved_tokens+? WHERE id=?", (tokens, run_id))
            self.event(run_id, "reserved", {"reservation": reservation, "tokens": tokens})
            self.db.execute("COMMIT")
            return reservation
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def settle(self, reservation, usage, complete=True):
        if type(complete) is not bool:
            raise PolicyError('Usage completeness must be boolean')
        if usage is not None:
            for key in ("input_tokens", "output_tokens", "cached_input_tokens"):
                if type(usage.get(key)) is not int or usage[key] < 0:
                    raise PolicyError("Invalid usage")
            if usage["cached_input_tokens"] > usage["input_tokens"]:
                raise PolicyError("Cached input is a subset of input")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute("SELECT * FROM reservations WHERE id=?", (reservation,)).fetchone()
            if row is None or row["settled"]:
                raise PolicyError("Unknown or already settled reservation")
            total = usage["input_tokens"] + usage["output_tokens"] if usage is not None else 0
            self.db.execute("UPDATE runs SET used_tokens=used_tokens+?,reserved_tokens=reserved_tokens-?,usage_unknown=MAX(usage_unknown,?) WHERE id=?",
                            (total, row["tokens"], int(usage is None or not complete), row["run_id"]))
            self.db.execute("UPDATE reservations SET settled=1 WHERE id=?", (reservation,))
            self.event(row["run_id"], "usage", {"reservation": reservation, "usage": usage,
                       "usage_complete": complete and usage is not None,
                       "known_total": total if usage is not None else None,
                       "reservation_overshoot": max(0, total - row["tokens"]) if usage is not None else None})
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
