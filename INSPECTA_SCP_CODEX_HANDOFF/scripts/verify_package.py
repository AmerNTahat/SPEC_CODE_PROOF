#!/usr/bin/env python3
"""Verify this handoff's SHA-256 manifest. Integrity only, not signed authenticity or engineering attestation."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys


def verify(root: Path, manifest: str = "SHA256SUMS") -> dict:
    root = root.resolve()
    errors: list[str] = []
    checked=0
    expected: set[str] = set()
    try:
        lines=(root/manifest).read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return {"ok": False, "files_checked": 0, "errors": [f"Cannot read manifest: {exc}"]}
    for line in lines:
        match=re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            errors.append("Malformed manifest entry"); continue
        digest, name=match.groups()
        rel=PurePosixPath(name)
        if rel.is_absolute() or ".." in rel.parts or "\\" in name or ":" in name:
            errors.append(f"Unsafe relative name: {name}"); continue
        if name in expected:
            errors.append(f"Duplicate manifest name: {name}"); continue
        expected.add(name)
        path=root.joinpath(*rel.parts)
        try:
            path.resolve().relative_to(root)
            if any(part.is_symlink() for part in [path, *path.parents] if part != root and root in part.parents):
                raise ValueError("Symlink is not permitted")
            if not path.is_file(): raise ValueError("Missing regular file")
            hasher=hashlib.sha256()
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024*1024), b""): hasher.update(chunk)
            if hasher.hexdigest() != digest: errors.append(f"Digest mismatch: {name}")
            checked += 1
        except (OSError, ValueError) as exc:
            errors.append(f"Invalid file {name}: {exc}")
    extras=[]
    for p in root.rglob("*"):
        if p.is_file() or p.is_symlink():
            name=p.relative_to(root).as_posix()
            if name != manifest and name not in expected:
                extras.append(name)
    if extras: errors.append("Unlisted files: "+", ".join(sorted(extras)))
    return {"ok": not errors, "files_checked": checked, "errors": errors,
            "scope": "Package-integrity check only; no trusted signature, toolchain validation, or engineering acceptance."}


def main(argv: list[str] | None = None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    args=parser.parse_args(argv)
    result=verify(args.root)
    print(json.dumps(result,indent=2))
    return 0 if result["ok"] else 1
if __name__ == "__main__": raise SystemExit(main())
