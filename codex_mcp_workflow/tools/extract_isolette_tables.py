#!/usr/bin/env python3
import json
import os
import re
from typing import Dict, List, Optional, Tuple

TEXT_PATH = "Steve_Meller_FAA_docAR-08-32.txt"
OUTPUT_DIR = "Isollete_tables"

TABLE_SPECS = [
    {
        "match": "Table 3. Thermostat Monitored and Controlled Variables",
        "columns": ["Name", "Type", "Physical Interpretation"],
        "header_lines": 1,
    },
    {
        "match": "Table 6. Preliminary Set of Isolette Thermostat Functions",
        "columns": ["Function Column 1", "Function Column 2"],
        "header_lines": 0,
        "notes": ["Source table has no explicit headers; column names assigned during extraction."],
    },
    {
        "match": "Table A-1. Summary of Isolette Thermostat Use and Exception Cases",
        "columns": ["ID", "Primary Actors", "Title and Description"],
        "header_lines": 2,
    },
    {
        "match": "Table A-2. Isolette Thermostat Primary Actors and Goals",
        "columns": ["Actor", "Primary Goals of the Actor"],
        "header_lines": 1,
    },
    {
        "match": "Table A-3. Thermostat Monitored Variables for Temperature Sensor",
        "columns": ["Name", "Type", "Range", "Units", "Physical Interpretation"],
        "header_lines": 1,
    },
    {
        "match": "Table A-4. Thermostat Controlled Variables for Heat Source",
        "columns": ["Name", "Type", "Range", "Units", "Physical Interpretation"],
        "header_lines": 1,
    },
    {
        "match": "Table A-5. Thermostat Monitored Variables for Operator Interface",
        "columns": ["Name", "Type", "Range", "Units", "Physical Interpretation"],
        "header_lines": 1,
    },
    {
        "match": "Table A-6. Thermostat Controlled Variables for Operator Interface",
        "columns": ["Name", "Type", "Range", "Units", "Physical Interpretation"],
        "header_lines": 1,
    },
    {
        "match": "Table A-7. The Regulate Temperature Internal Variables",
        "columns": ["Name", "Type", "Range", "Units", "Physical Interpretation"],
        "header_lines": 1,
    },
    {
        "match": "Table A-8. Manage Regulator Interface Function Constants",
        "columns": ["Name", "Type", "Value", "Units", "Physical Interpretation"],
        "header_lines": 1,
    },
    {
        "match": "Table A-9. The Manage Regulator Mode Function Constants",
        "columns": ["Name", "Type", "Value", "Units", "Physical Interpretation"],
        "header_lines": 1,
    },
    {
        "match": "Table A-10. The Manage Regulator Mode Function Definitions",
        "columns": ["Name", "Type", "Definition"],
        "header_lines": 1,
    },
    {
        "match": "Table A-11. The Manage Heat Source Function Constants",
        "columns": ["Name", "Type", "Value", "Units", "Physical Interpretation"],
        "header_lines": 1,
    },
    {
        "match": "Table A-12. Monitor Temperature Internal Variables",
        "columns": ["Name", "Type", "Range", "Units", "Physical Interpretation"],
        "header_lines": 1,
    },
    {
        "match": "Table A-13. The Manage Monitor Interface Function Constants",
        "columns": ["Name", "Type", "Value", "Units", "Physical Interpretation"],
        "header_lines": 1,
    },
    {
        "match": "Table A-14. The Manage Monitor Mode Function Constants",
        "columns": ["Name", "Type", "Value", "Units", "Physical Interpretation"],
        "header_lines": 1,
    },
    {
        "match": "Table A-15. The Manage Monitor Mode Function Definitions",
        "columns": ["Name", "Type", "Definition"],
        "header_lines": 1,
    },
]

NOTE_PREFIXES = ("●", "Rationale:", "Note:", "Notes:")


def load_lines(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as infile:
        return infile.readlines()


def normalize(text: str) -> str:
    return " ".join(text.split())


def get_segments(line: str) -> List[Tuple[int, str]]:
    segments: List[Tuple[int, str]] = []
    i = 0
    n = len(line)
    while i < n:
        while i < n and line[i] == " ":
            i += 1
        if i >= n:
            break
        start = i
        while i < n:
            if line[i] == " ":
                space_count = 1
                j = i + 1
                while j < n and line[j] == " ":
                    space_count += 1
                    j += 1
                if space_count >= 2:
                    break
            i += 1
        segment = line[start:i].rstrip()
        segments.append((start, segment.strip()))
        while i < n and line[i] == " ":
            i += 1
    return [(pos, text) for pos, text in segments if text]


def compute_column_starts_from_header(header_lines: List[str], columns: List[str]) -> List[int]:
    best_segments: List[Tuple[int, str]] = []
    for line in header_lines:
        segments = get_segments(line)
        if len(segments) > len(best_segments):
            best_segments = segments
    starts: List[Optional[int]] = [pos for pos, _ in best_segments]
    if len(starts) < len(columns):
        additional: List[int] = []
        for line in header_lines:
            for pos, _ in get_segments(line):
                if pos not in starts and pos not in additional:
                    additional.append(pos)
        if additional:
            starts.extend(sorted(additional))
    if len(starts) < len(columns):
        for idx, column in enumerate(columns):
            lowered = column.lower()
            for line in header_lines:
                pos = line.lower().find(lowered)
                if pos != -1:
                    if idx >= len(starts):
                        starts.extend([None] * (idx + 1 - len(starts)))
                    if starts[idx] is None or pos < starts[idx]:
                        starts[idx] = pos
    resolved: List[int] = []
    last_value = 0
    for idx in range(len(columns)):
        if idx < len(starts) and starts[idx] is not None:
            last_value = starts[idx]  # type: ignore[arg-type]
        else:
            last_value += 8
        resolved.append(last_value)
    return resolved


def assign_column(position: int, column_starts: List[int]) -> int:
    best_idx = 0
    best_diff = abs(position - column_starts[0]) if column_starts else 0
    for idx in range(1, len(column_starts)):
        diff = abs(position - column_starts[idx])
        if diff < best_diff:
            best_idx = idx
            best_diff = diff
    return best_idx


def looks_like_note(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and stripped.startswith(NOTE_PREFIXES)


def collect_table_lines(lines: List[str], start: int, next_start: Optional[int]) -> List[str]:
    collected: List[str] = []
    idx = start + 1
    while idx < len(lines) and (next_start is None or idx < next_start):
        raw = lines[idx].rstrip("\n")
        stripped = raw.strip()
        if not stripped:
            # look ahead to ensure the table really continues
            lookahead = idx + 1
            while lookahead < len(lines) and (next_start is None or lookahead < next_start):
                next_line = lines[lookahead].rstrip("\n")
                if next_line.strip():
                    break
                lookahead += 1
            if lookahead >= len(lines) or (next_start is not None and lookahead >= next_start):
                break
            next_content = lines[lookahead].rstrip("\n")
            if next_content.lstrip().startswith("Table "):
                break
            if not next_content.startswith(" ") and "  " not in next_content:
                break
            collected.append(raw)
            idx += 1
            continue
        if stripped.startswith("Table "):
            break
        if not raw.startswith(" ") and "  " not in raw:
            break
        collected.append(raw)
        idx += 1
    while collected and not collected[0].strip():
        collected.pop(0)
    while collected and not collected[-1].strip():
        collected.pop()
    return collected


def split_header_body(lines: List[str], header_count: int) -> Tuple[List[str], List[str]]:
    headers: List[str] = []
    body: List[str] = []
    consumed = 0
    for line in lines:
        stripped = line.strip()
        if consumed < header_count:
            if stripped:
                headers.append(line)
                consumed += 1
            continue
        body.append(line)
    return headers, body


def extract_notes_and_data(lines: List[str]) -> Tuple[List[str], List[str]]:
    notes: List[str] = []
    data: List[str] = []
    idx = 0
    while idx < len(lines):
        raw = lines[idx]
        stripped = raw.strip()
        if not stripped:
            idx += 1
            continue
        if looks_like_note(raw):
            note_parts = [normalize(stripped)]
            idx += 1
            while idx < len(lines):
                next_raw = lines[idx]
                next_stripped = next_raw.strip()
                if not next_stripped:
                    idx += 1
                    continue
                if looks_like_note(next_raw):
                    break
                if "  " in next_raw:
                    break
                note_parts.append(normalize(next_stripped))
                idx += 1
            notes.append(" ".join(note_parts))
            continue
        data.append(raw)
        idx += 1
    return notes, data


def finalize_row(values: List[str], columns: List[str]) -> Dict[str, str]:
    row: Dict[str, str] = {}
    for idx, column in enumerate(columns):
        row[column] = normalize(values[idx]) if values[idx] else ""
    return row


def parse_rows(
    header_lines: List[str],
    lines: List[str],
    columns: List[str],
) -> Tuple[List[Dict[str, str]], List[str]]:
    notes, data_lines = extract_notes_and_data(lines)
    if not data_lines:
        return [], notes
    column_starts = compute_column_starts_from_header(header_lines, columns)
    first_column_min = min(
        len(raw) - len(raw.lstrip(" "))
        for raw in data_lines
        if raw.strip()
    )
    column_starts[0] = min(column_starts[0], first_column_min)
    data_based: List[List[int]] = [[] for _ in columns]
    for raw in data_lines:
        segments = get_segments(raw)
        if len(segments) == len(columns):
            for idx_seg, (pos, _) in enumerate(segments):
                data_based[idx_seg].append(pos)
        else:
            for idx_seg, (pos, _) in enumerate(segments):
                if idx_seg < len(columns):
                    data_based[idx_seg].append(pos)
    for idx, positions in enumerate(data_based):
        if positions:
            column_starts[idx] = min(positions)
    for idx in range(1, len(column_starts)):
        if column_starts[idx] < column_starts[idx - 1]:
            column_starts[idx] = column_starts[idx - 1]
    rows: List[List[str]] = []
    current: Optional[List[str]] = None
    for raw in data_lines:
        stripped = raw.strip()
        if not stripped:
            continue
        segments = get_segments(raw)
        if not segments:
            continue
        assigned: List[Tuple[int, int, str]] = []
        if len(segments) == len(columns):
            for idx_seg, (pos, text) in enumerate(segments):
                text_norm = normalize(text)
                if not text_norm:
                    continue
                assigned.append((idx_seg, pos, text_norm))
        else:
            for pos, text in segments:
                text_norm = normalize(text)
                if not text_norm:
                    continue
                col_idx = assign_column(pos, column_starts)
                assigned.append((col_idx, pos, text_norm))
        if not assigned:
            continue
        col0_positions = [pos for col, pos, _ in assigned if col == 0]
        col0_texts = [text for col, _, text in assigned if col == 0]
        col1_positions = [pos for col, pos, _ in assigned if col == 1]
        has_col0 = bool(col0_positions)
        has_col1 = bool(col1_positions)
        continuation = False
        if current is None:
            current = [""] * len(columns)
        else:
            if not has_col0:
                continuation = True
            else:
                earliest = min(col0_positions)
                if current[0] and not has_col1 and len(assigned) <= 2 and current[1]:
                    continuation = True
                elif current[0] and has_col1 and earliest <= column_starts[0] - 2 and current[1]:
                    continuation = True
                elif current[0] and not has_col1 and earliest > column_starts[0] + 1:
                    continuation = True
                elif (
                    current[0]
                    and not has_col1
                    and earliest <= column_starts[0] - 2
                    and current[1]
                    and col0_texts
                    and len(col0_texts[0].split()) <= 2
                ):
                    continuation = True
        if not continuation and current is not None and any(current):
            rows.append(current)
            current = [""] * len(columns)
        if current is None:
            current = [""] * len(columns)
        for col_idx, _pos, text_norm in assigned:
            if col_idx < len(columns) and columns[col_idx].lower() == "units" and current[col_idx]:
                last_idx = len(columns) - 1
                if last_idx != col_idx:
                    if current[last_idx]:
                        current[last_idx] += f" {text_norm}"
                    else:
                        current[last_idx] = text_norm
                continue
            target_text = text_norm
            if col_idx < len(columns) and columns[col_idx].lower() == "units" and " " in text_norm:
                unit_value, _, remainder = text_norm.partition(" ")
                target_text = unit_value
                if remainder:
                    last_idx = len(columns) - 1
                    if last_idx != col_idx:
                        if current[last_idx]:
                            current[last_idx] += f" {remainder}"
                        else:
                            current[last_idx] = remainder
            if current[col_idx]:
                current[col_idx] += f" {target_text}"
            else:
                current[col_idx] = target_text
    if current is not None and any(current):
        rows.append(current)
    return [finalize_row(row, columns) for row in rows], notes


def slugify(text: str) -> str:
    lowered = text.lower()
    slug = re.sub(r"[^a-z0-9]+", "_", lowered)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "table"


def main() -> None:
    lines = load_lines(TEXT_PATH)
    for spec in TABLE_SPECS:
        match = spec["match"]
        spec_start = None
        for idx, line in enumerate(lines):
            if match in line:
                spec_start = idx
                break
        if spec_start is None:
            raise RuntimeError(f"Could not locate '{match}' in source text")
        spec["start"] = spec_start
        if "title" not in spec:
            spec["title"] = match.split(". ", 1)[1] if ". " in match else match
    ordered_specs = sorted(TABLE_SPECS, key=lambda s: s["start"])

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for idx, spec in enumerate(ordered_specs):
        match = spec["match"]
        next_start = ordered_specs[idx + 1]["start"] if idx + 1 < len(ordered_specs) else None
        block_lines = collect_table_lines(lines, spec["start"], next_start)
        headers, body = split_header_body(block_lines, spec["header_lines"])
        rows, notes = parse_rows(headers, body, spec["columns"])
        extra_notes = spec.get("notes", [])
        all_notes = extra_notes + notes

        table_id = match.split(". ", 1)[0]
        output = {
            "table_id": table_id,
            "title": spec.get("title", match),
            "columns": spec["columns"],
            "rows": rows,
        }
        if all_notes:
            output["notes"] = all_notes

        filename = f"{slugify(table_id)}_{slugify(spec.get('title', match))}.json"
        path = os.path.join(OUTPUT_DIR, filename)
        with open(path, "w", encoding="utf-8") as outfile:
            json.dump(output, outfile, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
