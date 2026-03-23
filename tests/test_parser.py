from __future__ import annotations

from src.parser.core import ProtocolTableParser


def test_parse_simple_table_text() -> None:
    text = """Table 1: Demo\nColA  ColB\nA1  B1\nA2  B2\n* a) note for A1"""
    parser = ProtocolTableParser()
    doc = parser.parse_pages([text]).to_dict()
    assert len(doc["tables"]) == 1
    table = doc["tables"][0]
    assert table["page_number"] == 1
    assert len(table["data"]["rows"]) == 3
    assert table["data"]["footnotes"][0]["symbol"] == "*"


def test_continuation_merge() -> None:
    parser = ProtocolTableParser()
    pages = [
        "Table 1: Exposure\nA  B\n1  2",
        "Table 2: Exposure (Continued)\nA  B\n3  4",
    ]
    out = parser.parse_pages(pages).to_dict()
    assert len(out["tables"]) == 1
    assert len(out["tables"][0]["data"]["rows"]) == 4


def test_deterministic_output() -> None:
    parser = ProtocolTableParser()
    pages = ["Table 1: X\nA  B\nx  y"]
    first = parser.parse_pages(pages).to_dict()
    second = parser.parse_pages(pages).to_dict()
    assert first == second
