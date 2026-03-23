# Protocol Table Agent

Deterministic, schema-first protocol table extraction baseline with explicit benchmark artifacts and failure taxonomy.

## Implemented components

- `src/parser/`: generalized table parser for PDF/text protocol content
- `src/eval/validate_outputs.py`: schema-contract validator
- `src/eval/run_benchmark.py`: regression benchmark + failure artifact exporter
- `src/synth/generate_cases.py`: deterministic synthetic case + independent gold generator
- `src/runner/self_improve.py`: iterative loop with deterministic config search
- `tests/`: regression tests for parser behavior and benchmark flow

## Determinism

- fixed synthetic RNG seed (`20260323`)
- deterministic sort/serialization (`sort_keys=True`)
- sorted file iteration for benchmark
- deterministic parser config search space in self-improve loop

## Installation

```bash
python -m pip install -e .[dev]
```

## Parse examples

```bash
python -m src.parser inputs/examples/ABC-01-001\ Study\ Protocol-v2\ 1-Bookmark.pdf artifacts/outputs/sample_pdf.json
python -m src.parser benchmarks/cases/synthetic/case_001.txt artifacts/outputs/case_001.json
```

## Full reproducible workflow

```bash
python -m src.synth.generate_cases --num-cases 12
python -m pytest tests -q
python -m src.eval.run_benchmark
python -m src.eval.validate_outputs
python -m src.runner.report_metrics
python -m src.runner.self_improve --iterations 2
```

## Artifact outputs

Generated at runtime under `artifacts/`:

- `artifacts/outputs/*.json`
- `artifacts/failed_cases/*.json`
- `artifacts/metrics/benchmark_summary.json`
- `artifacts/metrics/benchmark_results.json`
- `artifacts/self_improve/iteration_*.json`

## Notes

- Synthetic benchmark gold labels are generated independently of parser predictions.
- The provided sample JSON is used as a structure reference, not assumed ground truth.
- The core parser avoids document-title/sponsor/page hardcoding.
