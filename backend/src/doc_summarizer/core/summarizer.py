import json
import logging

import anthropic

from doc_summarizer.config import settings

logger = logging.getLogger(__name__)

_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

_SYSTEM_PROMPT = """You are a document summarization assistant. Given document text, return a JSON object with:
- "summary_short": a 2-3 sentence summary
- "summary_long": a paragraph-length summary with key findings
- "key_topics": an array of 3-7 short topic tags

Respond with only the JSON object — no markdown, no explanation."""


def summarize_document(text: str) -> dict[str, str | list[str]]:
    message = _client.messages.create(
        model=settings.model,
        max_tokens=settings.max_tokens,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Summarize this document:\n\n{text[:50_000]}"}],
    )
    raw = message.content[0].text
    return json.loads(raw)
