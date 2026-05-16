import logging
import logging.handlers
from pathlib import Path

from doc_summarizer.config import settings

_LOG_DIR = Path(__file__).parent.parent.parent / "logs"
_LOG_FILE = _LOG_DIR / "doc_summarizer.log"

_FMT = "%(asctime)s %(levelname)-8s %(name)s — %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"


def configure_logging() -> None:
    """Set up console + rotating file logging. Safe to call multiple times."""
    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    if root.handlers:
        return  # already configured

    root.setLevel(settings.log_level.upper())

    # Console handler
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(_FMT, datefmt=_DATE_FMT))
    root.addHandler(console)

    # Rotating file handler — 5 MB per file, keep 5 backups
    file_handler = logging.handlers.RotatingFileHandler(
        _LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter(_FMT, datefmt=_DATE_FMT))
    root.addHandler(file_handler)
