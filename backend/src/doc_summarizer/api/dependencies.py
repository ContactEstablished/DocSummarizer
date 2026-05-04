from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from doc_summarizer.db.session import async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
