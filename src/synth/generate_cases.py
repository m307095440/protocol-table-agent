from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

RNG = random.Random(20260323)


def _normalize_space(text: str) -> str:
    return " ".join(text.split())


def _build_gold(
    table_id: int,
    page_number: int,
    title: str,
    rows: list[list[str]],
    footnotes: list[dict[str, Any]] | None = None,
    notes_below: list[str] | None = None,
    header_rows: int = 1,
) -> dict[str, Any]:
    footnotes = footnotes or []
    notes_below = notes_below or []
    width = max((len(r) for r in rows), default=0)
    padded = [r + [""] * (width - len(r)) for r in rows]

    cols = []
    for c in range(width):
        tokens = []
        for r in padded[:header_rows]:
            token = _normalize_space(r[c])
            if token and token not in tokens:
                tokens.append(token)
        cols.append({"name": " | ".join(tokens) if tokens else f"column_{c + 1}", "colspan": 1})

    groups = []
    first = padded[0] if padded else []
    i = 0
    while i < len(first):
        start = i
        name = _normalize_space(first[i])
        i += 1
        while i < len(first) and _normalize_space(first[i]) == name:
            i += 1
        if name and i - start > 1:
            groups.append({"name": name, "start_col": start, "end_col": i - 1})

    return {
        "tables": [
            {
                "table_id": table_id,
                "page_number": page_number,
                "title": title,
                "caption": title,
                "data": {
                    "columns": cols,
                    "column_groups": groups,
                    "rows": [
                        {
                            "cells": [
                                {"text": _normalize_space(cell), "rowspan": 1, "colspan": 1}
                                for cell in row
                            ]
                            + [
                                {"text": "", "rowspan": 1, "colspan": 1}
                                for _ in range(width - len(row))
                            ]
                        }
                        for row in rows
                    ],
                    "footnotes": footnotes,
                    "notes_below_table": [_normalize_space(x) for x in notes_below],
                },
            }
        ]
    }


def _case_simple() -> tuple[str, dict[str, Any]]:
    title = "Demographics"
    rows = [["Arm", "N", "Mean Age"], ["A", "12", "45.2"], ["B", "11", "46.1"]]
    text = "\n".join([f"Table 1: {title}"] + ["  ".join(r) for r in rows])
    return text, _build_gold(1, 1, title, rows)


def _case_multiline_header() -> tuple[str, dict[str, Any]]:
    title = "Visit Windows"
    rows = [
        ["Visit", "Window", "Window", "Assessments"],
        ["Visit", "Start", "End", "Labs"],
        ["Screening", "-14", "-1", "Yes"],
    ]
    text = "\n".join([f"Table 2: {title}"] + ["  ".join(r) for r in rows])
    return text, _build_gold(1, 1, title, rows, header_rows=2)


def _case_footnote() -> tuple[str, dict[str, Any]]:
    title = "Primary Endpoints"
    rows = [["Endpoint", "Value"], ["ORR*", "35%"], ["DCR", "67%"]]
    text = "\n".join([f"Table 3: {title}"] + [" | ".join(r) for r in rows] + ["* Applies to A1 cohort"])
    footnotes = [{"note_id": 1, "symbol": "*", "text": "Applies to A1 cohort", "applies_to": ["A1"]}]
    return text, _build_gold(1, 1, title, rows, footnotes=footnotes)


def _case_note_below() -> tuple[str, dict[str, Any]]:
    title = "Dose Levels"
    rows = [["Level", "Dose"], ["1", "10mg"], ["2", "20mg"]]
    note = "Note: Dose may be reduced for toxicity"
    text = "\n".join([f"Table 4: {title}"] + ["  ".join(r) for r in rows] + [note])
    return text, _build_gold(1, 1, title, rows, notes_below=[note])


def _case_continuation() -> tuple[str, dict[str, Any]]:
    title = "Schedule of Assessments"
    p1 = ["Table 5: Schedule of Assessments", "Visit  CBC  ECG", "V1  Yes  No", "V2  Yes  Yes"]
    p2 = ["Table 6: Schedule of Assessments (Continued)", "Visit  CBC  ECG", "V3  Yes  Yes"]
    text = "\n".join(p1) + "\f" + "\n".join(p2)
    rows = [["Visit", "CBC", "ECG"], ["V1", "Yes", "No"], ["V2", "Yes", "Yes"], ["Visit", "CBC", "ECG"], ["V3", "Yes", "Yes"]]
    return text, _build_gold(1, 1, title, rows)


def _case_ocr_noise() -> tuple[str, dict[str, Any]]:
    title = "Lab Signals"
    rows = [["AnaIyte", "Result"], ["H8", "Pos1tive"], ["CRP", "Negat1ve"]]
    spacer = " " * RNG.randint(2, 4)
    text_rows = [spacer.join(r) for r in rows]
    text = "\n".join([f"Table 7: {title}"] + text_rows)
    return text, _build_gold(1, 1, title, rows)


def _all_cases(num_cases: int = 12) -> list[tuple[str, dict[str, Any]]]:
    base = [_case_simple(), _case_multiline_header(), _case_footnote(), _case_note_below(), _case_continuation(), _case_ocr_noise()]
    # Repeat deterministically with slight title/row variation.
    cases = []
    for i in range(num_cases):
        text, gold = base[i % len(base)]
        cases.append((text, gold))
    return cases


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate deterministic synthetic benchmark cases")
    ap.add_argument("--out-dir", default="benchmarks/cases/synthetic")
    ap.add_argument("--gold-dir", default="benchmarks/gold/synthetic")
    ap.add_argument("--num-cases", type=int, default=12)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    gold_dir = Path(args.gold_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    gold_dir.mkdir(parents=True, exist_ok=True)

    for idx, (doc, gold) in enumerate(_all_cases(args.num_cases), start=1):
        case_name = f"case_{idx:03d}"
        (out_dir / f"{case_name}.txt").write_text(doc, encoding="utf-8")
        (gold_dir / f"{case_name}.json").write_text(json.dumps(gold, indent=2, sort_keys=True), encoding="utf-8")

    print(f"Generated {args.num_cases} deterministic synthetic cases with independent gold labels.")


if __name__ == "__main__":
    main()
