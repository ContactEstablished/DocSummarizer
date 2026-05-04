from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from doc_summarizer.api.dependencies import get_db
from doc_summarizer.schemas.summary import SummaryCreate, SummaryPage, SummaryResponse

router = APIRouter(tags=["summaries"])


@router.get("", response_model=SummaryPage)
async def list_summaries(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
) -> SummaryPage:
    # TODO: implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{summary_id}", response_model=SummaryResponse)
async def get_summary(
    summary_id: int,
    db: AsyncSession = Depends(get_db),
) -> SummaryResponse:
    # TODO: implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.delete("/{summary_id}", status_code=204)
async def delete_summary(
    summary_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    # TODO: implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/upload", response_model=SummaryResponse, status_code=201)
async def upload_file(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
) -> SummaryResponse:
    # TODO: implement
    raise HTTPException(status_code=501, detail="Not implemented")
