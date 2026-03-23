from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass(frozen=True)
class Cell:
    text: str
    rowspan: int = 1
    colspan: int = 1


@dataclass(frozen=True)
class Row:
    cells: list[Cell]


@dataclass(frozen=True)
class Column:
    name: str
    colspan: int = 1


@dataclass(frozen=True)
class ColumnGroup:
    name: str
    start_col: int
    end_col: int


@dataclass(frozen=True)
class Footnote:
    note_id: int
    symbol: str
    text: str
    applies_to: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class TableData:
    columns: list[Column]
    column_groups: list[ColumnGroup]
    rows: list[Row]
    footnotes: list[Footnote]
    notes_below_table: list[str]


@dataclass(frozen=True)
class Table:
    table_id: int
    page_number: int
    title: str
    caption: str
    data: TableData


@dataclass(frozen=True)
class DocumentTables:
    tables: list[Table]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["tables"] = sorted(
            payload["tables"], key=lambda t: (t["page_number"], t["table_id"], t["title"])
        )
        return payload
