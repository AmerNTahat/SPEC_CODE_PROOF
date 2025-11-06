
from agents import function_tool
import json, os

@function_tool
def generate_gumbo(json_tables: str, sysml_model_path: str) -> str:
    """Build a classic GUMBO annex (Lark grammar). Returns annex text.
    (You can extend this to write the updated model file on disk.)
    """
    data = json.loads(json_tables)
    lines = []
    lines.append('language "GUMBO" /*{')
    # integration
    lines.append('    integration')
    for i, a in enumerate(data.get("assumptions", []), 1):
        desc = a.get("raw", f"Assumption {i}").replace('"','\"')
        lines.append(f'        assume A{i} "{desc}" : true;')
    lines.append('')
    # initialize
    lines.append('    initialize')
    lines.append('        guarantee GI1 "init" : monitor_status = Init_Status;')
    lines.append('')
    # compute
    lines.append('    compute')
    lines.append('        compute_cases')
    for i, r in enumerate(data.get("requirements", []), 1):
        desc = r.get("raw", f"Requirement {i}").replace('"','\"')
        lines.append(f'            case REQ_{i} "{desc}" :')
        lines.append('                assume true;')
        lines.append('                guarantee true;')
    lines.append('*/')
    return "\n".join(lines)
