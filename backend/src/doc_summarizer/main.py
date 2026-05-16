import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from doc_summarizer.api.routes import health, search, summaries
from doc_summarizer.config import settings
from doc_summarizer.db.session import init_db
from doc_summarizer.logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await init_db()
    logger.info("DocSummarizer API started")
    yield


app = FastAPI(
    title="DocSummarizer",
    description="AI-powered document summarization API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(summaries.router, prefix="/api/summaries")
app.include_router(search.router, prefix="/api")
