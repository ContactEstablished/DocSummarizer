from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from doc_summarizer.api.dependencies import get_db
from doc_summarizer.schemas.summary import SummaryPage

router = APIRouter(tags=["search"])


@router.get("/search", response_model=SummaryPage)
async def search_summaries(
    q: str,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
) -> SummaryPage:
    # TODO: implement full-text search
    raise HTTPException(status_code=501, detail="Not implemented")
