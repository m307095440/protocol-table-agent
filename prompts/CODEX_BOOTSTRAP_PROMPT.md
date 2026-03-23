Build this repository into a deterministic, self-improving protocol table extraction system.

Read and follow these files first:
- AGENTS.md
- TASK_SPEC.md
- schema/protocol_table.schema.json
- benchmarks/BENCHMARK_PLAN.md
- README.md

Context:
- The repository contains a sample protocol PDF and a sample parsed JSON.
- The sample JSON is a structure reference only.
- Its structure is directionally correct, but its extracted values may be wrong.
- Do not overfit to the sample protocol.

Primary objective:
Create a generalized parser for extracting tables from protocol PDFs into a stable JSON schema.

Requirements:
1. Implement the parser in Python.
2. Make the system as deterministic and reproducible as practical.
3. Create a baseline parser pipeline.
4. Add schema validation.
5. Add regression tests.
6. Add a benchmark runner.
7. Add synthetic data generation for hard table cases.
8. Add an iterative self-improvement loop that:
   - runs parser
   - validates outputs
   - evaluates benchmark quality
   - classifies failures
   - patches code
   - reruns checks
   - saves metrics and failed cases under artifacts/
9. Support difficult cases where feasible:
   - multi-row headers
   - rowspan / colspan
   - column groups
   - footnotes
   - notes below table
   - continuation tables across pages
   - noisy OCR-like text
10. Do not hardcode sample-specific rules into the core parser.
11. Produce clear usage instructions in README.

Execution rules:
- After every meaningful code change, run the full test and evaluation flow.
- Save benchmark metrics and failed examples after each evaluation pass.
- Prefer inspectable, testable logic.
- Keep failures explicit instead of hiding them.
- Continue iterating until tests pass and benchmark quality stabilizes or no obvious low-effort fix remains.

Start in this order:
1. inspect example inputs
2. refine the schema only if necessary
3. scaffold the codebase
4. implement a baseline parser
5. add validation and tests
6. add benchmark evaluation
7. add synthetic generation
8. iterate on failures

Completion criteria:
- tests pass
- schema validation passes
- benchmark report is generated
- failed cases are saved for remaining errors
- repository contains reproducible commands
