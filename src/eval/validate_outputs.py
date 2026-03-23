from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _validate_cell(cell: dict[str, Any]) -> list[str]:
    errs = []
    for req, typ in [("text", str), ("rowspan", int), ("colspan", int)]:
        if req not in cell or not isinstance(cell[req], typ):
            errs.append(f"cell missing/invalid {req}")
    return errs


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["root must be object"]
    tables = payload.get("tables")
    if not isinstance(tables, list):
        return ["tables must be list"]

    for i, table in enumerate(tables):
        prefix = f"tables[{i}]"
        for req, typ in [("table_id", int), ("page_number", int), ("title", str), ("caption", str), ("data", dict)]:
            if req not in table or not isinstance(table[req], typ):
                errors.append(f"{prefix}.{req} missing/invalid")
        data = table.get("data", {})
        if not isinstance(data, dict):
            continue
        for req, typ in [("columns", list), ("column_groups", list), ("rows", list), ("footnotes", list), ("notes_below_table", list)]:
            if req not in data or not isinstance(data[req], typ):
                errors.append(f"{prefix}.data.{req} missing/invalid")
        for rj, row in enumerate(data.get("rows", [])):
            if not isinstance(row, dict) or "cells" not in row or not isinstance(row["cells"], list):
                errors.append(f"{prefix}.data.rows[{rj}] invalid")
                continue
            for cj, cell in enumerate(row["cells"]):
                for err in _validate_cell(cell):
                    errors.append(f"{prefix}.data.rows[{rj}].cells[{cj}] {err}")
    return errors


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate output JSON files against protocol schema contract")
    ap.add_argument("--schema", default="schema/protocol_table.schema.json")
    ap.add_argument("--outputs", default="artifacts/outputs")
    args = ap.parse_args()

    _ = Path(args.schema).read_text(encoding="utf-8")
    output_dir = Path(args.outputs)
    files = sorted(output_dir.glob("*.json"))
    all_errors: list[str] = []
    for file in files:
        payload = json.loads(file.read_text(encoding="utf-8"))
        all_errors.extend([f"{file}: {e}" for e in validate_payload(payload)])

    if all_errors:
        for err in all_errors:
            print(err)
        raise SystemExit(1)

    print(f"Validated {len(files)} files successfully.")


if __name__ == "__main__":
    main()
