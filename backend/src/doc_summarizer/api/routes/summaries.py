import hashlib
import json
import logging
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from doc_summarizer.api.dependencies import get_db
from doc_summarizer.api.utils import to_response
from doc_summarizer.core.parser import parse_document
from doc_summarizer.core.summarizer import (
    PROMPT_TEMPLATES,
    ask_about_document,
    stream_ask_about_document,
    summarize_document,
)
from doc_summarizer.db.models import Summary
from doc_summarizer.db.repository import SummaryRepository
from doc_summarizer.schemas.summary import (
    AskRequest,
    AskResponse,
    SummaryPage,
    SummaryResponse,
    TemplateInfo,
    TopicCount,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["summaries"])

SUPPORTED_TYPES = {"pdf", "docx", "txt", "md"}

_TEMPLATE_META: list[TemplateInfo] = [
    TemplateInfo(key="default", label="Default", description="Balanced short + long summary with topic tags"),
    TemplateInfo(key="executive", label="Executive Brief", description="Bottom-line focus with findings, implications, and actions"),
    TemplateInfo(key="bullets", label="Bullet Points", description="Key points as a bulleted list"),
    TemplateInfo(key="technical", label="Technical", description="Detailed technical analysis with methodology and limitations"),
    TemplateInfo(key="simple", label="Simple / ELI5", description="Plain-language explanation, no jargon"),
]


# ── Templates ────────────────────────────────────────────────────────────────

@router.get("/templates", response_model=list[TemplateInfo])
async def list_templates() -> list[TemplateInfo]:
    """Return available prompt templates."""
    return _TEMPLATE_META


# ── Topics ───────────────────────────────────────────────────────────────────

@router.get("/topics", response_model=list[TopicCount])
async def list_topics(db: AsyncSession = Depends(get_db)) -> list[TopicCount]:
    """Return unique topics across all summaries with document counts."""
    repo = SummaryRepository(db)
    rows = await repo.get_topics()
    return [TopicCount(topic=t, count=c) for t, c in rows]


# ── CRUD ─────────────────────────────────────────────────────────────────────

@router.get("", response_model=SummaryPage)
async def list_summaries(
    page: int = 1,
    page_size: int = 20,
    sort: str = "created_at",
    order: str = "desc",
    file_type: str | None = None,
    topic: str | None = None,
    starred_only: bool = False,
    db: AsyncSession = Depends(get_db),
) -> SummaryPage:
    repo = SummaryRepository(db)
    items, total = await repo.get_all(
        page, page_size, sort, order, file_type, topic, starred_only
    )
    return SummaryPage(
        items=[to_response(s) for s in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{summary_id}", response_model=SummaryResponse)
async def get_summary(
    summary_id: int,
    db: AsyncSession = Depends(get_db),
) -> SummaryResponse:
    repo = SummaryRepository(db)
    summary = await repo.get_by_id(summary_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Summary not found")
    return to_response(summary)


@router.delete("/{summary_id}", status_code=204)
async def delete_summary(
    summary_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    repo = SummaryRepository(db)
    summary = await repo.get_by_id(summary_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Summary not found")
    await repo.delete(summary)


@router.patch("/{summary_id}/star", response_model=SummaryResponse)
async def toggle_star(
    summary_id: int,
    db: AsyncSession = Depends(get_db),
) -> SummaryResponse:
    """Toggle the starred status of a summary."""
    repo = SummaryRepository(db)
    summary = await repo.get_by_id(summary_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Summary not found")
    updated = await repo.toggle_star(summary)
    return to_response(updated)


@router.patch("/{summary_id}/re-summarize", response_model=SummaryResponse)
async def re_summarize(
    summary_id: int,
    prompt_template: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> SummaryResponse:
    """Re-run Claude on the stored extracted text for an existing summary."""
    repo = SummaryRepository(db)
    summary = await repo.get_by_id(summary_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Summary not found")
    if not summary.extracted_text:
        raise HTTPException(
            status_code=422,
            detail="No extracted text stored for this document. Re-upload the file to enable re-summarization.",
        )
    logger.info("Re-summarizing document id=%d (%s) with template=%s", summary_id, summary.file_name, prompt_template or "default")
    try:
        result = summarize_document(summary.extracted_text, prompt_template)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Anthropic API error re-summarizing id=%d", summary_id)
        raise HTTPException(status_code=502, detail=f"Summarization failed: {exc}") from exc

    updated = await repo.update_summary_fields(
        summary,
        summary_short=result["summary_short"],
        summary_long=result["summary_long"],
        key_topics=json.dumps(result.get("key_topics", [])),
    )
    logger.info("Re-summarized id=%d successfully", summary_id)
    return to_response(updated)


# ── Ask a question ───────────────────────────────────────────────────────────

@router.post("/{summary_id}/ask", response_model=AskResponse)
async def ask_question(
    summary_id: int,
    body: AskRequest,
    db: AsyncSession = Depends(get_db),
) -> AskResponse:
    """Ask Claude a question grounded in a document's stored summary."""
    repo = SummaryRepository(db)
    summary = await repo.get_by_id(summary_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Summary not found")
    if not body.question.strip():
        raise HTTPException(status_code=422, detail="Question cannot be empty")
    logger.info("Answering question for id=%d: %s", summary_id, body.question[:80])
    try:
        answer = ask_about_document(summary.summary_long, body.question)
    except Exception as exc:
        logger.exception("Anthropic API error answering question for id=%d", summary_id)
        raise HTTPException(status_code=502, detail=f"Failed to answer question: {exc}") from exc
    return AskResponse(answer=answer)


@router.post("/{summary_id}/ask/stream")
async def ask_question_stream(
    summary_id: int,
    body: AskRequest,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Stream Claude's answer as Server-Sent Events."""
    repo = SummaryRepository(db)
    summary = await repo.get_by_id(summary_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Summary not found")
    if not body.question.strip():
        raise HTTPException(status_code=422, detail="Question cannot be empty")
    logger.info("Streaming answer for id=%d: %s", summary_id, body.question[:80])

    def generate():
        try:
            for chunk in stream_ask_about_document(summary.summary_long, body.question):
                yield f"data: {json.dumps({'text': chunk})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as exc:
            logger.exception("Anthropic API error streaming answer for id=%d", summary_id)
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ── Upload ───────────────────────────────────────────────────────────────────

@router.post("/upload", response_model=SummaryResponse, status_code=201)
async def upload_file(
    file: UploadFile,
    prompt_template: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
) -> SummaryResponse:
    ext = Path(file.filename or "").suffix.lstrip(".").lower()
    if ext not in SUPPORTED_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type '.{ext}'. Supported: {', '.join(sorted(SUPPORTED_TYPES))}",
        )

    contents = await file.read()
    content_hash = hashlib.sha256(contents).hexdigest()

    repo = SummaryRepository(db)
    existing = await repo.get_by_hash(content_hash)
    if existing:
        logger.info("Duplicate file detected, returning cached summary: %s", file.filename)
        return to_response(existing)

    with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        text = parse_document(tmp_path)
    except Exception as exc:
        logger.exception("Failed to parse %s", file.filename)
        raise HTTPException(status_code=422, detail=f"Could not parse document: {exc}") from exc
    finally:
        os.unlink(tmp_path)

    if not text.strip():
        raise HTTPException(status_code=422, detail="Could not extract text from the document")

    logger.info("Summarizing %s (%d bytes) template=%s…", file.filename, len(contents), prompt_template or "default")
    try:
        result = summarize_document(text, prompt_template)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Anthropic API error for %s", file.filename)
        raise HTTPException(status_code=502, detail=f"Summarization failed: {exc}") from exc

    summary = Summary(
        file_path=file.filename or "upload",
        file_name=file.filename or "upload",
        file_type=ext,
        original_size_bytes=len(contents),
        content_hash=content_hash,
        summary_short=result["summary_short"],
        summary_long=result["summary_long"],
        key_topics=json.dumps(result.get("key_topics", [])),
        extracted_text=text[:50_000],
    )
    saved = await repo.create(summary)
    logger.info("Saved summary id=%d for %s", saved.id, file.filename)
    return to_response(saved)
