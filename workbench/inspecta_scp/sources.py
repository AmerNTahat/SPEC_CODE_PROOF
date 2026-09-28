"""Registered immutable source snapshots with role-aware, read-only access."""
from pathlib import Path
import hashlib

from .config import PolicyError, relative_file
from .storage import safe_child, sha_file


class Sources:
    ROLES = {"learning", "development", "evaluator", "shared"}

    def __init__(self, store):
        self.store = store

    def register_root(self, path, role):
        path = Path(path).absolute()
        if role not in self.ROLES:
            raise PolicyError("Unknown source role")
        if not path.is_dir() or any(p.is_symlink() for p in [path, *path.parents]):
            raise PolicyError("Source root must be an existing directory without symlinks")
        return self.store.record("source_root", {"path": str(path), "role": role})

    def register(self, root_id, relative):
        root = self.store.read_record("source_root", root_id)
        self.check_root(root)
        # Evaluator files can be registered inside their separate root, not via
        # traversal or by weakening hidden/credential-file exclusions.
        rel = relative_file(relative)
        path = safe_child(Path(root["path"]), rel)
        if not path.is_file() or path.stat().st_size > (32 if path.suffix.lower() == ".pdf" else 4) * 1024 * 1024:
            raise PolicyError("Missing, nonregular or oversized source")
        if path.suffix.lower() not in {".pdf", ".md", ".txt", ".json", ".sysml", ".aadl", ".scala", ".rs"}:
            raise PolicyError("Unsupported source format; no fabricated viewer")
        data = path.read_bytes()
        extractor = None
        if path.suffix.lower() == ".pdf":
            from .pdf_context import extract_pdf
            text, extractor = extract_pdf(path)
        else:text = data.decode("utf-8")
        content = self.store.object({"text": text})
        return self.store.record("source", {"root_id": root_id, "relative": rel,
                                "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
                                "role": root["role"], "content": content,
                                "text_sha256": hashlib.sha256(text.encode()).hexdigest(), "extractor": extractor,
                                "generator_visible": root["role"] == "shared"})

    @staticmethod
    def check_root(root):
        path = Path(root["path"])
        if not path.is_dir() or any(p.is_symlink() for p in [path, *path.parents]):
            raise PolicyError("Registered source root is missing or has become a symlink")

    def view(self, source_id, audience="human", start=1, end=None):
        if audience not in {"human", "generator"}:
            raise PolicyError("Unknown source audience")
        source = self.store.read_record("source", source_id)
        if audience == "generator" and not source["generator_visible"]:
            raise PolicyError("Source is human-review only, not exported generator context")
        root = self.store.read_record("source_root", source["root_id"])
        state = "CURRENT"
        try:
            self.check_root(root)
            path = safe_child(Path(root["path"]), source["relative"])
            if sha_file(path) != source["sha256"]:
                state = "STALE"
        except (OSError, PolicyError):
            state = "BROKEN"
        if audience == "generator" and state != "CURRENT":
            raise PolicyError("Generator source is stale or missing")
        text = self.store.load_object(source["content"])["text"]
        if hashlib.sha256(text.encode()).hexdigest() != source.get("text_sha256",source["sha256"]):
            raise PolicyError("Source content identity changed")
        lines = text.splitlines(keepends=True)
        end = len(lines) if end is None else end
        if type(start) is not int or type(end) is not int or start < 1 or end < start - 1 or end > len(lines):
            raise PolicyError("Invalid source passage")
        return {**source, "freshness": state, "start_line": start, "end_line": end,
                "text": "".join(lines[start - 1:end]),
                "content_type": "text/plain", "scope": "Exact registered revision; never execute or render as HTML"}
