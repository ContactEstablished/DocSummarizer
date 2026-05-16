import hashlib
import json
import logging
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from doc_summarizer.api.dependencies import get_db
from doc_summarizer.api.utils import to_response
from doc_summarizer.core.parser import parse_document
from doc_summarizer.core.summarizer import ask_about_document, summarize_document
from doc_summarizer.db.models import Summary
from doc_summarizer.db.repository import SummaryRepository
from doc_summarizer.schemas.summary import AskRequest, AskResponse, SummaryPage, SummaryResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["summaries"])

SUPPORTED_TYPES = {"pdf", "docx", "txt", "md"}


@router.get("", response_model=SummaryPage)
async def list_summaries(
    page: int = 1,
    page_size: int = 20,
    sort: str = "created_at",
    order: str = "desc",
    file_type: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> SummaryPage:
    repo = SummaryRepository(db)
    items, total = await repo.get_all(page, page_size, sort, order, file_type)
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


@router.patch("/{summary_id}/re-summarize", response_model=SummaryResponse)
async def re_summarize(
    summary_id: int,
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
    logger.info("Re-summarizing document id=%d (%s)", summary_id, summary.file_name)
    try:
        result = summarize_document(summary.extracted_text)
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


@router.post("/upload", response_model=SummaryResponse, status_code=201)
async def upload_file(
    file: UploadFile,
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

    logger.info("Summarizing %s (%d bytes)…", file.filename, len(contents))
    try:
        result = summarize_document(text)
    except ValueError as exc:
        # Claude returned non-JSON
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
        extracted_text=text[:50_000],  # store same slice used for summarization
    )
    saved = await repo.create(summary)
    logger.info("Saved summary id=%d for %s", saved.id, file.filename)
    return to_response(saved)
