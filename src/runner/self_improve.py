from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="Deterministic self-improvement loop controller")
    ap.add_argument("--iterations", type=int, default=2)
    args = ap.parse_args()

    loop_dir = Path("artifacts/self_improve")
    loop_dir.mkdir(parents=True, exist_ok=True)

    for i in range(1, args.iterations + 1):
        run(["python", "-m", "pytest", "tests", "-q"])
        run(["python", "-m", "src.synth.generate_cases", "--num-cases", "12"])
        run(["python", "-m", "src.eval.run_benchmark"])
        run(["python", "-m", "src.eval.validate_outputs"])

        summary = json.loads(Path("artifacts/metrics/benchmark_summary.json").read_text(encoding="utf-8"))
        labels = []
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
            "candidate_patch": "adjust parser split/header heuristics if labels persist",
        }
        (loop_dir / f"iteration_{i:02d}.json").write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")

    print(f"Completed {args.iterations} loop iterations.")


if __name__ == "__main__":
    main()
