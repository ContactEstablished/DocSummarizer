import asyncio
import hashlib
import json
import logging
from pathlib import Path

import click
import uvicorn

from doc_summarizer.config import settings

logger = logging.getLogger(__name__)


@click.group()
@click.option("--log-level", default=settings.log_level, help="Logging level")
def cli(log_level: str) -> None:
    """DocSummarizer — AI-powered document summarization tool."""
    import os
    os.environ.setdefault("LOG_LEVEL", log_level.upper())
    from doc_summarizer.logging_config import configure_logging
    configure_logging()


@cli.command()
@click.option("--host", default=settings.api_host, help="Bind host")
@click.option("--port", default=settings.api_port, help="Bind port")
@click.option("--reload", is_flag=True, help="Enable hot reload (dev only)")
def serve(host: str, port: int, reload: bool) -> None:
    """Start the FastAPI server."""
    uvicorn.run("doc_summarizer.main:app", host=host, port=port, reload=reload)


@cli.command()
@click.argument("folder", default=None, required=False)
def watch(folder: str | None) -> None:
    """Start the file watcher on FOLDER (defaults to WATCH_FOLDER in .env)."""
    import time
    from doc_summarizer.core.watcher import start_watcher

    target = folder or settings.watch_folder
    Path(target).mkdir(parents=True, exist_ok=True)
    click.echo(f"Watching {target} for new documents. Press Ctrl+C to stop.")

    async def _process(file_path: str) -> None:
        from doc_summarizer.core.parser import parse_document
        from doc_summarizer.core.summarizer import summarize_document
        from doc_summarizer.db.models import Summary
        from doc_summarizer.db.repository import SummaryRepository
        from doc_summarizer.db.session import async_session_factory, init_db

        await init_db()
        ext = Path(file_path).suffix.lstrip(".").lower()
        size = Path(file_path).stat().st_size
        content_hash = _hash_file(file_path)

        async with async_session_factory() as session:
            repo = SummaryRepository(session)
            if await repo.get_by_hash(content_hash):
                click.echo(f"  [skip] {Path(file_path).name} — unchanged")
                return

            click.echo(f"  [parse] {Path(file_path).name}")
            text = parse_document(file_path)
            if not text.strip():
                click.echo(f"  [warn] No text extracted from {Path(file_path).name}")
                return

            click.echo(f"  [summarize] {Path(file_path).name}")
            result = summarize_document(text)

            summary = Summary(
                file_path=file_path,
                file_name=Path(file_path).name,
                file_type=ext,
                original_size_bytes=size,
                content_hash=content_hash,
                summary_short=result["summary_short"],
                summary_long=result["summary_long"],
                key_topics=json.dumps(result.get("key_topics", [])),
            )
            saved = await repo.create(summary)
            click.echo(f"  [done] Saved summary id={saved.id} for {saved.file_name}")

    def sync_callback(file_path: str) -> None:
        asyncio.run(_process(file_path))

    observer = start_watcher(target, sync_callback)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


@cli.command()
@click.argument("file_path")
@click.option("--save/--no-save", default=True, help="Persist summary to the database")
def summarize(file_path: str, save: bool) -> None:
    """Summarize a single FILE_PATH on demand."""
    asyncio.run(_summarize_async(file_path, save))


async def _summarize_async(file_path: str, save: bool) -> None:
    from doc_summarizer.core.parser import parse_document
    from doc_summarizer.core.summarizer import summarize_document
    from doc_summarizer.db.models import Summary
    from doc_summarizer.db.repository import SummaryRepository
    from doc_summarizer.db.session import async_session_factory, init_db

    path = Path(file_path)
    if not path.exists():
        click.echo(f"Error: file not found: {file_path}", err=True)
        raise SystemExit(1)

    ext = path.suffix.lstrip(".").lower()
    size = path.stat().st_size
    content_hash = _hash_file(file_path)

    click.echo(f"Parsing {path.name}…")
    text = parse_document(file_path)
    if not text.strip():
        click.echo("Error: no text could be extracted from this file.", err=True)
        raise SystemExit(1)

    click.echo("Summarizing with Claude…")
    result = summarize_document(text)

    click.echo("\n── Short Summary ─────────────────────────────────────")
    click.echo(result["summary_short"])
    click.echo("\n── Full Summary ──────────────────────────────────────")
    click.echo(result["summary_long"])
    click.echo("\n── Topics ────────────────────────────────────────────")
    click.echo(", ".join(result.get("key_topics", [])))

    if save:
        await init_db()
        async with async_session_factory() as session:
            repo = SummaryRepository(session)
            existing = await repo.get_by_hash(content_hash)
            if existing:
                click.echo(f"\nAlready in database as id={existing.id} — skipping save.")
                return
            summary = Summary(
                file_path=str(path.resolve()),
                file_name=path.name,
                file_type=ext,
                original_size_bytes=size,
                content_hash=content_hash,
                summary_short=result["summary_short"],
                summary_long=result["summary_long"],
                key_topics=json.dumps(result.get("key_topics", [])),
            )
            saved = await repo.create(summary)
            click.echo(f"\nSaved to database as id={saved.id}")


def _hash_file(path: str) -> str:
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()
