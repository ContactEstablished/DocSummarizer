import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from doc_summarizer.api.routes import health, search, summaries
from doc_summarizer.config import settings
from doc_summarizer.db.session import init_db

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DocSummarizer",
    description="AI-powered document summarization API",
    version="0.1.0",
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


@app.on_event("startup")
async def on_startup() -> None:
    await init_db()
    logger.info("DocSummarizer API started")
