from pathlib import Path

from doc_summarizer.core.parsers.docx_parser import parse_docx
from doc_summarizer.core.parsers.pdf_parser import parse_pdf
from doc_summarizer.core.parsers.text_parser import parse_text

_DISPATCH: dict[str, object] = {
    ".pdf": parse_pdf,
    ".docx": parse_docx,
    ".txt": parse_text,
    ".md": parse_text,
}


def parse_document(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    parser = _DISPATCH.get(ext)
    if parser is None:
        raise ValueError(f"Unsupported file type: {ext}")
    return parser(file_path)  # type: ignore[operator]
