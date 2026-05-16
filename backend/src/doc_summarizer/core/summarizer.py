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

# Only retry on transient errors — never on auth/permission failures
_RETRYABLE = (
    anthropic.RateLimitError,
    anthropic.InternalServerError,
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


def _strip_markdown_fences(text: str) -> str:
    """Remove ```json ... ``` or ``` ... ``` wrappers Claude sometimes adds."""
    stripped = text.strip()
    if stripped.startswith("```"):
        # Drop the opening fence line and the closing fence
        lines = stripped.splitlines()
        inner = lines[1:] if lines[0].startswith("```") else lines
        if inner and inner[-1].strip() == "```":
            inner = inner[:-1]
        return "\n".join(inner).strip()
    return stripped


def summarize_document(text: str) -> dict[str, str | list[str]]:
    """Call Claude to produce a structured summary. Retries up to 4 times on
    rate-limit and transient API errors with exponential backoff (2s → 60s)."""
    raw = _call_api(text)
    cleaned = _strip_markdown_fences(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error("Claude returned non-JSON response: %s", raw[:200])
        raise ValueError("Summarizer returned invalid JSON") from exc


_ASK_SYSTEM_PROMPT = """You are a helpful assistant that answers questions about documents.
You are given a document summary and a user question. Answer the question based on the
summary content. Be concise but complete. If the summary doesn't contain enough information
to answer fully, say so clearly."""


@retry(
    retry=retry_if_exception_type(_RETRYABLE),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(3),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def _call_ask_api(summary: str, question: str) -> str:
    message = _client.messages.create(
        model=settings.model,
        max_tokens=1024,
        system=_ASK_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Document summary:\n{summary}\n\nQuestion: {question}",
        }],
    )
    return message.content[0].text


def ask_about_document(summary: str, question: str) -> str:
    """Ask a question about a document summary. Returns Claude's answer."""
    return _call_ask_api(summary, question)
