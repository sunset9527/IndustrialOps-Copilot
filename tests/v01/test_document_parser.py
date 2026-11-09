from __future__ import annotations

from pathlib import Path

import pytest
from docx import Document
from pypdf import PdfWriter

from industrialops.services.document_parser import DocumentParseError, parse_document


def test_parse_document_extracts_utf8_text_with_a_stable_content_type(tmp_path: Path) -> None:
    source = tmp_path / "maintenance-note.txt"
    source.write_text("Inspect the coolant level.", encoding="utf-8")

    parsed = parse_document(source)

    assert parsed.content_type == "text/plain"
    assert parsed.text == "Inspect the coolant level."
    assert parsed.page_count is None


def test_parse_document_records_pdf_page_count_even_when_a_page_has_no_text(tmp_path: Path) -> None:
    source = tmp_path / "manual.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with source.open("wb") as stream:
        writer.write(stream)

    parsed = parse_document(source)

    assert parsed.content_type == "application/pdf"
    assert parsed.text == ""
    assert parsed.page_count == 1


def test_parse_document_extracts_paragraphs_from_docx(tmp_path: Path) -> None:
    source = tmp_path / "checklist.docx"
    document = Document()
    document.add_paragraph("Lock out energy sources first.")
    document.save(source)

    parsed = parse_document(source)

    assert parsed.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert parsed.text == "Lock out energy sources first."
    assert parsed.page_count is None


def test_parse_document_rejects_an_unsupported_file_type(tmp_path: Path) -> None:
    source = tmp_path / "manual.exe"
    source.write_bytes(b"not a document")

    with pytest.raises(DocumentParseError, match="Unsupported"):
        parse_document(source)
