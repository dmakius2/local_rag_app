"""Multi-format document discovery and text extraction.

Supports PDF (PyMuPDF), DOCX (python-docx), and plain text out of the box.
Legacy .doc files (the pre-2007 binary Word format) are discovered so they
show up as stored documents, but their text is not extracted — there is no
reliable pure-Python parser for that format. They are skipped with a log
message rather than failing the whole ingestion run.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List

import docx
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

# Extensions accepted for upload/storage. Only a subset are actually
# extracted into the index — see EXTRACTABLE_EXTENSIONS below.
SUPPORTED_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt"}
EXTRACTABLE_EXTENSIONS = {".pdf", ".docx", ".txt"}


@dataclass(frozen=True)
class PageContent:
    """Extracted text for a single page (or page-equivalent) of a document."""

    filename: str
    page_number: int  # 1-indexed
    text: str


class DocumentLoader:
    """Discovers documents in a directory and extracts their text."""

    def __init__(self, documents_dir: Path):
        logger.info("Creating DocumentLoader Object.")
        self.documents_dir = documents_dir

    def discover_documents(self) -> List[Path]:
        """Return all supported document paths found directly inside documents_dir."""
        logger.info("Running DocumentLoader.discover_documents()")
        if not self.documents_dir.exists():
            logger.warning("Documents directory does not exist: %s", self.documents_dir)
            return []

        paths = sorted(
            p for p in self.documents_dir.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
        )
        logger.info("Discovered %d document(s) in %s", len(paths), self.documents_dir)
        return paths

    def load_all(self) -> Iterator[PageContent]:
        """Yield PageContent for every extractable document in documents_dir.

        Invalid, unreadable, or unsupported (e.g. legacy .doc) documents are
        logged and skipped rather than aborting the whole ingestion run.
        """
        logger.info("Running DocumentLoader.load_all()")
        paths = self.discover_documents()
        if not paths:
            logger.warning("No documents found in %s", self.documents_dir)
            return

        for path in paths:
            yield from self._load_single(path)

    def _load_single(self, path: Path) -> Iterator[PageContent]:
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            yield from self._load_pdf(path)
        elif suffix == ".docx":
            yield from self._load_docx(path)
        elif suffix == ".txt":
            yield from self._load_txt(path)
        elif suffix == ".doc":
            logger.warning(
                "Skipping legacy .doc file '%s': unsupported format for text extraction. "
                "Convert it to .docx or PDF to make it searchable.",
                path.name,
            )
        else:
            logger.warning("Skipping unsupported file '%s'", path.name)

    def _load_pdf(self, path: Path) -> Iterator[PageContent]:
        logger.info("Running DocumentLoader._load_pdf() on: %s", path)
        try:
            with fitz.open(path) as doc:
                page_count = len(doc)
                for page_index in range(page_count):
                    page = doc.load_page(page_index)
                    text = page.get_text().strip()
                    if not text:
                        continue
                    yield PageContent(filename=path.name, page_number=page_index + 1, text=text)
            logger.info("Extracted text from %s (%d pages)", path.name, page_count)
        except Exception as exc:  # noqa: BLE001 - want to keep ingesting other documents
            logger.error("Failed to read PDF '%s': %s", path.name, exc)

    def _load_docx(self, path: Path) -> Iterator[PageContent]:
        logger.info("Running DocumentLoader._load_docx() on: %s", path)
        try:
            document = docx.Document(str(path))
            text = "\n".join(p.text for p in document.paragraphs if p.text.strip())
            if not text.strip():
                return
            yield PageContent(filename=path.name, page_number=1, text=text)
            logger.info("Extracted text from %s", path.name)
        except Exception as exc:  # noqa: BLE001 - want to keep ingesting other documents
            logger.error("Failed to read DOCX '%s': %s", path.name, exc)

    def _load_txt(self, path: Path) -> Iterator[PageContent]:
        logger.info("Running DocumentLoader._load_txt() on: %s", path)
        try:
            text = path.read_text(encoding="utf-8", errors="ignore").strip()
            if not text:
                return
            yield PageContent(filename=path.name, page_number=1, text=text)
            logger.info("Extracted text from %s", path.name)
        except Exception as exc:  # noqa: BLE001 - want to keep ingesting other documents
            logger.error("Failed to read TXT '%s': %s", path.name, exc)
