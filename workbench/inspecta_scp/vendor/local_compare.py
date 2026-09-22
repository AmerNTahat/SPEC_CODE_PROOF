#!/usr/bin/env python3
"""Offline lexical diagnostics. Not semantic, structural, or engineering acceptance."""
from __future__ import annotations
import argparse
from collections import Counter
from difflib import SequenceMatcher
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from typing import Any

TOKENIZER_VERSION = "lexical-preserve-v1"
TOKEN_RE = re.compile(
    r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|'
    r'<=>|==>|<->|<=|>=|!=|==|&&|\|\||->|=>|::|:=|'
    r'(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?|'
    r'(?:[^\W\d]|_)\w*|[^\s]', re.UNICODE
)

def tokenize(text: str) -> list[str]:
    """Preserve case/operators/numbers/strings. Does not parse SysML or remove comments."""
    return TOKEN_RE.findall(text)

def cosine_counts(left: list[str], right: list[str]) -> float | None:
    """Unordered count-vector cosine; undefined if either vector is empty."""
    a, b = Counter(left), Counter(right)
    if not a or not b:
        return None
    numerator = sum(v * b.get(k, 0) for k, v in a.items())
    denominator = math.sqrt(sum(v*v for v in a.values()) * sum(v*v for v in b.values()))
    return min(1.0, max(0.0, numerator / denominator))

def sequence_edits(left: list[str], right: list[str]) -> int:
    """Count deleted+inserted tokens on SequenceMatcher alignment; not minimal edit distance."""
    count = 0
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, left, right, autojunk=False).get_opcodes():
        if tag == "replace":
            count += (i2-i1) + (j2-j1)
        elif tag == "delete":
            count += i2-i1
        elif tag == "insert":
            count += j2-j1
    return count

def compare_text(left: str, right: str) -> dict[str, Any]:
    a, b = tokenize(left), tokenize(right)
    cosine = cosine_counts(a, b)
    edits = sequence_edits(a, b)
    return {
        "artifact_kind": "LEXICAL_DIAGNOSTIC_NOT_ACCEPTANCE",
        "tokenizer_version": TOKENIZER_VERSION,
        "left_tokens": len(a), "right_tokens": len(b),
        "cosine_status": "UNDEFINED_EMPTY_VECTOR" if cosine is None else "DEFINED",
        "cosine_similarity": cosine,
        "cosine_distance": None if cosine is None else 1.0-cosine,
        "sequence_deleted_plus_inserted": edits,
        "sequence_edit_fraction": None if not (a or b) else edits/(len(a)+len(b)),
        "line_deleted_plus_inserted": sequence_edits(left.splitlines(), right.splitlines()),
        "left_utf8_sha256": hashlib.sha256(left.encode("utf-8")).hexdigest(),
        "right_utf8_sha256": hashlib.sha256(right.encode("utf-8")).hexdigest(),
        "semantic_equivalence": "NOT_ESTABLISHED",
        "architecture_check": "NOT_RUN",
        "acceptance": "NOT_ASSESSED",
        "limitations": [
            "Count cosine discards order and role bindings; equal vectors may encode different behavior.",
            "Token sequence diagnostics are not a parser, proof, or minimum-edit metric.",
            "No source/contract ownership extraction, requirement check, or model call is performed."
        ]
    }

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    parser.add_argument("--output", type=Path, help="Create a new JSON file; never overwrite an existing file.")
    args = parser.parse_args(argv)
    try:
        # read_bytes avoids implicit newline normalization, preserving exact UTF-8 identity
        result = compare_text(args.left.read_bytes().decode("utf-8"), args.right.read_bytes().decode("utf-8"))
        encoded = json.dumps(result, indent=2, ensure_ascii=False)+"\n"
        if args.output:
            with args.output.open("x", encoding="utf-8") as handle:
                handle.write(encoded)
        else:
            sys.stdout.write(encoded)
    except (OSError, UnicodeError) as exc:
        print(f"Comparison failed: {exc}", file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
