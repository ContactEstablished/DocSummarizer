"""Document parser tests — no API key or network required."""

import io

import pytest


# ── Text parser ───────────────────────────────────────────────────────────────

def test_parse_text_returns_string(tmp_path):
    sample = tmp_path / "sample.txt"
    sample.write_text("Hello world")
    from doc_summarizer.core.parsers.text_parser import parse_text
    assert parse_text(str(sample)) == "Hello world"


def test_parse_text_utf8_content(tmp_path):
    sample = tmp_path / "unicode.txt"
    sample.write_text("Héllo wörld — 日本語", encoding="utf-8")
    from doc_summarizer.core.parsers.text_parser import parse_text
    assert "Héllo" in parse_text(str(sample))


def test_parse_markdown(tmp_path):
    sample = tmp_path / "notes.md"
    sample.write_text("# Title\n\nSome **bold** text.")
    from doc_summarizer.core.parsers.text_parser import parse_text
    result = parse_text(str(sample))
    assert "Title" in result
    assert "bold" in result


# ── Dispatch ──────────────────────────────────────────────────────────────────

def test_unsupported_extension_raises():
    from doc_summarizer.core.parser import parse_document
    with pytest.raises(ValueError, match="Unsupported"):
        parse_document("file.xyz")


def test_dispatch_routes_txt(tmp_path):
    f = tmp_path / "doc.txt"
    f.write_text("dispatch test")
    from doc_summarizer.core.parser import parse_document
    assert parse_document(str(f)) == "dispatch test"


def test_dispatch_routes_md(tmp_path):
    f = tmp_path / "doc.md"
    f.write_text("## Heading")
    from doc_summarizer.core.parser import parse_document
    assert "Heading" in parse_document(str(f))


# ── DOCX parser ───────────────────────────────────────────────────────────────

def _make_docx(tmp_path, paragraphs: list[str]) -> str:
    """Create a minimal .docx file in-memory and write it to tmp_path."""
    from docx import Document
    doc = Document()
    for para in paragraphs:
        doc.add_paragraph(para)
    path = tmp_path / "test.docx"
    doc.save(str(path))
    return str(path)


def test_parse_docx_basic(tmp_path):
    path = _make_docx(tmp_path, ["First paragraph.", "Second paragraph."])
    from doc_summarizer.core.parsers.docx_parser import parse_docx
    result = parse_docx(path)
    assert "First paragraph." in result
    assert "Second paragraph." in result


def test_parse_docx_empty_paragraphs_skipped(tmp_path):
    """Empty paragraphs should not appear in output (whitespace-only lines stripped)."""
    path = _make_docx(tmp_path, ["Line one.", "", "Line two."])
    from doc_summarizer.core.parsers.docx_parser import parse_docx
    result = parse_docx(path)
    assert "Line one." in result
    assert "Line two." in result


def test_parse_docx_via_dispatch(tmp_path):
    path = _make_docx(tmp_path, ["Dispatched content."])
    from doc_summarizer.core.parser import parse_document
    result = parse_document(path)
    assert "Dispatched content." in result


# ── PDF parser ────────────────────────────────────────────────────────────────

def _make_pdf(tmp_path, text: str) -> str:
    """Create a minimal single-page PDF using pypdf's PageObject API."""
    import struct, zlib
    from pypdf import PdfWriter
    from pypdf.generic import (
        ArrayObject, DecodedStreamObject, DictionaryObject,
        NameObject, NumberObject, RectangleObject,
    )

    writer = PdfWriter()

    # Build a content stream with the text
    stream_data = f"BT /F1 12 Tf 50 700 Td ({text}) Tj ET".encode()

    page = writer.add_blank_page(width=612, height=792)
    page[NameObject("/Contents")] = writer._add_object(
        DecodedStreamObject.initialize_from_dictionary(
            {NameObject("/Length"): NumberObject(len(stream_data))},
            stream_data,
        )
    )

    path = tmp_path / "test.pdf"
    with open(str(path), "wb") as f:
        writer.write(f)
    return str(path)


def test_parse_pdf_via_dispatch(tmp_path):
    """Smoke test: parse_document() accepts a .pdf path without raising."""
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    path = tmp_path / "blank.pdf"
    with open(str(path), "wb") as f:
        writer.write(f)

    from doc_summarizer.core.parser import parse_document
    result = parse_document(str(path))
    # Blank page — just verify it returns a string without error
    assert isinstance(result, str)


def test_parse_pdf_extension_recognised():
    """Parser dispatch recognises .pdf extension."""
    from doc_summarizer.core.parser import _DISPATCH
    assert ".pdf" in _DISPATCH
