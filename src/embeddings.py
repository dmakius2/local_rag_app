"""Local embedding generation via Sentence Transformers."""
from __future__ import annotations

import logging
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Wraps a local Sentence Transformers model behind a minimal interface.

    Only `embed_texts` / `embed_query` / `dimension` are exposed so the
    vector store and retriever never need to know which embedding backend
    is in use.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        logger.info("Creating EmbeddingService Object")
        self.model_name = model_name
        logger.info("Loading embedding model '%s'", model_name)
        try:
            self._model = SentenceTransformer(model_name)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to load embedding model '%s': %s", model_name, exc)
            raise
        if hasattr(self._model, "get_embedding_dimension"):
            self._dimension = self._model.get_embedding_dimension()
        else:
            self._dimension = self._model.get_sentence_embedding_dimension()
        logger.info("Embedding model loaded (dimension=%d)", self._dimension)

    @property
    def dimension(self) -> int:
        logger.info("Running EmbeddingService.dimension()")
        return self._dimension

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Embed a batch of texts, returning a (n, dimension) float32 array."""
        if not texts:
            return np.empty((0, self._dimension), dtype=np.float32)

        logger.info("Generating embeddings for %d chunk(s)", len(texts))
        embeddings = self._model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True,
        )

        for e in embeddings:
            print(e)

        return embeddings.astype(np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        """Embed a single query string, returning a (dimension,) float32 array."""
        embedding = self._model.encode(
            [query],
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        logger.info("Running EmbeddingService.embed_query()")
        return embedding[0].astype(np.float32)
