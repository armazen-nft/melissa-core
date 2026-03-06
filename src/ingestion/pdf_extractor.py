"""
PDF extractor — handles both native-text and scanned PDFs.

Strategy:
  1. Try pdfminer.six for text-native PDFs (fast, no deps).
  2. If a page yields < MIN_CHARS_PER_PAGE chars, fall back to
     Tesseract OCR on that page's rasterized image.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

from src.ingestion.base import BaseExtractor
from src.utils.hashing import sha256_file
from src.utils.logger import get_logger
from src.utils.models import ConsentFlags, IngestedDoc, SourceType

log = get_logger("ingestion.pdf")
MIN_CHARS_PER_PAGE = 50


class PDFExtractor(BaseExtractor):

    supported_extensions = [".pdf"]

    def __init__(
        self,
        ocr_dpi: int = 300,
        ocr_lang: str = "eng+por",
        max_pages: Optional[int] = None,
    ) -> None:
        self.ocr_dpi = ocr_dpi
        self.ocr_lang = ocr_lang
        self.max_pages = max_pages

    def extract(self, path: Path, consent: dict | None = None) -> IngestedDoc:
        path = Path(path)
        file_hash = sha256_file(path)
        log.info("Extracting PDF: %s  (hash=%s…)", path.name, file_hash[:8])

        pages_text, title, author, page_count = self._extract_pages(path)
        full_text = "\n\n".join(pages_text)
        flags = ConsentFlags(**(consent or {}))
        lang = self._detect_language(full_text)

        log.info("Extracted %d pages, %d chars, lang=%s", page_count, len(full_text), lang)

        return IngestedDoc(
            file_hash=file_hash,
            source_path=str(path.resolve()),
            source_type=SourceType.PDF,
            content=full_text,
            language=lang,
            page_count=page_count,
            title=title,
            author=author,
            consent=flags,
            extra_metadata={"pages": page_count, "ocr_dpi": self.ocr_dpi},
        )

    def _extract_pages(self, path: Path) -> tuple[list[str], str | None, str | None, int]:
        try:
            from pdfminer.high_level import extract_pages
            from pdfminer.layout import LAParams, LTTextContainer
            from pypdf import PdfReader
        except ImportError as e:
            raise ImportError("pip install pdfminer.six pypdf") from e

        reader = PdfReader(str(path))
        meta = reader.metadata or {}
        title = meta.get("/Title") or None
        author = meta.get("/Author") or None
        total = len(reader.pages)
        limit = min(total, self.max_pages) if self.max_pages else total

        pages_text: list[str] = []

        for page_num, page_layout in enumerate(extract_pages(str(path), laparams=LAParams()), start=1):
            if page_num > limit:
                break
            page_chars: list[str] = []
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    page_chars.append(element.get_text())
            native_text = "".join(page_chars).strip()

            if len(native_text) >= MIN_CHARS_PER_PAGE:
                pages_text.append(native_text)
            else:
                ocr_text = self._ocr_page(reader, page_num - 1)
                pages_text.append(ocr_text if ocr_text else native_text)
                if ocr_text:
                    log.debug("Page %d used OCR (%d chars)", page_num, len(ocr_text))

        return pages_text, title, author, limit

    def _ocr_page(self, reader, page_index: int) -> str:
        try:
            import pytesseract
            from pypdf import PdfWriter
        except ImportError:
            log.warning("pytesseract/Pillow not installed — skipping OCR page %d", page_index + 1)
            return ""
        try:
            writer = PdfWriter()
            writer.add_page(reader.pages[page_index])
            buf = io.BytesIO()
            writer.write(buf)
            buf.seek(0)
            try:
                from pdf2image import convert_from_bytes

                images = convert_from_bytes(buf.read(), dpi=self.ocr_dpi)
                if not images:
                    return ""
                img = images[0].convert("L")
            except ImportError:
                log.warning("pdf2image not installed — pip install pdf2image poppler-utils")
                return ""
            return pytesseract.image_to_string(img, lang=self.ocr_lang).strip()
        except Exception as e:
            log.warning("OCR failed page %d: %s", page_index + 1, e)
            return ""

    @staticmethod
    def _detect_language(text: str) -> str:
        try:
            from langdetect import detect

            return detect(text[:2000]) if text else "unknown"
        except Exception:
            return "unknown"
