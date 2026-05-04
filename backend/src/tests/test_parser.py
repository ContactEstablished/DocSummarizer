import pytest


def test_parse_text_returns_string(tmp_path):
    sample = tmp_path / "sample.txt"
    sample.write_text("Hello world")
    from doc_summarizer.core.parsers.text_parser import parse_text
    assert parse_text(str(sample)) == "Hello world"


def test_unsupported_extension_raises():
    from doc_summarizer.core.parser import parse_document
    with pytest.raises(ValueError, match="Unsupported"):
        parse_document("file.xyz")
