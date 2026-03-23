from __future__ import annotations

import json
import subprocess
from pathlib import Path


def test_synth_and_benchmark_flow(tmp_path: Path) -> None:
    cases = tmp_path / "cases"
    gold = tmp_path / "gold"
    artifacts = tmp_path / "artifacts"

    subprocess.run(
        [
            "python",
            "-m",
            "src.synth.generate_cases",
            "--out-dir",
            str(cases),
            "--gold-dir",
            str(gold),
            "--num-cases",
            "4",
        ],
        check=True,
    )
    subprocess.run(
        [
            "python",
            "-m",
            "src.eval.run_benchmark",
            "--cases",
            str(cases),
            "--gold",
            str(gold),
            "--artifacts",
            str(artifacts),
        ],
        check=True,
    )

    summary = json.loads((artifacts / "metrics" / "benchmark_summary.json").read_text())
    assert summary["cases"] == 4
    assert "schema_pass_rate" in summary
