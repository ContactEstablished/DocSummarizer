from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from doc_summarizer.config import settings
from doc_summarizer.db.models import Base


def _ensure_db_dir() -> None:
    """Create the directory that will hold the SQLite file if it doesn't exist."""
    url = settings.database_url
    # Extract file path from sqlite+aiosqlite:///./path/to/db.sqlite
    if "///" in url:
        db_path = url.split("///", 1)[1]
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)


_ensure_db_dir()
engine = create_async_engine(settings.database_url, echo=False)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
