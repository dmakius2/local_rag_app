"""Interactive CLI for the local RAG application."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

# Allow running as `python src/main.py` from the project root.
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import Config, configure_logging
from src.llm import LLMConnectionError, LLMError, LLMModelNotFoundError
from src.rag import EmptyDocumentDirectoryError
from src.services.rag_service import RAGService

logger = logging.getLogger(__name__)

EXIT_COMMANDS = {"exit", "quit"}


def print_banner() -> None:
    print("=" * 60)
    print("Local RAG Application")
    print("Ask questions about the documents in your /documents folder.")
    print("Type 'exit' to quit.")
    print("=" * 60)


def print_answer(answer_text: str, sources) -> None:
    print("\nAnswer:")
    print(answer_text)
    if sources:
        seen = []
        for s in sources:
            label = f"{s.filename} (page {s.page_number})"
            if label not in seen:
                seen.append(label)
        print("\nSources:")
        for label in seen:
            print(f"  - {label}")
    print()

 
def run() -> int:
    config = Config.load()
    configure_logging(config.log_level)
    config.ensure_directories()

    logger.info("Starting Local RAG application")

    try:
        service = RAGService(config)
        service.initialize()
    except EmptyDocumentDirectoryError as exc:
        print(f"\nError: {exc}\n")
        return 1
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to initialize RAG pipeline: %s", exc)
        print(f"\nFailed to start the application: {exc}\n")
        return 1

    print_banner()

    while True:
        try:
            question = input("\nQuestion: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return 0

        if not question:
            continue
        if question.lower() in EXIT_COMMANDS:
            print("Goodbye.")
            return 0

        try:
            answer = service.chat(question)
            print_answer(answer.text, answer.sources)
        except LLMModelNotFoundError as exc:
            print(f"\nError: {exc}\n")
        except LLMConnectionError as exc:
            print(f"\nError: {exc}\n")
        except LLMError as exc:
            print(f"\nError: {exc}\n")
        except Exception as exc:  # noqa: BLE001
            logger.error("Unexpected error while answering question: %s", exc)
            print(f"\nAn unexpected error occurred: {exc}\n")


if __name__ == "__main__":
    sys.exit(run())
