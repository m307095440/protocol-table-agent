from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .models import Cell, Column, ColumnGroup, DocumentTables, Footnote, Row, Table, TableData

_TABLE_TITLE_RE = re.compile(r"^\s*table\s*\d+[\.:\-]?\s*(.*)$", re.IGNORECASE)
_FOOTNOTE_RE = re.compile(r"^\s*([*†‡]|\d+[\)\.:\-]|[a-zA-Z][\)\.:\-])\s+(.+)$")


@dataclass(frozen=True)
class ParserConfig:
    split_pattern: str = r"\s{2,}|\|"
    min_rows_for_table: int = 2
    max_header_rows: int = 3


class ProtocolTableParser:
    def __init__(self, config: ParserConfig | None = None) -> None:
        self.config = config or ParserConfig()
        self._splitter = re.compile(self.config.split_pattern)

    def parse_pdf(self, pdf_path: str | Path) -> DocumentTables:
        page_texts = self._extract_pdf_pages(pdf_path)
        return self.parse_pages(page_texts)

    def _extract_pdf_pages(self, pdf_path: str | Path) -> list[str]:
        pdf_path = str(pdf_path)
        cmd = ["pdftotext", "-layout", pdf_path, "-"]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
            txt = proc.stdout
            return txt.split("\f") if txt else [""]
        except (FileNotFoundError, subprocess.CalledProcessError):
            # Deterministic fallback when local PDF text extraction is unavailable.
            return [""]

    def parse_pages(self, page_texts: list[str]) -> DocumentTables:
        tables: list[Table] = []
        next_id = 1
        for page_number, text in enumerate(page_texts, start=1):
            page_tables = self._extract_tables_from_page(text, page_number, next_id)
            tables.extend(page_tables)
            next_id += len(page_tables)

        merged = self._merge_continuations(tables)
        return DocumentTables(tables=merged)

    def parse_text_file(self, path: str | Path) -> DocumentTables:
        lines = Path(path).read_text(encoding="utf-8").split("\f")
        return self.parse_pages(lines)

    def parse_to_json(self, input_path: str | Path, output_path: str | Path) -> None:
        input_path = Path(input_path)
        parsed = self.parse_pdf(input_path) if input_path.suffix.lower() == ".pdf" else self.parse_text_file(input_path)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(json.dumps(parsed.to_dict(), indent=2, sort_keys=True), encoding="utf-8")

    def _extract_tables_from_page(self, page_text: str, page_number: int, start_id: int) -> list[Table]:
        lines = [l.rstrip() for l in page_text.splitlines() if l.strip()]

        blocks: list[tuple[str, list[str], list[str]]] = []
        current_title = ""
        current_rows: list[str] = []
        current_notes: list[str] = []

        def flush() -> None:
            nonlocal current_title, current_rows, current_notes
            if len(current_rows) >= self.config.min_rows_for_table:
                blocks.append((current_title, current_rows[:], current_notes[:]))
            current_title = ""
            current_rows = []
            current_notes = []

        for line in lines:
            norm = self._normalize_line(line)
            title_match = _TABLE_TITLE_RE.match(norm)
            if title_match:
                flush()
                suffix = title_match.group(1).strip()
                current_title = suffix or norm
                continue

            if self._is_note_line(norm):
                current_notes.append(norm)
                continue

            cells = self._split_row(line)
            if len(cells) >= 2:
                current_rows.append(line.strip())
            elif current_rows:
                flush()

        flush()

        tables: list[Table] = []
        for idx, (title, row_lines, note_lines) in enumerate(blocks):
            rows = [Row(cells=[Cell(text=c, rowspan=1, colspan=1) for c in self._split_row(r)]) for r in row_lines]
            padded_rows = self._normalize_row_width(rows)
            table = Table(
                table_id=start_id + idx,
                page_number=page_number,
                title=title or f"Table on page {page_number}",
                caption=title or "",
                data=TableData(
                    columns=self._infer_columns(padded_rows),
                    column_groups=self._infer_column_groups(padded_rows),
                    rows=padded_rows,
                    footnotes=self._parse_footnotes(note_lines),
                    notes_below_table=[n for n in note_lines if not _FOOTNOTE_RE.match(n)],
                ),
            )
            tables.append(table)
        return tables

    def _normalize_row_width(self, rows: list[Row]) -> list[Row]:
        width = max((len(r.cells) for r in rows), default=0)
        return [
            Row(cells=row.cells + [Cell(text="", rowspan=1, colspan=1) for _ in range(width - len(row.cells))])
            for row in rows
        ]

    def _infer_columns(self, rows: list[Row]) -> list[Column]:
        if not rows:
            return []
        header_rows = self._header_rows(rows)
        width = len(rows[0].cells)
        columns: list[Column] = []
        for col_idx in range(width):
            header_bits = [r.cells[col_idx].text for r in header_rows if r.cells[col_idx].text]
            name = " | ".join(dict.fromkeys(header_bits)) if header_bits else f"column_{col_idx + 1}"
            columns.append(Column(name=name, colspan=1))
        return columns

    def _infer_column_groups(self, rows: list[Row]) -> list[ColumnGroup]:
        if len(rows) < 2:
            return []
        groups: list[ColumnGroup] = []
        first_header = rows[0].cells
        i = 0
        while i < len(first_header):
            name = first_header[i].text
            j = i + 1
            while j < len(first_header) and first_header[j].text == name:
                j += 1
            if name and j - i > 1:
                groups.append(ColumnGroup(name=name, start_col=i, end_col=j - 1))
            i = j
        return groups

    def _header_rows(self, rows: list[Row]) -> list[Row]:
        headers: list[Row] = []
        for row in rows[: self.config.max_header_rows]:
            joined = " ".join(c.text for c in row.cells)
            alpha = len(re.findall(r"[A-Za-z]", joined))
            digit = len(re.findall(r"\d", joined))
            if alpha >= digit:
                headers.append(row)
            else:
                break
        return headers or rows[:1]

    def _parse_footnotes(self, lines: list[str]) -> list[Footnote]:
        out: list[Footnote] = []
        for line in lines:
            m = _FOOTNOTE_RE.match(line)
            if not m:
                continue
            symbol = m.group(1)
            if len(symbol) > 1 and symbol[0].isalpha() and symbol[-1] in ").:-":
                symbol = symbol[0]
            text = m.group(2)
            out.append(Footnote(note_id=len(out) + 1, symbol=symbol, text=text, applies_to=sorted(set(re.findall(r"\b[A-Za-z]\d+\b", text)))))
        return out

    def _split_row(self, line: str) -> list[str]:
        return [self._normalize_line(p) for p in self._splitter.split(line) if self._normalize_line(p)]

    def _is_note_line(self, line: str) -> bool:
        if line.lower().startswith("note:"):
            return True
        if re.match(r"^\s*[*†‡]\s+", line):
            return True
        return bool(_FOOTNOTE_RE.match(line))

    def _normalize_line(self, line: str) -> str:
        return re.sub(r"\s+", " ", line).strip()

    def _merge_continuations(self, tables: list[Table]) -> list[Table]:
        merged: list[Table] = []
        for table in tables:
            if merged and self._is_continuation(merged[-1], table):
                prev = merged[-1]
                merged[-1] = Table(
                    table_id=prev.table_id,
                    page_number=prev.page_number,
                    title=prev.title,
                    caption=prev.caption,
                    data=TableData(
                        columns=prev.data.columns,
                        column_groups=prev.data.column_groups,
                        rows=prev.data.rows + table.data.rows,
                        footnotes=prev.data.footnotes + table.data.footnotes,
                        notes_below_table=prev.data.notes_below_table + table.data.notes_below_table,
                    ),
                )
            else:
                merged.append(table)
        return merged

    def _is_continuation(self, prev: Table, curr: Table) -> bool:
        p = prev.title.lower().replace("(continued)", "").strip()
        c = curr.title.lower().replace("(continued)", "").strip()
        return bool(p and p == c and curr.page_number == prev.page_number + 1)
