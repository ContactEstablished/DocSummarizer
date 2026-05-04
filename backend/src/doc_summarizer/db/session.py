from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from doc_summarizer.config import settings
from doc_summarizer.db.models import Base

engine = create_async_engine(settings.database_url, echo=False)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
