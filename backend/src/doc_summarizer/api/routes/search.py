import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from doc_summarizer.api.dependencies import get_db
from doc_summarizer.api.utils import to_response
from doc_summarizer.db.repository import SummaryRepository
from doc_summarizer.schemas.summary import SummaryPage

logger = logging.getLogger(__name__)

router = APIRouter(tags=["search"])


@router.get("/search", response_model=SummaryPage)
async def search_summaries(
    q: str,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
) -> SummaryPage:
    repo = SummaryRepository(db)
    items, total = await repo.search(q, page, page_size)
    return SummaryPage(
        items=[to_response(s) for s in items],
        total=total,
        page=page,
        page_size=page_size,
    )
