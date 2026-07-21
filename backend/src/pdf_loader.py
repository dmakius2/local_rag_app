"""PDF discovery and text extraction using PyMuPDF."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PageContent:
    """Extracted text for a single page of a single document."""

    filename: str
    page_number: int  # 1-indexed
    text: str


class PDFLoader:
    """Discovers PDFs in a directory and extracts their text page by page."""

    def __init__(self, documents_dir: Path):
        logger.info("Creating PDFLoader Object.")
        self.documents_dir = documents_dir

    def discover_pdfs(self) -> List[Path]:
        """Return all PDF file paths found directly inside documents_dir."""
        logger.info("Running PDFLoader.discover_pdfs()")
        if not self.documents_dir.exists():
            logger.warning("Documents directory does not exist: %s", self.documents_dir)
            return []

        pdfs = sorted(self.documents_dir.glob("*.pdf"))
        logger.info("Discovered %d PDF(s) in %s", len(pdfs), self.documents_dir)
        for pdf in pdfs:
            logger.info("DOCUMENT:", pdf)

        return pdfs

    def load_all(self) -> Iterator[PageContent]:
        """Yield PageContent for every page of every discoverable PDF.

        Invalid or unreadable PDFs are logged and skipped rather than
        aborting the whole ingestion run.
        """
        logger.info("Running PDFLoader.load_all()")
        pdfs = self.discover_pdfs()
        if not pdfs:
            logger.warning("No PDF files found in %s", self.documents_dir)
            return

        for pdf_path in pdfs:
            yield from self._load_single(pdf_path)

    def _load_single(self, pdf_path: Path) -> Iterator[PageContent]:
        logger.info("Running PDFLoader._load_single() on: %s", pdf_path)
        try:
            with fitz.open(pdf_path) as doc:
                page_count = len(doc)
                for page_index in range(page_count):
                    #breakes down the pdf into pages
                    page = doc.load_page(page_index)
                    text = page.get_text().strip()
                    if not text:
                        continue
                    yield PageContent(
                        filename=pdf_path.name,
                        page_number=page_index + 1,
                        text=text,
                    )
            logger.info("Extracted text from %s (%d pages)", pdf_path.name, page_count)
        except Exception as exc:  # noqa: BLE001 - want to keep ingesting other PDFs
            logger.error("Failed to read PDF '%s': %s", pdf_path.name, exc)
