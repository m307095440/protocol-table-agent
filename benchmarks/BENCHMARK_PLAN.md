# BENCHMARK_PLAN.md

## Objective
Define the benchmark strategy for developing a generalized protocol table extraction engine.

## Principles
- cover structural diversity
- separate structure quality from text fidelity
- measure regression over time
- include both real and synthetic cases
- preserve failed cases for repeated debugging

## Benchmark buckets

### B1. Simple regular tables
Examples:
- two-dimensional grids
- single header row
- no merged cells

Focus:
- basic detection
- row/column segmentation
- stable serialization

### B2. Multi-row header tables
Examples:
- schedule tables
- grouped visit windows
- layered column headers

Focus:
- header hierarchy
- column group reconstruction
- header depth detection

### B3. Merged-cell tables
Examples:
- rowspan in first column
- colspan in grouped treatment columns
- partial header merges

Focus:
- rowspan / colspan recovery
- grid normalization

### B4. Footnote-heavy tables
Examples:
- superscript markers
- note references attached to cells
- abbreviation blocks below the table

Focus:
- footnote capture
- applies_to linkage
- note separation from body rows

### B5. Continuation tables across pages
Examples:
- "(Continued)" tables
- same caption across consecutive pages
- repeated headers across page boundaries

Focus:
- continuation merge
- source page tracking
- repeated header recognition

### B6. OCR-noisy or visually irregular tables
Examples:
- broken words
- skewed alignment
- partially missing borders
- image-heavy pages

Focus:
- robustness
- warning generation
- graceful degradation without schema breakage

### B7. Semi-structured tables
Examples:
- category divider rows inside the table
- mixed dense/narrative table content
- irregular cell occupancy

Focus:
- row role classification
- preserving structure without flattening meaning

## Real benchmark set
Start with a small but diverse real set:
- 10-30 protocol PDFs
- at least 3 sponsors if available
- at least 1 case each from B1-B7

## Synthetic benchmark set
Codex should generate synthetic tables covering:
- random header depths
- random rowspan / colspan patterns
- synthetic footnotes
- synthetic continuation tables
- injected OCR-like noise
- blank and sparse cells
- rotated or shifted layouts when feasible

## Golden outputs
For a subset of benchmark documents, create curated gold outputs:
- exact or near-exact structural targets
- verified table boundaries
- verified header/group structure
- verified footnotes
- verified continuation links

## Metrics

### Structural metrics
- table detection precision
- table detection recall
- table boundary IoU or overlap score
- row count accuracy
- column count accuracy
- header depth accuracy
- rowspan accuracy
- colspan accuracy
- column group accuracy

### Linkage metrics
- footnote linkage accuracy
- note-below-table capture accuracy
- continuation merge accuracy
- source anchor accuracy

### Output quality metrics
- schema pass rate
- serialization stability
- warning usefulness coverage

### Optional text metrics
- normalized cell text exact match
- edit distance on cell text
- header text normalization score

## Failure artifact requirements
For every failed case, save:
- input document reference
- extracted JSON
- expected JSON or expected structure summary
- failure taxonomy label
- diff summary
- reproducible rerun command if possible

## Benchmark gates for initial success
Suggested initial thresholds:
- schema pass rate >= 99%
- table detection recall >= 0.85 on real benchmark
- header structure accuracy >= 0.80
- rowspan / colspan accuracy >= 0.75
- continuation merge accuracy >= 0.75 where applicable

These thresholds may be adjusted after the first baseline is implemented.

## Regression policy
Any code change that lowers core benchmark scores must be flagged.
No silent regressions should be accepted.
