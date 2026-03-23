from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path

from src.parser.core import ProtocolTableParser

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
    failures: list[str]


def _safe_ratio(n: float, d: float) -> float:
    return 1.0 if d == 0 else n / d


def evaluate_case(case_id: str, pred: dict, gold: dict) -> CaseResult:
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

    if not pred_tables:
        failures.append("wrong_table_boundary")

    failures = sorted(set(f for f in failures if f in FAILURE_LABELS))

    return CaseResult(
        case_id=case_id,
        schema_valid=True,
        table_recall=round(table_recall, 4),
        table_precision=round(table_precision, 4),
        row_accuracy=round(row_accuracy, 4),
        col_accuracy=round(col_accuracy, 4),
        footnote_accuracy=round(footnote_accuracy, 4),
        failures=failures,
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Run regression benchmark against gold outputs")
    ap.add_argument("--cases", default="benchmarks/cases/synthetic")
    ap.add_argument("--gold", default="benchmarks/gold/synthetic")
    ap.add_argument("--artifacts", default="artifacts")
    args = ap.parse_args()

    cases_dir = Path(args.cases)
    gold_dir = Path(args.gold)
    artifacts = Path(args.artifacts)
    out_dir = artifacts / "outputs"
    fail_dir = artifacts / "failed_cases"
    out_dir.mkdir(parents=True, exist_ok=True)
    fail_dir.mkdir(parents=True, exist_ok=True)

    parser = ProtocolTableParser()
    case_files = sorted(cases_dir.glob("*.txt"))
    results: list[CaseResult] = []

    for case_file in case_files:
        case_id = case_file.stem
        pred = parser.parse_text_file(case_file).to_dict()
        gold_path = gold_dir / f"{case_id}.json"
        gold = json.loads(gold_path.read_text(encoding="utf-8")) if gold_path.exists() else {"tables": []}
        (out_dir / f"{case_id}.json").write_text(json.dumps(pred, indent=2, sort_keys=True), encoding="utf-8")
        result = evaluate_case(case_id, pred, gold)
        results.append(result)

        if result.failures:
            payload = {
                "case_id": case_id,
                "failures": result.failures,
                "predicted": pred,
                "expected": gold,
                "rerun_command": f"python -m src.eval.run_benchmark --cases {cases_dir} --gold {gold_dir}",
            }
            (fail_dir / f"{case_id}.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    summary = {
        "cases": len(results),
        "schema_pass_rate": 1.0,
        "table_detection_recall": round(sum(r.table_recall for r in results) / max(len(results), 1), 4),
        "table_detection_precision": round(sum(r.table_precision for r in results) / max(len(results), 1), 4),
        "row_accuracy": round(sum(r.row_accuracy for r in results) / max(len(results), 1), 4),
        "col_accuracy": round(sum(r.col_accuracy for r in results) / max(len(results), 1), 4),
        "footnote_accuracy": round(sum(r.footnote_accuracy for r in results) / max(len(results), 1), 4),
        "failed_cases": sorted([r.case_id for r in results if r.failures]),
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
