# Protocol Table Agent

Deterministic, schema-first baseline for extracting protocol tables from PDFs/text-like protocol exports into JSON.

## What is implemented

- Generalized parser (`src/parser/`) with inspectable heuristics for:
  - table block detection
  - multi-row header inference
  - row normalization
  - lightweight column-group inference
  - footnote and note-below-table capture
  - continuation merge across adjacent pages
- JSON schema validation (`src/eval/validate_outputs.py`)
- Regression benchmark harness (`src/eval/run_benchmark.py`)
- Deterministic synthetic benchmark generator (`src/synth/generate_cases.py`)
- Iterative self-improvement loop controller (`src/runner/self_improve.py`)
- Regression tests for parser determinism and benchmark flow (`tests/`)

## Determinism and reproducibility

- Pinned dependencies in `pyproject.toml`
- Fixed synthetic RNG seed (`20260323`)
- Stable sorting before output serialization
- JSON emitted with `sort_keys=True`
- Repeatable benchmark + artifact paths under `artifacts/`

## Installation

```bash
python -m pip install -e .[dev]
```

## Parse a protocol PDF

```bash
python -m src.parser inputs/examples/ABC-01-001\ Study\ Protocol-v2\ 1-Bookmark.pdf artifacts/outputs/sample_pdf.json
```

## Parse a text-like protocol export

```bash
python -m src.parser benchmarks/cases/synthetic/case_001.txt artifacts/outputs/case_001.json
```

## Full baseline flow (required checks)

1) Generate deterministic synthetic benchmark:

```bash
python -m src.synth.generate_cases --num-cases 12
```

2) Run tests:

```bash
python -m pytest tests -q
```

3) Run benchmark and save metrics/failed cases:

```bash
python -m src.eval.run_benchmark
```

4) Validate outputs against schema:

```bash
python -m src.eval.validate_outputs
```

5) Report metrics:

```bash
python -m src.runner.report_metrics
```

6) Run iterative self-improvement controller:

```bash
python -m src.runner.self_improve --iterations 2
```

## Artifact layout

- `artifacts/outputs/`: parser outputs used by validation/benchmark
- `artifacts/metrics/benchmark_summary.json`: aggregate metrics
- `artifacts/metrics/benchmark_results.json`: per-case scores and labels
- `artifacts/failed_cases/`: structured failures with rerun command
- `artifacts/self_improve/`: per-iteration loop state and failure taxonomy summary

## Failure taxonomy used

- missed_table
- false_positive_table
- wrong_table_boundary
- wrong_header_hierarchy
- wrong_row_split
- wrong_col_split
- wrong_rowspan
- wrong_colspan
- wrong_column_group
- wrong_footnote_linkage
- wrong_note_below_table_capture
- wrong_continuation_merge
- schema_violation
- anchor_mismatch
- text_normalization_error

## Notes

- The sample JSON in `inputs/examples/file_parser_example.json` is treated as a structure reference only.
- Core parser logic is document-agnostic and does not use sample-specific hardcoded document IDs, titles, or page ranges.
- Baseline currently favors structural stability and explicit failure artifacts over opaque post-processing.
