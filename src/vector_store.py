"""FAISS-backed vector store with sidecar JSON metadata.

The index stores normalized embeddings and uses inner product search, which
is equivalent to cosine similarity for normalized vectors. Metadata (filename,
page number, chunk id, chunk text) is kept in a parallel JSON file, indexed
by the same position as its vector in the FAISS index.
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Tuple

import faiss
import numpy as np

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ChunkMetadata:
    """Metadata describing the origin of a single stored chunk."""

    filename: str
    page_number: int
    chunk_id: int
    chunk_text: str


@dataclass(frozen=True)
class SearchResult:
    """A single retrieved chunk with its similarity score."""

    metadata: ChunkMetadata
    score: float


class VectorStore:
    """Manages a FAISS index and its associated chunk metadata."""

    def __init__(self, dimension: int):
        logger.info("Creating VectorStore Object")
        self.dimension = dimension
        self._index = faiss.IndexFlatIP(dimension)
        self._metadata: List[ChunkMetadata] = []

    def __len__(self) -> int:
        return len(self._metadata)

    def all_metadata(self) -> List[ChunkMetadata]:
        """Return metadata for every chunk currently stored."""
        return list(self._metadata)

    def add(self, embeddings: np.ndarray, metadata: List[ChunkMetadata]) -> None:
        """Add a batch of embeddings and their corresponding metadata."""
        logger.info("Running VectorStore.add()")
        if embeddings.shape[0] != len(metadata):
            raise ValueError("embeddings and metadata must have the same length")
        if embeddings.shape[0] == 0:
            return

        self._index.add(embeddings)
        self._metadata.extend(metadata)
        logger.info("Added %d vector(s) to index (total=%d)", embeddings.shape[0], len(self._metadata))

    def search(self, query_embedding: np.ndarray, top_k: int) -> List[SearchResult]:
        """Return the top_k most similar chunks to the query embedding."""
        logger.info("Running VectorStore.search()")

        if len(self._metadata) == 0:
            logger.warning("Search attempted against an empty vector store")
            return []

        k = min(top_k, len(self._metadata))
        query = np.expand_dims(query_embedding, axis=0)
        scores, indices = self._index.search(query, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            results.append(SearchResult(metadata=self._metadata[idx], score=float(score)))

        logger.info("Retrieved %d chunk(s) for query", len(results))
        return results

    def save(self, index_path: Path, metadata_path: Path) -> None:
        """Persist the FAISS index and metadata to disk."""
        logger.info("Running VectorStore.save()")
        index_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)

        faiss.write_index(self._index, str(index_path))
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "dimension": self.dimension,
                    "chunks": [asdict(m) for m in self._metadata],
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        logger.info("Saved index (%d vectors) to %s and metadata to %s", len(self._metadata), index_path, metadata_path)

    @classmethod
    def load(cls, index_path: Path, metadata_path: Path) -> "VectorStore":
        logger.info("Runnign VectorStore.loads()")
        """Load a previously persisted FAISS index and its metadata."""
        if not index_path.exists() or not metadata_path.exists():
            raise FileNotFoundError(f"Missing index or metadata at {index_path} / {metadata_path}")

        with open(metadata_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        store = cls(dimension=payload["dimension"])
        store._index = faiss.read_index(str(index_path))
        store._metadata = [ChunkMetadata(**c) for c in payload["chunks"]]

        logger.info("Loaded index with %d vectors from %s", len(store._metadata), index_path)
        return store

    @staticmethod
    def exists(index_path: Path, metadata_path: Path) -> bool:
        logger.info("Runnign VectorStore.exists()")
        return index_path.exists() and metadata_path.exists()
