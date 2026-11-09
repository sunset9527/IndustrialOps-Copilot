"""Text extraction for permitted uploaded document formats."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from docx import Document
from pypdf import PdfReader


@dataclass(frozen=True)
class ParsedDocument:
    """The text and basic format metadata extracted from an uploaded document."""

    text: str
    content_type: str
    page_count: int | None


class DocumentParseError(ValueError):
    """Raised when a document cannot be parsed by the permitted format handlers."""


def parse_document(path: Path) -> ParsedDocument:
    """Extract text from an allowed local upload without modifying it."""

    suffix = path.suffix.casefold()
    if suffix == ".txt":
        return ParsedDocument(text=path.read_text(encoding="utf-8"), content_type="text/plain", page_count=None)
    if suffix == ".pdf":
        reader = PdfReader(path)
        return ParsedDocument(
            text="\n".join(page.extract_text() or "" for page in reader.pages).strip(),
            content_type="application/pdf",
            page_count=len(reader.pages),
        )
    if suffix == ".docx":
        document = Document(path)
        return ParsedDocument(
            text="\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text).strip(),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            page_count=None,
        )
    raise DocumentParseError(f"Unsupported document type: {suffix or 'no extension'}")
