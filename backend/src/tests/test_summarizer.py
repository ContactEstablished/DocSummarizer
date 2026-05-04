"""Summarizer tests — requires a valid ANTHROPIC_API_KEY to run against the real API."""

import pytest


@pytest.mark.skip(reason="Requires live API key — run manually")
def test_summarize_returns_expected_keys():
    from doc_summarizer.core.summarizer import summarize_document
    result = summarize_document("This is a test document about artificial intelligence.")
    assert "summary_short" in result
    assert "summary_long" in result
    assert "key_topics" in result
    assert isinstance(result["key_topics"], list)
