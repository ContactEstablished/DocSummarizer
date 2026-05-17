import logging

from pypdf import PdfReader

logger = logging.getLogger(__name__)


def parse_pdf(file_path: str) -> str:
    """Extract text from a PDF. Falls back to OCR if pypdf returns blank text."""
    reader = PdfReader(file_path)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)

    if text.strip():
        return text

    # pypdf returned no text — attempt OCR fallback
    logger.info("pypdf returned blank text for %s, attempting OCR fallback", file_path)
    return _ocr_fallback(file_path)


def _ocr_fallback(file_path: str) -> str:
    """Use pdf2image + pytesseract to OCR a scanned PDF.
    Returns empty string if dependencies are not installed."""
    try:
        from pdf2image import convert_from_path
        import pytesseract
    except ImportError:
        logger.warning(
            "OCR dependencies not installed (pip install pdf2image pytesseract). "
            "Install them and ensure Tesseract is on PATH to enable OCR for image-only PDFs."
        )
        return ""

    try:
        images = convert_from_path(file_path, dpi=300)
        pages = []
        for i, img in enumerate(images):
            page_text = pytesseract.image_to_string(img)
            if page_text.strip():
                pages.append(page_text)
            logger.debug("OCR page %d: %d characters", i + 1, len(page_text))
        result = "\n".join(pages)
        logger.info("OCR extracted %d characters from %d pages", len(result), len(images))
        return result
    except Exception as exc:
        logger.warning("OCR failed for %s: %s", file_path, exc)
        return ""
