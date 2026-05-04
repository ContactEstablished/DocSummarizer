from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from doc_summarizer.db.models import Summary


class SummaryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all(self, page: int = 1, page_size: int = 20) -> tuple[list[Summary], int]:
        offset = (page - 1) * page_size
        result = await self.session.execute(
            select(Summary).order_by(Summary.created_at.desc()).offset(offset).limit(page_size)
        )
        items = list(result.scalars())
        count_result = await self.session.execute(select(Summary))
        total = len(list(count_result.scalars()))
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

    async def delete(self, summary: Summary) -> None:
        await self.session.delete(summary)
        await self.session.commit()

    async def search(self, query: str, page: int = 1, page_size: int = 20) -> tuple[list[Summary], int]:
        offset = (page - 1) * page_size
        like = f"%{query}%"
        stmt = (
            select(Summary)
            .where(
                Summary.summary_short.ilike(like)
                | Summary.summary_long.ilike(like)
                | Summary.file_name.ilike(like)
                | Summary.key_topics.ilike(like)
            )
            .order_by(Summary.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.session.execute(stmt)
        items = list(result.scalars())
        return items, len(items)
