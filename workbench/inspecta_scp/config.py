"""Single configuration resolver used by every client; never parses goal prose."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path


class PolicyError(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def merge(base, override):
    result = copy.deepcopy(base)
    for key, value in override.items():
        result[key] = (merge(result[key], value)
                       if isinstance(value, dict) and isinstance(result.get(key), dict)
                       else copy.deepcopy(value))
    return result


OPERATIONS = {"auto", "continue-project", "complete-system", "extend-system",
              "repair-system", "verify-only", "create-system"}
GATES = {"parse_type", "architecture_capture", "hamr_codegen", "integration_constraints", "configured_formal_verification", "configured_build",
         "requirements_coverage", "architecture", "independent_requirements_tests", "review"}


def default_toolchain():
    """Workspace-selected default; explicit profiles/overrides still take precedence."""
    path = Path(__file__).resolve().parents[1] / "default-toolchain.json"
    if not path.is_file():
        return {"sireum": None, "sireum_sha256": None, "integration_solver": "auto"}
    value = json.loads(path.read_text())
    if set(value) != {"sireum", "sireum_sha256", "integration_solver"}:
        raise PolicyError("Invalid workspace default toolchain")
    return value


def defaults(mode):
    if mode not in ("learning", "user"):
        raise PolicyError("Mode must be learning or user")
    learning = mode == "learning"
    return {
        "schema_version": 1, "mode": mode, "assistance": "automatic",
        "task_operation": "auto", "creation_authorized": False,
        "naming_policy": "preserve-existing", "rename_authorized": False,
        "project": None, "input_files": [], "model_file": None,
        "required_gates": ["parse_type", "requirements_coverage", "architecture",
                           "independent_requirements_tests", "configured_formal_verification",
                           "configured_build", "review"],
        **default_toolchain(), "hamr_platform": "JVM",
        "learning_materials": None, "development_validation": None, "final_evaluation": None,
        "dataset_assignment": None, "dataset_task": None,
        "model": {"family": "gpt", "requested_profile": "astra", "resolved_model_id": None},
        "rule_release": None, "paid_runs_authorized": False,
        "architecture_policy": None, "requirement_ledger": None, "unit_registry": None, "repair_allowed_files": [],
        "budget": {"wall_seconds": 3600 if learning else 1200,
                   "aggregate_model_tokens": 3000000 if learning else 1000000,
                   "repairs_per_issue": 5 if learning else 3,
                   "repairs_per_run": 20 if learning else 8,
                   "concurrent_model_calls": 1, "final_validation_time_reserve": 0.2,
                   "enforcement": "strict"},
    }


def relative_file(value):
    if not isinstance(value, str) or not value:
        raise PolicyError("Input path must be a nonempty string")
    p = Path(value)
    if p.is_absolute() or ".." in p.parts or "\\" in value:
        raise PolicyError("Input files must be relative paths without traversal")
    if any(part.startswith(".") or part.lower() in {
        "eva-results", "eval_results", "truth-values", "golden_examples",
        "node_modules", "__pycache__"} for part in p.parts):
        raise PolicyError("Secret, hidden, historical evaluation or generated-cache path excluded")
    if p.suffix.lower() in {".pem", ".key", ".p12", ".pfx"}:
        raise PolicyError("Credential file excluded")
    return p.as_posix()


def resolve(profile=None, overrides=None, base_dir=None):
    profile, overrides = profile or {}, overrides or {}
    mode = overrides.get("mode", profile.get("mode", "user"))
    config = merge(merge(defaults(mode), profile), overrides)
    unknown = set(config) - set(defaults(mode))
    if unknown:
        raise PolicyError("Unknown configuration fields: " + ", ".join(sorted(unknown)))
    if config["schema_version"] != 1 or config["assistance"] not in ("automatic", "interactive"):
        raise PolicyError("Unsupported schema or assistance")
    op = config["task_operation"]
    if op not in OPERATIONS:
        raise PolicyError("Unknown task operation")
    if config["creation_authorized"] is not False and config["creation_authorized"] is not True:
        raise PolicyError("creation_authorized must be boolean")
    if op == "create-system" and config["creation_authorized"] is not True:
        raise PolicyError("Creation needs explicit authorization")
    if config["naming_policy"] not in ("preserve-existing", "consistent-internal-renaming"):
        raise PolicyError("Unknown naming policy")
    if config["naming_policy"] != "preserve-existing" and config["rename_authorized"] is not True:
        raise PolicyError("Renaming requires explicit authorization")
    if not isinstance(config["model"], dict) or config["model"].get("family") != "gpt":
        raise PolicyError("GPT-only model policy")
    if config['hamr_platform'] not in {'JVM','Microkit'}:raise PolicyError('Unsupported HAMR platform')
    budget = config["budget"]
    if not isinstance(budget, dict) or set(budget) != set(defaults(mode)["budget"]):
        raise PolicyError("Invalid budget fields")
    for key in ("wall_seconds", "aggregate_model_tokens", "repairs_per_issue", "repairs_per_run", "concurrent_model_calls"):
        value = budget[key]
        minimum = 0 if key.startswith("repairs_") else 1
        if type(value) is not int or value < minimum:
            raise PolicyError(key + " must be an integer within bounds")
    if budget["concurrent_model_calls"] != 1:
        raise PolicyError("Only one concurrent model call is supported")
    reserve = budget["final_validation_time_reserve"]
    if type(reserve) not in (int, float) or not 0 <= reserve < 1:
        raise PolicyError("Invalid final-validation reserve")
    if budget["enforcement"] not in ("strict", "best_effort"):
        raise PolicyError("Unknown enforcement policy")
    base = Path(base_dir or Path.cwd()).resolve()
    for key in ("project", "sireum", "learning_materials", "development_validation", "final_evaluation", "rule_release"):
        value = config[key]
        if value is not None:
            if not isinstance(value, str) or not value:
                raise PolicyError(key + " must be a path or null")
            config[key] = str((base / Path(value).expanduser()).resolve())
    roles = [Path(config[k]) for k in ("learning_materials", "development_validation", "final_evaluation") if config[k]]
    for i, a in enumerate(roles):
        for b in roles[i + 1:]:
            if a == b or a in b.parents or b in a.parents:
                raise PolicyError("Dataset role directories overlap")
    if (config['dataset_assignment'] is None) != (config['dataset_task'] is None):
        raise PolicyError('Dataset assignment and selected task must be supplied together')
    if config['dataset_task'] is not None and (not isinstance(config['dataset_task'], str) or not config['dataset_task'].strip()):
        raise PolicyError('Dataset task must be nonempty text')
    for key in ("architecture_policy", "requirement_ledger", "unit_registry", "dataset_assignment"):
        value = config[key]
        if value is not None and (not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value)):
            raise PolicyError(key + " must be an immutable record ID or null")
    files = config["input_files"]
    if not isinstance(files, list) or not files or len(files) != len(set(files)):
        raise PolicyError("Declare a nonempty unique input file allowlist")
    config["input_files"] = sorted(relative_file(p) for p in files)
    editable = config["repair_allowed_files"]
    if not isinstance(editable, list) or len(set(editable)) != len(editable) or not set(editable) <= set(files):
        raise PolicyError("Repair edit scope must be a unique subset of declared inputs")
    config["repair_allowed_files"] = sorted(relative_file(p) for p in editable)
    if any(Path(p).suffix.lower() not in {".sysml", ".scala", ".rs", ".aadl"} for p in editable):
        raise PolicyError("Repair scope only supports model/implementation source files")
    if config["model_file"] is not None:
        config["model_file"] = relative_file(config["model_file"])
        if config["model_file"] not in files:
            raise PolicyError("Model file must be in the input allowlist")
    gates = config["required_gates"]
    if config['integration_solver'] not in {'auto','cvc5','z3'}:
        raise PolicyError('Choose a recognized integration solver profile')
    if not isinstance(gates, list) or not gates or len(set(gates)) != len(gates) or not set(gates) <= GATES:
        raise PolicyError("Required gates must be nonempty, unique and recognized")
    # Auto records intent without promoting an empty folder to creation permission.
    config["resolved_operation"] = "continue-project" if op == "auto" else op
    return {"config": config, "config_sha256": digest(config),
            "precedence": ["defaults", "profile", "explicit_overrides", "policy_validation"]}
