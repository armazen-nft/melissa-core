
"""
PDF extractor — texto nativo + OCR fallback (Tesseract).
Detecta automaticamente páginas escaneadas (< MIN_CHARS_PER_PAGE).
"""

from __future__ import annotations

import io
import logging
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

    def __init__(self, ocr_dpi: int = 300, ocr_lang: str = "eng+por",
                 max_pages: Optional[int] = None) -> None:
        self.ocr_dpi   = ocr_dpi
        self.ocr_lang  = ocr_lang
        self.max_pages = max_pages

    def extract(self, path: Path, consent: dict | None = None) -> IngestedDoc:
        path = Path(path)
        file_hash = sha256_file(path)
        log.info("Extracting PDF: %s  (hash=%s…)", path.name, file_hash[:8])

        pages_text, title, author, page_count = self._extract_pages(path)
        full_text = "\n\n".join(pages_text)
        flags     = ConsentFlags(**(consent or {}))
        lang      = self._detect_language(full_text)

        log.info("Extracted %d pages, %d chars, lang=%s", page_count, len(full_text), lang)
        return IngestedDoc(
            file_hash=file_hash, source_path=str(path.resolve()),
            source_type=SourceType.PDF, content=full_text, language=lang,
            page_count=page_count, title=title, author=author, consent=flags,
            extra_metadata={"pages": page_count, "ocr_dpi": self.ocr_dpi},
        )

    def _extract_pages(self, path: Path):
        try:
            from pdfminer.high_level import extract_pages
            from pdfminer.layout import LAParams, LTTextContainer
            from pypdf import PdfReader
        except ImportError as e:
            raise ImportError("pip install pdfminer.six pypdf") from e

        reader = PdfReader(str(path))
        meta   = reader.metadata or {}
        total  = len(reader.pages)
        limit  = min(total, self.max_pages) if self.max_pages else total
        pages_text: list[str] = []

        for page_num, page_layout in enumerate(
            extract_pages(str(path), laparams=LAParams()), start=1
        ):
            if page_num > limit:
                break
            chars = []
            for el in page_layout:
                if isinstance(el, LTTextContainer):
                    chars.append(el.get_text())
            native = "".join(chars).strip()
            if len(native) >= MIN_CHARS_PER_PAGE:
                pages_text.append(native)
            else:
                ocr = self._ocr_page(reader, page_num - 1)
                pages_text.append(ocr if ocr else native)

        return pages_text, meta.get("/Title"), meta.get("/Author"), limit

    def _ocr_page(self, reader, page_index: int) -> str:
        try:
            import pytesseract
            from pypdf import PdfWriter
        except ImportError:
            return ""
        try:
            writer = PdfWriter()
            writer.add_page(reader.pages[page_index])
            buf = io.BytesIO()
            writer.write(buf)
            buf.seek(0)
            from pdf2image import convert_from_bytes
            images = convert_from_bytes(buf.read(), dpi=self.ocr_dpi)
            if not images:
                return ""
            return pytesseract.image_to_string(images[0].convert("L"), lang=self.ocr_lang).strip()
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
