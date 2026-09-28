#!/usr/bin/env python3
"""Validate local starter JSON Schemas/examples. Requires jsonschema; performs no downloads."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    args=p.parse_args(); root=args.root.resolve()
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        print("BLOCKED: Python jsonschema package not installed. This checker does not install it or claim validation.",file=sys.stderr)
        return 2
    errors=[]; schemas=0; examples=0
    for schema_path in sorted((root/'schemas').glob('*.schema.json')):
        try:
            Draft202012Validator.check_schema(json.loads(schema_path.read_text()))
            schemas+=1
        except Exception as exc:
            errors.append(f"{schema_path.name}: {exc}")
    for folder in ('configs','templates'):
        for example in sorted((root/folder).rglob('*.json')):
            try:
                value=json.loads(example.read_text())
                ref=value.get('$schema')
                if not ref: continue
                if '://' in ref: raise ValueError('Example must refer to a local schema')
                schema_path=(example.parent/ref).resolve()
                schema_path.relative_to(root/'schemas')
                schema=json.loads(schema_path.read_text())
                Draft202012Validator(schema).validate(value)
                examples+=1
            except Exception as exc:
                errors.append(f"{example.relative_to(root)}: {exc}")
    print(json.dumps({'ok':not errors,'schemas_validated':schemas,'examples_validated':examples,'errors':errors,
                      'scope':'Syntax/schema only, not readiness or engineering acceptance.'},indent=2))
    return 0 if not errors else 1
if __name__=='__main__': raise SystemExit(main())
