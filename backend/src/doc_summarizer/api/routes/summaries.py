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
from doc_summarizer.core.summarizer import summarize_document
from doc_summarizer.db.models import Summary
from doc_summarizer.db.repository import SummaryRepository
from doc_summarizer.schemas.summary import SummaryPage, SummaryResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["summaries"])

SUPPORTED_TYPES = {"pdf", "docx", "txt", "md"}


@router.get("", response_model=SummaryPage)
async def list_summaries(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
) -> SummaryPage:
    repo = SummaryRepository(db)
    items, total = await repo.get_all(page, page_size)
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
    finally:
        os.unlink(tmp_path)

    if not text.strip():
        raise HTTPException(status_code=422, detail="Could not extract text from the document")

    logger.info("Summarizing %s (%d bytes)…", file.filename, len(contents))
    result = summarize_document(text)

    summary = Summary(
        file_path=file.filename or "upload",
        file_name=file.filename or "upload",
        file_type=ext,
        original_size_bytes=len(contents),
        content_hash=content_hash,
        summary_short=result["summary_short"],
        summary_long=result["summary_long"],
        key_topics=json.dumps(result.get("key_topics", [])),
    )
    saved = await repo.create(summary)
    logger.info("Saved summary id=%d for %s", saved.id, file.filename)
    return to_response(saved)
