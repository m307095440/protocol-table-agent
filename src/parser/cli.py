from __future__ import annotations

import argparse

from .core import ProtocolTableParser


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse protocol PDFs/text to table JSON")
    parser.add_argument("input", help="Input PDF or text file")
    parser.add_argument("output", help="Output JSON path")
    args = parser.parse_args()
    ProtocolTableParser().parse_to_json(args.input, args.output)


if __name__ == "__main__":
    main()
