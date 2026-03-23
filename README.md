# Protocol Table Agent

A Codex-driven repository for building a deterministic, self-improving protocol table extraction system.

## Purpose
This repository is the starting point for Codex to build a generalized parser that extracts tables from protocol PDFs into a stable JSON schema.

## Current state
This repository initially contains:
- task instructions for Codex
- a target JSON schema draft
- a benchmark plan
- example inputs

It does not yet contain the parser implementation.

## Core goal
Given a protocol PDF, extract all tables into structured JSON that conforms to `schema/protocol_table.schema.json`.

## Important constraints
- The provided sample JSON is a structure reference, not guaranteed truth.
- The parser must generalize across many protocol layouts.
- The parser must avoid overfitting to one study or sponsor.
- Runs should be reproducible and as deterministic as practical.

## Initial repository setup
Place the following files here before starting Codex:
- `inputs/examples/ABC-01-001 Study Protocol-v2 1-Bookmark.pdf`
- `inputs/examples/file_parser_example.json`

## Recommended Codex workflow
1. Open this repository in Codex.
2. Ask Codex to read:
   - `AGENTS.md`
   - `TASK_SPEC.md`
   - `schema/protocol_table.schema.json`
   - `benchmarks/BENCHMARK_PLAN.md`
   - `prompts/CODEX_BOOTSTRAP_PROMPT.md`
3. Instruct Codex to:
   - scaffold the codebase
   - implement a baseline parser
   - add schema validation
   - add tests
   - add benchmark evaluation
   - add synthetic data generation
   - iterate until benchmark quality stabilizes

## Expected implementation areas
Codex should eventually create:
- `src/parser/`
- `src/eval/`
- `src/synth/`
- `src/runner/`
- `tests/`

## Minimum expected commands after implementation
These are expected target commands that Codex should make work:
- `python -m pytest tests -q`
- `python -m src.eval.validate_outputs`
- `python -m src.eval.run_benchmark`
- `python -m src.runner.report_metrics`

## Output artifacts
Codex should save the following under `artifacts/`:
- logs
- benchmark summaries
- failure classifications
- output diffs
- failed sample outputs

## Quality priorities
Prioritize:
1. schema validity
2. table detection recall
3. boundary correctness
4. header structure
5. rowspan / colspan
6. footnote linkage
7. continuation-table handling
8. text fidelity

## What success looks like
A good first version should:
- pass schema validation
- work on a meaningful subset of protocol tables
- expose failure modes clearly
- improve through repeated benchmark-driven iteration
