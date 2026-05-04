from datetime import datetime

from pydantic import BaseModel


class SummaryResponse(BaseModel):
    id: int
    file_name: str
    file_path: str
    file_type: str
    original_size_bytes: int
    content_hash: str
    summary_short: str
    summary_long: str
    key_topics: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SummaryCreate(BaseModel):
    file_path: str
    file_name: str
    file_type: str
    original_size_bytes: int
    content_hash: str
    summary_short: str
    summary_long: str
    key_topics: list[str]


class SummaryPage(BaseModel):
    items: list[SummaryResponse]
    total: int
    page: int
    page_size: int
