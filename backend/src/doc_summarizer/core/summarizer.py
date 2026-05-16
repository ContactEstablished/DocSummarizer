import json
import logging

import anthropic
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from doc_summarizer.config import settings

logger = logging.getLogger(__name__)

_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

_SYSTEM_PROMPT = """You are a document summarization assistant. Given document text, return a JSON object with:
- "summary_short": a 2-3 sentence summary
- "summary_long": a paragraph-length summary with key findings
- "key_topics": an array of 3-7 short topic tags

Respond with only the JSON object — no markdown, no explanation."""

_RETRYABLE = (
    anthropic.RateLimitError,
    anthropic.APIStatusError,
    anthropic.APIConnectionError,
    anthropic.APITimeoutError,
)


@retry(
    retry=retry_if_exception_type(_RETRYABLE),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(4),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def _call_api(text: str) -> str:
    message = _client.messages.create(
        model=settings.model,
        max_tokens=settings.max_tokens,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Summarize this document:\n\n{text[:50_000]}"}],
    )
    return message.content[0].text


def summarize_document(text: str) -> dict[str, str | list[str]]:
    """Call Claude to produce a structured summary. Retries up to 4 times on
    rate-limit and transient API errors with exponential backoff (2s → 60s)."""
    raw = _call_api(text)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("Claude returned non-JSON response: %s", raw[:200])
        raise ValueError("Summarizer returned invalid JSON") from exc
