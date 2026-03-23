from __future__ import annotations

import argparse
import itertools
import json
import subprocess
from pathlib import Path


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def run_capture(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def _score(summary: dict) -> float:
    return (
        summary.get("schema_pass_rate", 0.0) * 5
        + summary.get("table_detection_recall", 0.0) * 3
        + summary.get("header_accuracy", 0.0) * 2
        + summary.get("footnote_accuracy", 0.0)
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Deterministic self-improvement loop controller")
    ap.add_argument("--iterations", type=int, default=2)
    args = ap.parse_args()

    loop_dir = Path("artifacts/self_improve")
    loop_dir.mkdir(parents=True, exist_ok=True)

    split_candidates = [r"\s{2,}|\|", r"\|", r"\s{2,}"]
    min_rows_candidates = [2, 3]
    header_candidates = [2, 3]

    for i in range(1, args.iterations + 1):
        run(["python", "-m", "pytest", "tests", "-q"])
        run(["python", "-m", "src.synth.generate_cases"])

        best: tuple[float, dict] | None = None
        for split, min_rows, max_headers in itertools.product(split_candidates, min_rows_candidates, header_candidates):
            run_capture(
                [
                    "python",
                    "-m",
                    "src.eval.run_benchmark",
                    "--split-pattern",
                    split,
                    "--min-rows",
                    str(min_rows),
                    "--max-header-rows",
                    str(max_headers),
                ]
            )
            run(["python", "-m", "src.eval.validate_outputs"])
            summary = json.loads(Path("artifacts/metrics/benchmark_summary.json").read_text(encoding="utf-8"))
            score = _score(summary)
            candidate = {
                "score": round(score, 4),
                "split_pattern": split,
                "min_rows": min_rows,
                "max_header_rows": max_headers,
                "summary": summary,
            }
            if best is None or score > best[0]:
                best = (score, candidate)

        assert best is not None
        labels = []
        summary = best[1]["summary"]
        if summary.get("table_detection_recall", 0) < 0.85:
            labels.append("missed_table")
        if summary.get("row_accuracy", 0) < 0.8:
            labels.append("wrong_row_split")
        if summary.get("col_accuracy", 0) < 0.8:
            labels.append("wrong_col_split")
        if summary.get("footnote_accuracy", 0) < 0.75:
            labels.append("wrong_footnote_linkage")

        state = {
            "iteration": i,
            "failure_labels": sorted(set(labels)),
            "selected_config": {
                "split_pattern": best[1]["split_pattern"],
                "min_rows": best[1]["min_rows"],
                "max_header_rows": best[1]["max_header_rows"],
            },
            "score": best[1]["score"],
        }
        (loop_dir / f"iteration_{i:02d}.json").write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")

    print(f"Completed {args.iterations} loop iterations.")


if __name__ == "__main__":
    main()
