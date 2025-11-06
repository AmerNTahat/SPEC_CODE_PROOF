
import json, subprocess, tempfile, os, re
from agents import function_tool

@function_tool
def extract_faa_tables(pdf_path: str) -> str:
    """Extract FAA AR-08-32 tables from a PDF into standardized JSON.
    Returns: JSON string with 'variables', 'requirements', 'assumptions', etc.
    """
    tmpdir = tempfile.mkdtemp()
    txt = os.path.join(tmpdir, "out.txt")
    # Minimal dependency approach using `pdftotext -layout`
    subprocess.run(["pdftotext", "-layout", pdf_path, txt], check=True)
    text = open(txt, "r", encoding="utf-8", errors="ignore").read()

    def parse_table(section_title: str, headers: list[str]):
        out = []
        if section_title.lower() in text.lower():
            block = text[text.lower().find(section_title.lower()):]
            for line in block.splitlines():
                if any(h.lower() in line.lower() for h in headers):
                    continue
                cells = re.split(r"\s{2,}", line.strip())
                if len(cells) >= 2 and any(cells):
                    out.append({"raw": line.strip(), "cells": cells})
        return out

    variables = parse_table("Monitored Variables", ["Name", "Type"]) +                 parse_table("Controlled Variables", ["Name", "Type"])
    requirements = parse_table("Requirements", ["ID", "Condition", "Action"]) or                    parse_table("Monitor Interface", ["ID"])  # heuristic
    assumptions = parse_table("Assumptions", ["ID"]) or                   parse_table("Environmental Assumptions", ["ID"])  # heuristic

    payload = {
        "variables": variables,
        "requirements": requirements,
        "assumptions": assumptions,
    }
    return json.dumps(payload, ensure_ascii=False)
