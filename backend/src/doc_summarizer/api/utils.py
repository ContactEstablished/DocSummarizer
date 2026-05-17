import json

from doc_summarizer.db.models import Summary
from doc_summarizer.schemas.summary import SummaryResponse


def to_response(summary: Summary) -> SummaryResponse:
    return SummaryResponse(
        id=summary.id,
        file_name=summary.file_name,
        file_path=summary.file_path,
        file_type=summary.file_type,
        original_size_bytes=summary.original_size_bytes,
        content_hash=summary.content_hash,
        summary_short=summary.summary_short,
        summary_long=summary.summary_long,
        key_topics=json.loads(summary.key_topics),
        is_starred=summary.is_starred,
        created_at=summary.created_at,
        updated_at=summary.updated_at,
    )
