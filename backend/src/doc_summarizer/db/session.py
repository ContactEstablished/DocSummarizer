import logging
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from doc_summarizer.config import settings
from doc_summarizer.db.models import Base

logger = logging.getLogger(__name__)


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

# SQL for FTS5 virtual table and sync triggers
_FTS_DDL = [
    # Virtual table backed by the summaries content table
    """CREATE VIRTUAL TABLE IF NOT EXISTS summaries_fts USING fts5(
        file_name,
        summary_short,
        summary_long,
        key_topics,
        content='summaries',
        content_rowid='id'
    )""",
    # Keep FTS in sync on INSERT
    """CREATE TRIGGER IF NOT EXISTS summaries_fts_ai
       AFTER INSERT ON summaries BEGIN
           INSERT INTO summaries_fts(rowid, file_name, summary_short, summary_long, key_topics)
           VALUES (new.id, new.file_name, new.summary_short, new.summary_long, new.key_topics);
       END""",
    # Keep FTS in sync on DELETE
    """CREATE TRIGGER IF NOT EXISTS summaries_fts_ad
       AFTER DELETE ON summaries BEGIN
           INSERT INTO summaries_fts(summaries_fts, rowid, file_name, summary_short, summary_long, key_topics)
           VALUES ('delete', old.id, old.file_name, old.summary_short, old.summary_long, old.key_topics);
       END""",
    # Keep FTS in sync on UPDATE (remove old entry, add new)
    """CREATE TRIGGER IF NOT EXISTS summaries_fts_au
       AFTER UPDATE ON summaries BEGIN
           INSERT INTO summaries_fts(summaries_fts, rowid, file_name, summary_short, summary_long, key_topics)
           VALUES ('delete', old.id, old.file_name, old.summary_short, old.summary_long, old.key_topics);
           INSERT INTO summaries_fts(rowid, file_name, summary_short, summary_long, key_topics)
           VALUES (new.id, new.file_name, new.summary_short, new.summary_long, new.key_topics);
       END""",
]


async def init_db() -> None:
    async with engine.begin() as conn:
        # Create ORM tables
        await conn.run_sync(Base.metadata.create_all)

        # Non-destructive migrations for existing databases
        for col_sql, col_name in [
            ("ALTER TABLE summaries ADD COLUMN extracted_text TEXT", "extracted_text"),
            ("ALTER TABLE summaries ADD COLUMN is_starred BOOLEAN NOT NULL DEFAULT 0", "is_starred"),
        ]:
            try:
                await conn.execute(text(col_sql))
                logger.info("Migration: added %s column to summaries table", col_name)
            except Exception:
                pass  # Column already exists — expected on subsequent starts

        # Set up FTS5 virtual table and sync triggers
        for ddl in _FTS_DDL:
            await conn.execute(text(ddl))

        # Rebuild FTS index if it's out of sync (covers first run after migration)
        fts_count = (await conn.execute(text("SELECT COUNT(*) FROM summaries_fts"))).scalar_one()
        summaries_count = (await conn.execute(text("SELECT COUNT(*) FROM summaries"))).scalar_one()
        if fts_count != summaries_count:
            await conn.execute(text("INSERT INTO summaries_fts(summaries_fts) VALUES('rebuild')"))
            logger.info("FTS5: rebuilt index (%d → %d entries)", fts_count, summaries_count)
        else:
            logger.debug("FTS5: index up to date (%d entries)", fts_count)
