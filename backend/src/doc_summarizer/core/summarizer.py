import json
import logging
from collections.abc import Generator

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

# Built-in prompt templates — keys are sent from the frontend
PROMPT_TEMPLATES: dict[str, str] = {
    "default": _SYSTEM_PROMPT,
    "executive": (
        "You are an executive briefing assistant. Given document text, return a JSON object with:\n"
        '- "summary_short": a crisp 1-2 sentence executive summary highlighting the bottom line\n'
        '- "summary_long": a structured executive brief with: key findings, implications, and recommended actions\n'
        '- "key_topics": an array of 3-7 business-relevant topic tags\n\n'
        "Respond with only the JSON object — no markdown, no explanation."
    ),
    "bullets": (
        "You are a document summarization assistant. Given document text, return a JSON object with:\n"
        '- "summary_short": a 2-3 sentence overview\n'
        '- "summary_long": a bulleted list of the 5-10 most important points, each on its own line starting with "• "\n'
        '- "key_topics": an array of 3-7 short topic tags\n\n'
        "Respond with only the JSON object — no markdown, no explanation."
    ),
    "technical": (
        "You are a technical documentation assistant. Given document text, return a JSON object with:\n"
        '- "summary_short": a precise 2-3 sentence technical summary\n'
        '- "summary_long": a detailed technical analysis covering: methodology, key data/findings, '
        "technical implications, and limitations\n"
        '- "key_topics": an array of 3-7 technical topic tags\n\n'
        "Respond with only the JSON object — no markdown, no explanation."
    ),
    "simple": (
        "You are a friendly explanation assistant. Given document text, return a JSON object with:\n"
        '- "summary_short": a simple 2-3 sentence summary anyone could understand\n'
        '- "summary_long": an easy-to-understand explanation in plain language, avoiding jargon\n'
        '- "key_topics": an array of 3-7 simple topic tags\n\n'
        "Respond with only the JSON object — no markdown, no explanation."
    ),
}

# Only retry on transient errors — never on auth/permission failures
_RETRYABLE = (
    anthropic.RateLimitError,
    anthropic.InternalServerError,
    anthropic.APIConnectionError,
    anthropic.APITimeoutError,
)


def _resolve_prompt(template_key: str | None) -> str:
    """Return the system prompt for a given template key, or the default."""
    if not template_key:
        return _SYSTEM_PROMPT
    return PROMPT_TEMPLATES.get(template_key, _SYSTEM_PROMPT)


@retry(
    retry=retry_if_exception_type(_RETRYABLE),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(4),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def _call_api(text: str, system: str = _SYSTEM_PROMPT) -> str:
    message = _client.messages.create(
        model=settings.model,
        max_tokens=settings.max_tokens,
        system=system,
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


def summarize_document(
    text: str, prompt_template: str | None = None
) -> dict[str, str | list[str]]:
    """Call Claude to produce a structured summary. Retries up to 4 times on
    rate-limit and transient API errors with exponential backoff (2s → 60s)."""
    system = _resolve_prompt(prompt_template)
    raw = _call_api(text, system)
    cleaned = _strip_markdown_fences(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error("Claude returned non-JSON response: %s", raw[:200])
        raise ValueError("Summarizer returned invalid JSON") from exc


# ── Ask a question ─────────────────────────────────────────────────────────

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


def stream_ask_about_document(summary: str, question: str) -> Generator[str, None, None]:
    """Stream answer chunks from Claude using server-sent events."""
    with _client.messages.stream(
        model=settings.model,
        max_tokens=1024,
        system=_ASK_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Document summary:\n{summary}\n\nQuestion: {question}",
        }],
    ) as stream:
        for chunk in stream.text_stream:
            yield chunk
