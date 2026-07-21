import pytest

from src.chunker import RecursiveCharacterChunker, build_chunks


def test_short_text_is_a_single_chunk():
    chunker = RecursiveCharacterChunker(chunk_size=500, chunk_overlap=100)
    result = chunker.split("This is a short piece of text.")

    assert len(result) == 1
    assert result[0] == "This is a short piece of text."


def test_empty_text_produces_no_chunks():
    chunker = RecursiveCharacterChunker(chunk_size=500, chunk_overlap=100)

    assert chunker.split("") == []
    assert chunker.split("   ") == []


def test_long_text_is_split_into_multiple_chunks_within_size_limit():
    chunker = RecursiveCharacterChunker(chunk_size=100, chunk_overlap=20)
    text = "".join(f"Sentence number {i} provides some content. " for i in range(20))

    chunks = chunker.split(text)

    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 100


def test_invalid_overlap_raises_value_error():
    with pytest.raises(ValueError):
        RecursiveCharacterChunker(chunk_size=100, chunk_overlap=100)

    with pytest.raises(ValueError):
        RecursiveCharacterChunker(chunk_size=100, chunk_overlap=-1)


def test_build_chunks_assigns_sequential_ids_and_metadata():
    chunker = RecursiveCharacterChunker(chunk_size=50, chunk_overlap=10)
    text = "Paragraph one is here. " * 10

    chunks = build_chunks("doc.pdf", 3, text, chunker, start_id=5)

    assert all(c.filename == "doc.pdf" for c in chunks)
    assert all(c.page_number == 3 for c in chunks)
    ids = [c.chunk_id for c in chunks]
    assert ids == list(range(5, 5 + len(chunks)))
