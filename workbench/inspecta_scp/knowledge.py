"""Versioned rule library. Import is provenance, never verification or approval."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
import re

from .approvals import Approvals
from .config import PolicyError, canonical, digest
from .sources import Sources
from .vendor.local_compare import compare_text


RULE_ID = re.compile(r"\bMR-[A-Z0-9]+(?:-[A-Z0-9]+)*\b")
FORBIDDEN = {"eva-results", "eval_results", "verification-profiles", "truth-values",
             "golden_examples", "repair-logs", "verification-logs"}


def validate_schema(value, name):
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise PolicyError("Install the pinned Workbench jsonschema dependency in a local environment") from exc
    schema = json.loads((Path(__file__).resolve().parents[1] / "schemas" / name).read_text())
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda e: str(e.path))
    if errors:
        raise PolicyError("Schema validation: " + errors[0].message)


class Knowledge:
    def __init__(self, store):
        self.store = store
        self.sources = Sources(store)
        self.approvals = Approvals(store)

    def export_learned_books(self):
        """Readable immutable draft snapshots alongside the authoritative records."""
        from .storage import safe_child
        records=self.store.records('candidate_rule')
        extractions=self.store.records('learning_extraction')
        bundle={'format_version':'learned-rulebook-v2','state':'DRAFT_NOT_PUBLISHED','candidates':records,'extractions':extractions,
                'reviews':self.store.records('rule_review'),
                'qualification_coverage_notes':self.store.records('golden_coverage_note'),
                'scope':'Learned proposals and provenance; neither imported original books nor a verified release'}
        identity=digest(bundle);root=safe_child(self.store.root,'learned-rulebooks');root.mkdir(exist_ok=True)
        folder=safe_child(root,identity);folder.mkdir(exist_ok=True)
        lines=['# Learned draft rulebook','', 'DRAFT — not a validated or published User release.',
               '', 'Each candidate keeps its own immutable identity. Repeated rule names are not merged.', '']
        if bundle['qualification_coverage_notes']:
            lines += ['## Features not covered in the golden example yet', '',
                      'Qualification disclosures only; these notes are excluded from reusable rule prompts and do not certify any candidate.', '']
            for note in bundle['qualification_coverage_notes']:
                lines += ['### '+note['feature'], '', 'Not supported in golden yet.', '',
                          note['english_requirement'], '', note['golden_observation'], '',
                          note['qualification_effect'], '', 'Revisit: '+note['revisit_condition'], '']
        for candidate in records:
            r=candidate['record'];lines += ['## '+str(r['id'])+' · revision '+str(r['revision']),'',r['principle'],'',
                'Candidate: `'+candidate['id']+'`','']
            focuses=sorted({x.get('focus','full_stack') for x in extractions if x.get('candidate_id')==candidate['id']})
            lines += ['Extraction focus: '+(', '.join(focuses) or 'not recorded'),'']
            for field in ['trigger','semantic_roles','prerequisites','preserved_obligations','formal_output_pattern','counterexample','repair_gate','exclusions','source_references','notes']:
                if field in r:lines += ['### '+field.replace('_',' ').capitalize(),'','```json',json.dumps(r[field],indent=2,ensure_ascii=False),'```','']
        artifacts={'rulebook.json':json.dumps(bundle,indent=2,ensure_ascii=False)+'\n','RULEBOOK.md':'\n'.join(lines)}
        for name,text in artifacts.items():
            path=safe_child(folder,name)
            if path.exists() and path.read_text()!=text:raise PolicyError('Learned book snapshot was modified')
            if not path.exists():path.write_text(text)
        receipt=self.store.record('learned_book_export',{'snapshot_id':identity,'directory':str(folder),
            'candidate_count':len(records),'state':'DRAFT_NOT_PUBLISHED','files':list(artifacts),
            'content_hashes':{k:hashlib.sha256(v.encode()).hexdigest() for k,v in artifacts.items()}})
        index=safe_child(root,'INDEX.md')
        if index.exists() and not index.read_text().startswith('# Workbench learned book index\n'):
            raise PolicyError('Refusing to replace an unrecognized book index')
        index.write_text('# Workbench learned book index\n\nCurrent draft: ['+identity+']('+identity+'/RULEBOOK.md)\n\n'+str(len(records))+' candidates. Original books are unchanged. No publication or verification is implied.\n')
        return receipt

    def read_learned_book(self,export_id):
        from .storage import safe_child,sha_file
        receipt=self.store.read_record('learned_book_export',export_id)
        folder=safe_child(self.store.root,'learned-rulebooks/'+receipt['snapshot_id'])
        path=safe_child(folder,'RULEBOOK.md')
        if sha_file(path)!=receipt.get('content_hashes',{}).get('RULEBOOK.md'):
            raise PolicyError('Book content changed or predates content-bound export; export again')
        return {'export':receipt,'text':path.read_text()}

    def import_books(self, directory):
        root = self.sources.register_root(directory, "learning")
        directory = Path(root["path"])
        documents, variants, skipped = [], [], []
        for path in sorted(directory.rglob("*")):
            rel = path.relative_to(directory)
            if any(part.startswith(".") or part.lower() in FORBIDDEN or
                   "snapshot" in part.lower() or "clean-profile" in part.lower() for part in rel.parts):
                skipped.append(rel.as_posix())
                continue
            if path.is_symlink():
                skipped.append(rel.as_posix())
                continue
            if not path.is_file() or path.suffix.lower() not in {".json", ".md", ".txt"}:
                continue
            source = self.sources.register(root["id"], rel.as_posix())
            raw = self.sources.view(source["id"])["text"]
            ids = sorted(set(RULE_ID.findall(raw)))
            doc = self.store.record("book", {"source_id": source["id"], "path": rel.as_posix(),
                                    "sha256": source["sha256"], "rule_ids": ids,
                                    "status": "SOURCE_ONLY_PENDING_REVIEW"})
            documents.append(doc["id"])
            if path.suffix.lower() == ".json":
                try:
                    data = json.loads(raw)
                except ValueError:
                    skipped.append(rel.as_posix() + ": invalid JSON preserved as source")
                    continue
                records = data if isinstance(data, list) else data.get("rules", []) if isinstance(data, dict) else []
                if isinstance(data, dict) and "rule_id" in data:
                    records = [data]
                if not isinstance(records, list):
                    continue
                for record in records:
                    if not isinstance(record, dict) or not RULE_ID.fullmatch(str(record.get("rule_id", ""))):
                        continue
                    variant = self.store.record("legacy_rule", {"rule_id": record["rule_id"], "record": record,
                                                     "status": "IMPORTED_UNVALIDATED"})
                    self.store.record("rule_origin", {"variant_id": variant["id"], "source_id": source["id"]})
                    variants.append(variant["id"])
        imported = self.store.record("library_import", {"root_id": root["id"], "documents": documents,
                              "variants": sorted(set(variants)), "skipped": skipped,
                              "source_files_modified": 0, "model_calls": 0})
        return {**imported, "document_count": len(documents), "variant_count": len(set(variants))}

    def catalog(self):
        docs = self.store.records("book")
        origins = self.store.records("rule_origin")
        rules = {}
        for doc in docs:
            for rid in doc["rule_ids"]:
                rules.setdefault(rid, {"rule_id": rid, "documents": [], "variants": []})["documents"].append(doc["id"])
        for record in self.store.records("legacy_rule"):
            rid = record["rule_id"]
            rule = rules.setdefault(rid, {"rule_id": rid, "documents": [], "variants": []})
            rule["variants"].append({"id": record["id"], "record": record["record"],
                "sources": [o["source_id"] for o in origins if o["variant_id"] == record["id"]],
                "original_forecast": {"score": record["record"].get("confidence"),
                    "exact_question": record["record"].get("confidence_question"),
                    "interpretation": "historical model forecast; metadata may be incomplete; not measured success"}})
        for rule in rules.values():
            rule["status"] = "CONFLICT_REVIEW_REQUIRED" if len(rule["variants"]) > 1 else "SOURCE_ONLY_PENDING_REVIEW"
        return {"documents": docs, "rules": [rules[k] for k in sorted(rules)],
                "counts": {"documents": len(docs), "rule_ids": len(rules),
                           "conflicting_ids": sum(len(r["variants"]) > 1 for r in rules.values())},
                "scope": "Exact legacy variants and references; no rule auto-approved or counted as verified"}

    def propose(self, record):
        validate_schema(record, "knowledge.schema.json")
        if record["state"] != "DRAFT" or record["approval_reference"] is not None:
            raise PolicyError("Proposals must be unapproved drafts; supplied success labels grant no authority")
        if record["formal_pattern_status"] != "ABSTRACT_NOT_VALIDATED":
            raise PolicyError("Tool validation is established by trusted runs, not candidate labels")
        if record["record_type"] == "procedure":
            raise PolicyError("Executable procedures require the trusted operation registry")
        for key in ("id", "revision", "trigger", "principle", "semantic_choice", "structural_placement", "repair_gate"):
            if not record[key].strip():
                raise PolicyError("Empty rule field: " + key)
        if not record["source_references"] or not record["supported_operations"] or not record["target_compatibility"]:
            raise PolicyError("Sources, operations and target compatibility are required")
        if "auto" in record["supported_operations"]:
            raise PolicyError("Rule applicability must name resolved operations")
        refs = [self.sources.view(key) for key in record["source_references"]]
        if any(r["role"] == "evaluator" or r["freshness"] != "CURRENT" for r in refs):
            raise PolicyError("Evaluator, stale or broken material cannot support a reusable proposal")
        if sorted(record["source_artifact_hashes"]) != sorted(r["sha256"] for r in refs):
            raise PolicyError("Rule provenance hashes must match the exact source references")
        names = [p["name"] for p in record["parameters"]]
        if len(names) != len(set(names)):
            raise PolicyError("Parameter names must be unique")
        if not record["counterexample"]["scenario"].strip() or not record["counterexample"]["expected_difference"].strip():
            raise PolicyError("A discriminating counterexample is required")
        forecast = record["confidence_forecast_reference"]
        if forecast:
            self.store.read_record("forecast", forecast)
        return self.store.record("candidate_rule", {"record": record, "status": "DRAFT_PENDING_VALIDATION"})

    def forecast(self, record):
        validate_schema(record, "confidence.schema.json")
        if record["status"] == "REPORTED" and not record["exact_question"].strip():
            raise PolicyError("Reported confidence requires the exact question")
        return self.store.record("forecast", {"record": record,
                "provenance_status": "IMPORTED_FORECAST_PENDING_MODEL_EVENT_CORROBORATION"})

    def retrieve(self, query, operation, profile, release_id=None, distance_threshold=0.1):
        if type(distance_threshold) not in (int, float) or not 0 <= distance_threshold <= 0.3:
            raise PolicyError("Retrieval cosine distance threshold must be between 0 and 0.3")
        if release_id:
            records = self.release(release_id)["rules"]
        else:
            records = self.store.records("candidate_rule")
        matches = []
        for entry in records:
            record = entry["record"]
            if operation not in record["supported_operations"] or profile not in record["target_compatibility"]:
                continue
            comparison = compare_text(query, record["trigger"] + " " + record["principle"])
            if comparison['cosine_distance'] is None or comparison['cosine_distance'] > distance_threshold:
                continue
            matches.append({"distance_threshold": distance_threshold, "cosine_distance": comparison["cosine_distance"], "candidate_id": entry["id"], "rule_id": record["id"],
                            "lexical_score": comparison["cosine_similarity"],
                            "exclusions": record["exclusions"], "prerequisites": record["prerequisites"],
                            "status": "RELEASE_RULE" if release_id else "UNAPPROVED_CANDIDATE"})
        return sorted(matches, key=lambda r: (-(r["lexical_score"] or 0), r["candidate_id"]))

    def bind(self, candidate_id, operation, profile, target_roles, bindings, requirement_ids):
        candidate = self.store.read_record("candidate_rule", candidate_id)["record"]
        if operation not in candidate["supported_operations"] or profile not in candidate["target_compatibility"]:
            raise PolicyError("Rule does not apply to this operation/profile")
        names = {p["name"] for p in candidate["parameters"]}
        if set(bindings) != names or len(set(bindings.values())) != len(bindings):
            raise PolicyError("All parameters require distinct, consistent target identities")
        for parameter in candidate["parameters"]:
            target = target_roles.get(bindings[parameter["name"]])
            if not target or target.get("role") != parameter["role"] or not target.get("evidence_reference"):
                raise PolicyError("Target role must match with a reviewable evidence reference")
        if not requirement_ids or len(set(requirement_ids)) != len(requirement_ids):
            raise PolicyError("Unique target requirement IDs required")
        return self.store.record("binding", {"candidate_id": candidate_id, "operation": operation,
                                 "profile": profile, "target_roles": target_roles, "bindings": bindings,
                                 "requirement_ids": requirement_ids, "status": "DRAFT_REQUIRES_LEDGER_AND_ARCHITECTURE_CHECK"})

    def queue_lesson(self, run_id, candidate_id, lesson):
        run = self.store.get(run_id)
        if run["config"]["mode"] != "user":
            raise PolicyError("This queue captures User-mode lessons for future Learning review")
        self.store.read_record("candidate_rule", candidate_id)
        return self.store.record("lesson", {"run_id": run_id, "candidate_id": candidate_id,
                                "lesson": lesson, "status": "QUEUED_FOR_FUTURE_RELEASE",
                                "applied_release": run["config"]["rule_release"]})

    def review(self, candidate_id, supporting_run, contrasting_run):
        candidate = self.store.read_record("candidate_rule", candidate_id)
        # Use the controller's source/evidence freshness checks; caller-supplied
        # gate labels and imported historical 'accepted' strings are not evidence.
        from .controller import Controller
        controller = Controller(self.store.root)
        try:
            support = controller.status(supporting_run)
            contrast = controller.status(contrasting_run)
        finally:
            controller.close()
        if supporting_run == contrasting_run or support["config_hash"] == contrast["config_hash"]:
            raise PolicyError("Supporting and contrasting tasks must be separately declared")
        gates = candidate["record"]["validation_gate_ids"]
        blockers = []
        if not gates:
            blockers.append("No validation gates declared")
        for run, label in [(support, "support"), (contrast, "contrast")]:
            if not run.get("evidence_current_for_source"):
                blockers.append(label + " evidence is stale")
            results = {g["gate"]: g for g in (run.get("result") or {}).get("gates", [])}
            for gate in gates:
                if gate not in results or not results[gate].get("evidence"):
                    blockers.append(label + " missing executed gate " + gate)
            if label == "support" and any(results.get(g, {}).get("status") != "PASS" for g in gates):
                blockers.append("Supporting task did not pass all required gates")
            if label == "contrast" and not any(results.get(g, {}).get("status") == "FAIL" for g in gates):
                blockers.append("Contrasting task has no recorded distinguishing failure")
        # Current adapters do not establish requirement/architecture fidelity or
        # rule-causal transfer. Never let two arbitrary parser runs publish a rule.
        blockers.append("Independent rule-application/transfer attestation adapter is not implemented")
        return self.store.record("rule_review", {"candidate_id": candidate_id,
                    "supporting_run": supporting_run, "contrasting_run": contrasting_run,
                    "blockers": blockers, "status": "BLOCKED" if blockers else "TESTED"})

    def draft_release(self, candidate_ids):
        if not candidate_ids or len(set(candidate_ids)) != len(candidate_ids):
            raise PolicyError("Declare unique candidate revisions")
        records = [self.store.read_record("candidate_rule", key) for key in sorted(candidate_ids)]
        ids = [r["record"]["id"] for r in records]
        if len(set(ids)) != len(ids):
            raise PolicyError("Conflicting revisions of one rule cannot share a release")
        for entry in records:
            if not set(entry["record"]["dependencies"]) <= set(ids):
                raise PolicyError("Release has unresolved rule dependencies")
        # Exact export allowlist. Raw books, source text, diagnostic archives,
        # evaluator witnesses and learning conversations never enter this bundle.
        fields = {"id", "revision", "record_type", "basis", "trigger", "principle", "semantic_choice",
                  "structural_placement", "repair_gate", "prerequisites", "exclusions", "parameters",
                  "dependencies", "target_compatibility", "preserved_obligations", "counterexample",
                  "validation_gate_ids", "source_english_patterns", "positive_paraphrases",
                  "misleading_near_matches", "supported_operations", "stack_layers", "semantic_roles",
                  "formal_output_pattern", "formal_pattern_status", "allowed_edit_scope", "required_baseline"}
        exports = [{"id": r["id"], "record": {k: v for k, v in r["record"].items() if k in fields}} for r in records]
        for entry in exports:
            entry["record"]["counterexample"] = {
                key: value for key, value in entry["record"]["counterexample"].items()
                if key in {"scenario", "expected_difference"}}
        return self.store.record("release_draft", {"candidate_ids": sorted(candidate_ids), "rules": exports,
                                "status": "DRAFT_NOT_FOR_USER_EXECUTION", "export_policy": "sanitized-rule-fields-v1"})

    def request_publication(self, draft_id):
        draft = self.store.read_record("release_draft", draft_id)
        return self.approvals.request("publish_release", {"draft_id": draft_id, "draft_digest": digest(draft)})

    def publish(self, draft_id, approval_id):
        draft = self.store.read_record("release_draft", draft_id)
        self.approvals.require(approval_id, "publish_release", {"draft_id": draft_id, "draft_digest": digest(draft)})
        for candidate_id in draft["candidate_ids"]:
            record = self.store.read_record("candidate_rule", candidate_id)["record"]
            for source_id in record["source_references"]:
                if self.sources.view(source_id)["freshness"] != "CURRENT":
                    raise PolicyError("Source changed after release review")
            reviews = [r for r in self.store.records("rule_review") if r["candidate_id"] == candidate_id]
            if not any(r["status"] == "TESTED" and not r["blockers"] for r in reviews):
                raise PolicyError("Independent validation/transfer evidence required; approval alone cannot waive it")
        return self.store.record("release", {"draft_id": draft_id, "approval_id": approval_id,
                                "rules": draft["rules"], "status": "PUBLISHED"})

    def release(self, release_id):
        release = self.store.read_record("release", release_id)
        draft = self.store.read_record("release_draft", release["draft_id"])
        self.approvals.require(release["approval_id"], "publish_release",
                               {"draft_id": draft["id"], "draft_digest": digest(draft)})
        return release
