from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from src.parser.core import ProtocolTableParser

RNG = random.Random(20260323)


def _rand_word() -> str:
    vocab = ["Visit", "Window", "Dose", "Assessment", "Group", "Cohort", "Result", "Value"]
    return RNG.choice(vocab)


def _make_table_text(case_idx: int) -> str:
    cols = RNG.randint(3, 6)
    rows = RNG.randint(4, 8)
    header_depth = RNG.randint(1, 2)
    base_title = f"{_rand_word()} Schedule"
    title = f"Table {case_idx}: {base_title}"

    header_rows: list[list[str]] = []
    for h in range(header_depth):
        header_rows.append([f"{_rand_word()}_{h}_{c}" for c in range(cols)])

    body = [[f"R{r}C{c}" for c in range(cols)] for r in range(rows)]
    if rows > 5:
        body[1][0] = ""

    lines = [title]
    for row in header_rows + body:
        lines.append("  ".join(row))
    lines.append("* A1 applies to subgroup")
    if case_idx % 3 == 0:
        lines.append("Note: synthetic continuation candidate")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate deterministic synthetic benchmark cases")
    ap.add_argument("--out-dir", default="benchmarks/cases/synthetic")
    ap.add_argument("--gold-dir", default="benchmarks/gold/synthetic")
    ap.add_argument("--num-cases", type=int, default=12)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    gold_dir = Path(args.gold_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    gold_dir.mkdir(parents=True, exist_ok=True)

    parser = ProtocolTableParser()
    for i in range(1, args.num_cases + 1):
        doc = _make_table_text(i)
        case_name = f"case_{i:03d}"
        case_path = out_dir / f"{case_name}.txt"
        case_path.write_text(doc, encoding="utf-8")
        expected = parser.parse_text_file(case_path).to_dict()
        (gold_dir / f"{case_name}.json").write_text(
            json.dumps(expected, indent=2, sort_keys=True), encoding="utf-8"
        )

    print(f"Generated {args.num_cases} deterministic synthetic cases.")


if __name__ == "__main__":
    main()
