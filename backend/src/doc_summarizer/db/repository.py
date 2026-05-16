from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from doc_summarizer.db.models import Summary

_SORT_COLS: dict[str, Any] = {
    "created_at": Summary.created_at,
    "file_name": Summary.file_name,
    "original_size_bytes": Summary.original_size_bytes,
}


class SummaryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
        sort: str = "created_at",
        order: str = "desc",
        file_type: str | None = None,
    ) -> tuple[list[Summary], int]:
        offset = (page - 1) * page_size
        col = _SORT_COLS.get(sort, Summary.created_at)
        order_clause = col.desc() if order != "asc" else col.asc()

        conditions = []
        if file_type:
            conditions.append(Summary.file_type == file_type)

        items_q = select(Summary).order_by(order_clause).offset(offset).limit(page_size)
        count_q = select(func.count()).select_from(Summary)
        if conditions:
            items_q = items_q.where(*conditions)
            count_q = count_q.where(*conditions)

        items_result = await self.session.execute(items_q)
        items = list(items_result.scalars())
        count_result = await self.session.execute(count_q)
        total = count_result.scalar_one()
        return items, total

    async def get_by_id(self, summary_id: int) -> Summary | None:
        result = await self.session.execute(select(Summary).where(Summary.id == summary_id))
        return result.scalar_one_or_none()

    async def get_by_hash(self, content_hash: str) -> Summary | None:
        result = await self.session.execute(
            select(Summary).where(Summary.content_hash == content_hash)
        )
        return result.scalar_one_or_none()

    async def create(self, summary: Summary) -> Summary:
        self.session.add(summary)
        await self.session.commit()
        await self.session.refresh(summary)
        return summary

    async def update_summary_fields(
        self,
        summary: Summary,
        summary_short: str,
        summary_long: str,
        key_topics: str,
    ) -> Summary:
        """Update the summary text fields after re-summarization."""
        summary.summary_short = summary_short
        summary.summary_long = summary_long
        summary.key_topics = key_topics
        await self.session.commit()
        await self.session.refresh(summary)
        return summary

    async def delete(self, summary: Summary) -> None:
        await self.session.delete(summary)
        await self.session.commit()

    async def search(self, query: str, page: int = 1, page_size: int = 20) -> tuple[list[Summary], int]:
        """Full-text search using FTS5, ranked by BM25 relevance.
        Falls back to LIKE search if FTS5 is unavailable."""
        offset = (page - 1) * page_size
        try:
            return await self._search_fts5(query, page_size, offset)
        except Exception:
            return await self._search_like(query, page_size, offset)

    async def _search_fts5(
        self, query: str, page_size: int, offset: int
    ) -> tuple[list[Summary], int]:
        """BM25-ranked FTS5 search. Returns IDs in relevance order, then fetches ORM objects."""
        # Wrap in double-quotes for phrase search; escape existing quotes
        safe_q = query.strip().replace('"', '""')
        match_expr = f'"{safe_q}"' if " " in safe_q else safe_q + "*"

        ids_result = await self.session.execute(
            text(
                "SELECT rowid FROM summaries_fts WHERE summaries_fts MATCH :q"
                " ORDER BY bm25(summaries_fts) LIMIT :limit OFFSET :offset"
            ),
            {"q": match_expr, "limit": page_size, "offset": offset},
        )
        ids = [row[0] for row in ids_result]

        count_result = await self.session.execute(
            text("SELECT COUNT(*) FROM summaries_fts WHERE summaries_fts MATCH :q"),
            {"q": match_expr},
        )
        total = count_result.scalar_one()

        if not ids:
            return [], total

        # Fetch ORM objects, preserving relevance order
        orm_result = await self.session.execute(select(Summary).where(Summary.id.in_(ids)))
        by_id = {s.id: s for s in orm_result.scalars()}
        items = [by_id[i] for i in ids if i in by_id]
        return items, total

    async def _search_like(
        self, query: str, page_size: int, offset: int
    ) -> tuple[list[Summary], int]:
        """LIKE-based fallback search (case-insensitive)."""
        like = f"%{query}%"
        where_clause = (
            Summary.summary_short.ilike(like)
            | Summary.summary_long.ilike(like)
            | Summary.file_name.ilike(like)
            | Summary.key_topics.ilike(like)
        )
        items_result = await self.session.execute(
            select(Summary)
            .where(where_clause)
            .order_by(Summary.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        items = list(items_result.scalars())
        count_result = await self.session.execute(
            select(func.count()).select_from(Summary).where(where_clause)
        )
        total = count_result.scalar_one()
        return items, total
