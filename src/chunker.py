"""Text chunking strategies.

Kept as its own module with a small interface (Chunker.split) so that
alternative strategies (semantic, sentence-aware, token-based, etc.) can be
swapped in later without touching ingestion or retrieval code.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Protocol

logger = logging.getLogger(__name__)

# Preferred split points, tried in order, from largest semantic unit to smallest.
_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


@dataclass(frozen=True)
class Chunk:
    """A single chunk of text, still tied to its source page."""

    filename: str
    page_number: int
    chunk_id: int
    text: str


class Chunker(Protocol):
    """Interface every chunking strategy must satisfy."""

    def split(self, text: str) -> List[str]:
        ...


class RecursiveCharacterChunker:
    """Splits text recursively on a hierarchy of separators.

    Attempts to break on paragraph, then line, then sentence, then word
    boundaries before falling back to a hard character split, so chunks stay
    as semantically coherent as possible within the size limit.
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        logger.info("Creating RecursiveCharacterChunker Object.")
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be >= 0 and less than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, text: str) -> List[str]:
        logger.info("Runnign RecursiveCharacterChunker.split()")
        text = text.strip()
        if not text:
            return []

        raw_chunks = self._split_recursive(text, _SEPARATORS)
        return self._merge_with_overlap(raw_chunks)

    def _split_recursive(self, text: str, separators: List[str]) -> List[str]:
        logger.info("running RecursiveCharacterChunker._split_recursive()")
        if len(text) <= self.chunk_size:
            return [text] if text else []

        if not separators:
            # No separators left: hard split by character count.
            return [text[i : i + self.chunk_size] for i in range(0, len(text), self.chunk_size)]

        separator, *remaining_separators = separators
        if separator == "":
            return [text[i : i + self.chunk_size] for i in range(0, len(text), self.chunk_size)]

        parts = text.split(separator) #split by first element in _SEPARATORS
        pieces: List[str] = []
        logger.info(parts)

        for part in parts:
            if not part:
                continue
            if len(part) > self.chunk_size:
                pieces.extend(self._split_recursive(part, remaining_separators))
            else:
                pieces.append(part)
        return pieces

    def _merge_with_overlap(self, pieces: List[str]) -> List[str]:
        """Greedily pack small pieces into chunk_size windows with overlap."""
        logger.info("Runnign RecursiveCharacterChunker._merge_with_overlap()")
        if not pieces:
            return []

        chunks: List[str] = []
        current = ""

        for piece in pieces:
            candidate = f"{current} {piece}".strip() if current else piece
            if len(candidate) <= self.chunk_size:
                current = candidate
                continue

            if current:
                chunks.append(current)
                current = self._overlap_tail(current) + " " + piece
                current = current.strip()
                # If a single piece is still too big even alone, hard-split it.
                if len(current) > self.chunk_size:
                    chunks.extend(self._hard_split(current))
                    current = ""
            else:
                chunks.extend(self._hard_split(piece))
                current = ""

        if current:
            chunks.append(current)

        return chunks

    def _overlap_tail(self, text: str) -> str:
        logger.info("Runnign RecursiveCharacterChunker._overlap_tail()")

        if self.chunk_overlap <= 0 or len(text) <= self.chunk_overlap:
            return text if self.chunk_overlap > 0 else ""
        return text[-self.chunk_overlap :]

    def _hard_split(self, text: str) -> List[str]:
        step = max(self.chunk_size - self.chunk_overlap, 1)
        return [text[i : i + self.chunk_size] for i in range(0, len(text), step)]


def build_chunks(filename: str, page_number: int, text: str, chunker: Chunker, start_id: int = 0) -> List[Chunk]:
    logger.info("Runnign RecursiveCharacterChunker.build_chunks()")
    """Chunk a single page's text into Chunk objects with sequential ids."""
    logger.info("building chunks with:")
    logger.info(text)
    
    #recursively create chuncks of data
    pieces = chunker.split(text)
    logger.info(pieces)

    #creates a list of chuncks from each piece of pieces
    chunks = [
        Chunk(filename=filename, page_number=page_number, chunk_id=start_id + i, text=piece)
        for i, piece in enumerate(pieces)
    ]

    for c in chunks:
        logger.info(c.filename)

    if chunks:
        logger.debug("Created %d chunk(s) for %s page %d", len(chunks), filename, page_number)
    return chunks
