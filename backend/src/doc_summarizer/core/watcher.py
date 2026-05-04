import asyncio
import hashlib
import logging
from pathlib import Path

from watchdog.events import FileCreatedEvent, FileMovedEvent, FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def _hash_file(path: str) -> str:
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()


class DocumentHandler(FileSystemEventHandler):
    def __init__(self, callback: object) -> None:
        self._callback = callback

    def _handle(self, path: str) -> None:
        if Path(path).suffix.lower() in SUPPORTED_EXTENSIONS:
            logger.info("New document detected: %s", path)
            asyncio.run(self._callback(path))  # type: ignore[operator]

    def on_created(self, event: FileCreatedEvent) -> None:  # type: ignore[override]
        if not event.is_directory:
            self._handle(str(event.src_path))

    def on_moved(self, event: FileMovedEvent) -> None:  # type: ignore[override]
        if not event.is_directory:
            self._handle(str(event.dest_path))


def start_watcher(folder: str, callback: object) -> Observer:
    observer = Observer()
    observer.schedule(DocumentHandler(callback), folder, recursive=False)
    observer.start()
    logger.info("Watching %s", folder)
    return observer
