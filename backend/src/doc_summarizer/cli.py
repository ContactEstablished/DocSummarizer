import click
import uvicorn

from doc_summarizer.config import settings


@click.group()
def cli() -> None:
    """DocSummarizer — AI-powered document summarization tool."""


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
    target = folder or settings.watch_folder
    click.echo(f"Watching {target} for new documents...")
    # TODO: wire up watcher


@cli.command()
@click.argument("file_path")
def summarize(file_path: str) -> None:
    """Summarize a single FILE_PATH on demand."""
    click.echo(f"Summarizing {file_path}...")
    # TODO: wire up summarizer
