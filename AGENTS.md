# AGENTS.md

## Objective
Build a deterministic, self-improving protocol table extraction system for PDF protocol documents.

The system must:
- extract tables from protocol PDFs
- output JSON conforming to `schema/protocol_table.schema.json`
- generalize across diverse protocol layouts
- avoid hardcoding to any single sample file
- continuously improve using regression tests and synthetic data

## Non-goals
- Do not optimize only for the provided sample protocol.
- Do not rely on one-off rules tied to a single document title, sponsor, study, or page range.
- Do not return only flat CSV output.
- Do not assume all protocol tables are regular rectangular grids.

## Determinism requirements
All program behavior must be as deterministic as practical:
- pin dependencies
- use explicit random seeds
- sort unordered outputs before serialization
- keep JSON output stable across repeated runs in the same environment
- make evaluation reproducible
- isolate or avoid nondeterministic external services during tests

## Required repository outputs
The repo must contain:
- parser implementation
- JSON schema
- synthetic benchmark generator
- evaluation harness
- regression tests
- self-improvement loop controller
- structured metrics and failed-case artifacts
- exact usage documentation

## Expected extraction capabilities
Support as many of the following as possible:
- multi-row headers
- rowspan / colspan
- column groups
- footnotes
- notes below tables
- continuation tables across pages
- rotated tables
- noisy OCR-like text
- sparse and semi-structured tables
- mixed dense / narrative rows inside tables

## Development loop
For each meaningful iteration:
1. run tests
2. run schema validation
3. run regression benchmark
4. inspect failed cases
5. classify failure types
6. patch code
7. rerun all checks
8. save metrics and failed artifacts under `artifacts/`

## Failure taxonomy
Use these labels where applicable:
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

## Execution rules
Before claiming completion, run all applicable checks and save outputs:
- unit tests
- schema validation
- regression benchmark
- failed case export
- metrics report generation

## Completion bar
A task is not complete unless:
- tests pass
- schema validation passes
- benchmark metrics are produced
- failed cases are saved for remaining errors
- code and output artifacts are reproducible
- README contains exact run instructions

## Architectural constraints
- Keep core parser domain-agnostic at the table-structure level.
- Protocol-specific heuristics, if needed, must be isolated behind explicit adapters and not embedded in core extraction logic.
- Prefer simple, inspectable, testable logic over opaque behavior.
- Preserve traceability to the source document for each extracted table.

## Prioritization order
Optimize quality in this order:
1. schema validity
2. table detection recall
3. table boundary correctness
4. header structure reconstruction
5. rowspan / colspan reconstruction
6. footnote and note linkage
7. continuation-table merging
8. cell text fidelity