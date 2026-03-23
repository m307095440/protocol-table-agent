from __future__ import annotations

import argparse
import difflib
import json
from dataclasses import dataclass, asdict
from pathlib import Path

from src.eval.validate_outputs import validate_payload
from src.parser.core import ParserConfig, ProtocolTableParser

FAILURE_LABELS = {
    "missed_table",
    "false_positive_table",
    "wrong_table_boundary",
    "wrong_header_hierarchy",
    "wrong_row_split",
    "wrong_col_split",
    "wrong_rowspan",
    "wrong_colspan",
    "wrong_column_group",
    "wrong_footnote_linkage",
    "wrong_note_below_table_capture",
    "wrong_continuation_merge",
    "schema_violation",
    "anchor_mismatch",
    "text_normalization_error",
}


@dataclass
class CaseResult:
    case_id: str
    schema_valid: bool
    table_recall: float
    table_precision: float
    row_accuracy: float
    col_accuracy: float
    footnote_accuracy: float
    header_accuracy: float
    notes_below_accuracy: float
    failures: list[str]


def _safe_ratio(n: float, d: float) -> float:
    return 1.0 if d == 0 else n / d


def _table_title(t: dict) -> str:
    return str(t.get("title", "")).strip().lower().replace("(continued)", "")


def _normalized_rows(table: dict) -> list[list[str]]:
    out = []
    for row in table.get("data", {}).get("rows", []):
        out.append([" ".join(str(c.get("text", "")).split()) for c in row.get("cells", [])])
    return out


def evaluate_case(case_id: str, pred: dict, gold: dict) -> tuple[CaseResult, list[str]]:
    errors = validate_payload(pred)
    schema_valid = not errors

    pred_tables = pred.get("tables", [])
    gold_tables = gold.get("tables", [])

    matched = min(len(pred_tables), len(gold_tables))
    table_recall = _safe_ratio(matched, len(gold_tables))
    table_precision = _safe_ratio(matched, len(pred_tables))

    failures: list[str] = []
    if len(pred_tables) < len(gold_tables):
        failures.append("missed_table")
    if len(pred_tables) > len(gold_tables):
        failures.append("false_positive_table")

    pred_rows = sum(len(t.get("data", {}).get("rows", [])) for t in pred_tables)
    gold_rows = sum(len(t.get("data", {}).get("rows", [])) for t in gold_tables)
    row_accuracy = 1.0 - min(abs(pred_rows - gold_rows), max(gold_rows, 1)) / max(gold_rows, 1)
    if row_accuracy < 1.0:
        failures.append("wrong_row_split")

    pred_cols = sum(len(t.get("data", {}).get("columns", [])) for t in pred_tables)
    gold_cols = sum(len(t.get("data", {}).get("columns", [])) for t in gold_tables)
    col_accuracy = 1.0 - min(abs(pred_cols - gold_cols), max(gold_cols, 1)) / max(gold_cols, 1)
    if col_accuracy < 1.0:
        failures.append("wrong_col_split")

    pred_notes = sum(len(t.get("data", {}).get("footnotes", [])) for t in pred_tables)
    gold_notes = sum(len(t.get("data", {}).get("footnotes", [])) for t in gold_tables)
    footnote_accuracy = 1.0 - min(abs(pred_notes - gold_notes), max(gold_notes, 1)) / max(gold_notes, 1)
    if footnote_accuracy < 1.0:
        failures.append("wrong_footnote_linkage")

    pred_header = [c.get("name", "") for t in pred_tables for c in t.get("data", {}).get("columns", [])]
    gold_header = [c.get("name", "") for t in gold_tables for c in t.get("data", {}).get("columns", [])]
    matches = sum(1 for i in range(min(len(pred_header), len(gold_header))) if pred_header[i] == gold_header[i])
    header_accuracy = _safe_ratio(matches, max(len(gold_header), 1))
    if header_accuracy < 1.0:
        failures.append("wrong_header_hierarchy")

    pred_nbt = sum(len(t.get("data", {}).get("notes_below_table", [])) for t in pred_tables)
    gold_nbt = sum(len(t.get("data", {}).get("notes_below_table", [])) for t in gold_tables)
    notes_below_accuracy = 1.0 - min(abs(pred_nbt - gold_nbt), max(gold_nbt, 1)) / max(gold_nbt, 1)
    if notes_below_accuracy < 1.0:
        failures.append("wrong_note_below_table_capture")

    if not pred_tables:
        failures.append("wrong_table_boundary")
    else:
        if any(_table_title(p) != _table_title(g) for p, g in zip(pred_tables, gold_tables)):
            failures.append("anchor_mismatch")

    if not schema_valid:
        failures.append("schema_violation")

    failures = sorted(set(f for f in failures if f in FAILURE_LABELS))

    return (
        CaseResult(
            case_id=case_id,
            schema_valid=schema_valid,
            table_recall=round(table_recall, 4),
            table_precision=round(table_precision, 4),
            row_accuracy=round(row_accuracy, 4),
            col_accuracy=round(col_accuracy, 4),
            footnote_accuracy=round(footnote_accuracy, 4),
            header_accuracy=round(header_accuracy, 4),
            notes_below_accuracy=round(notes_below_accuracy, 4),
            failures=failures,
        ),
        errors,
    )


def _diff_summary(pred: dict, gold: dict) -> str:
    pred_s = json.dumps(pred, indent=2, sort_keys=True).splitlines()
    gold_s = json.dumps(gold, indent=2, sort_keys=True).splitlines()
    diff = list(difflib.unified_diff(gold_s, pred_s, fromfile="expected", tofile="predicted", n=1))
    return "\n".join(diff[:80])


def main() -> None:
    ap = argparse.ArgumentParser(description="Run regression benchmark against gold outputs")
    ap.add_argument("--cases", default="benchmarks/cases/synthetic")
    ap.add_argument("--gold", default="benchmarks/gold/synthetic")
    ap.add_argument("--artifacts", default="artifacts")
    ap.add_argument("--split-pattern", default=r"\s{2,}|\|")
    ap.add_argument("--min-rows", type=int, default=2)
    ap.add_argument("--max-header-rows", type=int, default=3)
    args = ap.parse_args()

    cases_dir = Path(args.cases)
    gold_dir = Path(args.gold)
    artifacts = Path(args.artifacts)
    out_dir = artifacts / "outputs"
    fail_dir = artifacts / "failed_cases"
    out_dir.mkdir(parents=True, exist_ok=True)
    fail_dir.mkdir(parents=True, exist_ok=True)

    parser = ProtocolTableParser(
        config=ParserConfig(
            split_pattern=args.split_pattern,
            min_rows_for_table=args.min_rows,
            max_header_rows=args.max_header_rows,
        )
    )
    case_files = sorted(cases_dir.glob("*.txt"))
    results: list[CaseResult] = []

    for case_file in case_files:
        case_id = case_file.stem
        pred = parser.parse_text_file(case_file).to_dict()
        gold_path = gold_dir / f"{case_id}.json"
        gold = json.loads(gold_path.read_text(encoding="utf-8")) if gold_path.exists() else {"tables": []}
        (out_dir / f"{case_id}.json").write_text(json.dumps(pred, indent=2, sort_keys=True), encoding="utf-8")
        result, schema_errors = evaluate_case(case_id, pred, gold)
        results.append(result)

        if result.failures:
            payload = {
                "case_id": case_id,
                "failures": result.failures,
                "schema_errors": schema_errors,
                "predicted": pred,
                "expected": gold,
                "diff_summary": _diff_summary(pred, gold),
                "rerun_command": f"python -m src.eval.run_benchmark --cases {cases_dir} --gold {gold_dir}",
            }
            (fail_dir / f"{case_id}.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    summary = {
        "cases": len(results),
        "schema_pass_rate": round(sum(1.0 if r.schema_valid else 0.0 for r in results) / max(len(results), 1), 4),
        "table_detection_recall": round(sum(r.table_recall for r in results) / max(len(results), 1), 4),
        "table_detection_precision": round(sum(r.table_precision for r in results) / max(len(results), 1), 4),
        "row_accuracy": round(sum(r.row_accuracy for r in results) / max(len(results), 1), 4),
        "col_accuracy": round(sum(r.col_accuracy for r in results) / max(len(results), 1), 4),
        "header_accuracy": round(sum(r.header_accuracy for r in results) / max(len(results), 1), 4),
        "footnote_accuracy": round(sum(r.footnote_accuracy for r in results) / max(len(results), 1), 4),
        "notes_below_accuracy": round(sum(r.notes_below_accuracy for r in results) / max(len(results), 1), 4),
        "failed_cases": sorted([r.case_id for r in results if r.failures]),
        "parser_config": {
            "split_pattern": args.split_pattern,
            "min_rows": args.min_rows,
            "max_header_rows": args.max_header_rows,
        },
    }

    metrics_dir = artifacts / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    (metrics_dir / "benchmark_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    (metrics_dir / "benchmark_results.json").write_text(
        json.dumps([asdict(r) for r in results], indent=2, sort_keys=True), encoding="utf-8"
    )

    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
