"""LLM service abstraction.

The RAG pipeline depends only on the `LLMService` interface below. Ollama is
today's implementation; future providers (OpenAI, Claude, Gemini, other local
models) can be added as additional classes implementing the same interface
without touching rag.py.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import requests

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Base class for all LLM service errors."""


class LLMConnectionError(LLMError):
    """Raised when the LLM backend cannot be reached."""


class LLMModelNotFoundError(LLMError):
    """Raised when the requested model is not available on the backend."""


class LLMService(ABC):
    """Interface every LLM provider must implement."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a completion for the given prompt."""
        raise NotImplementedError


class OllamaLLMService(LLMService):
    """LLM service backed by a local Ollama server's HTTP API."""

    def __init__(self, model: str = "llama3.2", base_url: str = "http://localhost:11434", timeout: int = 120):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        logger.info("Creating OllamaLLMService Object")


    def generate(self, prompt: str) -> str:
        logger.info("Creating OllamaLLMService.generate()")
        url = f"{self.base_url}/api/generate"
        payload = {"model": self.model, "prompt": prompt, "stream": False}

        logger.info("Sending request to Ollama (model=%s)", self.model)
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
        except requests.exceptions.ConnectionError as exc:
            raise LLMConnectionError(
                f"Could not connect to Ollama at {self.base_url}. "
                "Is Ollama installed and running? Try `ollama serve`."
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise LLMConnectionError(
                f"Ollama request timed out after {self.timeout}s."
            ) from exc

        if response.status_code == 404:
            raise LLMModelNotFoundError(
                f"Model '{self.model}' was not found on the Ollama server. "
                f"Try `ollama pull {self.model}`."
            )

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            raise LLMError(f"Ollama returned an error: {exc}") from exc

        data = response.json()
        answer = data.get("response", "").strip()
        logger.info("Received response from Ollama (%d chars)", len(answer))
        return answer
