\# TASK\_SPEC.md



\## Goal

Build a generalized protocol table extraction engine for PDF documents.



\## Inputs

Primary input:

\- protocol PDFs



Optional future inputs:

\- OCR text

\- layout metadata

\- page images

\- bookmarks / TOC exports



\## Outputs

For each input document, emit structured JSON conforming to `schema/protocol\_table.schema.json`.



\## Important notes

\- The provided JSON example is a structure reference, not guaranteed ground truth.

\- Its structure should be treated as directionally correct.

\- Its extracted values may contain errors.

\- The system should maximize generalization across many protocol documents.

\- Do not assume the sample protocol is representative of all protocols.



\## Design principles

\- schema-first

\- test-first

\- deterministic where practical

\- reproducible runs

\- no sample-specific overfitting

\- preserve traceability to source pages and anchors

\- keep failure analysis explicit and inspectable



\## Required system components

1\. PDF table detection and extraction

2\. table structure reconstruction

3\. header hierarchy reconstruction

4\. merged-cell detection

5\. footnote and note linkage

6\. cross-page continuation handling

7\. schema validation

8\. regression benchmark

9\. synthetic data generation

10\. iterative self-improvement runner



\## Quality priorities

Prioritize in this order:

1\. schema validity

2\. table boundary correctness

3\. header structure correctness

4\. rowspan / colspan correctness

5\. footnote linkage

6\. cross-page continuation

7\. cell text fidelity



\## Deliverables

\- working code

\- tests

\- benchmark runner

\- synthetic generator

\- artifacts and metrics

\- usage instructions

\- reproducible evaluation flow



\## Out of scope for the first baseline

\- perfect support for every scanned/OCR-only protocol

\- perfect interpretation of every visually irregular layout

\- semantic understanding of table meaning beyond structure extraction



\## Definition of success

A successful baseline should:

\- parse at least a meaningful subset of protocol tables into the target schema

\- pass schema validation consistently

\- improve over repeated iterations on the benchmark set

\- produce explainable failure artifacts

\- avoid document-specific hardcoding in the core parser

