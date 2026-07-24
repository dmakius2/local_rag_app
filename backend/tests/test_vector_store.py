import numpy as np

from src.vector_store import ChunkMetadata, VectorStore


def _normalized_vector(seed: int, dimension: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    vec = rng.random(dimension).astype(np.float32)
    return vec / np.linalg.norm(vec)


def test_add_and_search_returns_most_similar_chunk():
    dimension = 8
    store = VectorStore(dimension=dimension)

    vec_a = _normalized_vector(1, dimension)
    vec_b = _normalized_vector(2, dimension)
    embeddings = np.stack([vec_a, vec_b])
    metadata = [
        ChunkMetadata(filename="a.pdf", page_number=1, chunk_id=0, chunk_text="chunk a"),
        ChunkMetadata(filename="b.pdf", page_number=1, chunk_id=0, chunk_text="chunk b"),
    ]

    store.add(embeddings, metadata)
    results = store.search(vec_a, top_k=1)

    assert len(results) == 1
    assert results[0].metadata.filename == "a.pdf"


def test_search_on_empty_store_returns_no_results():
    store = VectorStore(dimension=8)

    results = store.search(_normalized_vector(1, 8), top_k=5)

    assert results == []


def test_save_and_load_round_trip(tmp_path):
    dimension = 8
    store = VectorStore(dimension=dimension)
    embeddings = np.stack([_normalized_vector(1, dimension), _normalized_vector(2, dimension)])
    metadata = [
        ChunkMetadata(filename="doc.pdf", page_number=1, chunk_id=0, chunk_text="first chunk"),
        ChunkMetadata(filename="doc.pdf", page_number=2, chunk_id=1, chunk_text="second chunk"),
    ]
    store.add(embeddings, metadata)

    index_path = tmp_path / "index.faiss"
    metadata_path = tmp_path / "metadata.json"
    store.save(index_path, metadata_path)

    assert VectorStore.exists(index_path, metadata_path)

    loaded = VectorStore.load(index_path, metadata_path)

    assert len(loaded) == 2
    assert loaded.dimension == dimension
    results = loaded.search(embeddings[0], top_k=1)
    assert results[0].metadata.chunk_text == "first chunk"


def test_exists_is_false_when_files_missing(tmp_path):
    assert not VectorStore.exists(tmp_path / "index.faiss", tmp_path / "metadata.json")


def test_remove_by_filename_removes_only_matching_chunks():
    dimension = 8
    store = VectorStore(dimension=dimension)
    vec_a1 = _normalized_vector(1, dimension)
    vec_a2 = _normalized_vector(2, dimension)
    vec_b1 = _normalized_vector(3, dimension)
    embeddings = np.stack([vec_a1, vec_a2, vec_b1])
    metadata = [
        ChunkMetadata(filename="a.pdf", page_number=1, chunk_id=0, chunk_text="a chunk 1"),
        ChunkMetadata(filename="a.pdf", page_number=2, chunk_id=1, chunk_text="a chunk 2"),
        ChunkMetadata(filename="b.pdf", page_number=1, chunk_id=0, chunk_text="b chunk 1"),
    ]
    store.add(embeddings, metadata)

    removed = store.remove_by_filename("a.pdf")

    assert removed == 2
    assert len(store) == 1
    remaining = store.all_metadata()
    assert remaining == [metadata[2]]

    # The surviving vector must still be searchable and correctly matched.
    results = store.search(vec_b1, top_k=1)
    assert len(results) == 1
    assert results[0].metadata.filename == "b.pdf"


def test_remove_by_filename_returns_zero_when_not_found():
    dimension = 8
    store = VectorStore(dimension=dimension)
    embeddings = np.stack([_normalized_vector(1, dimension)])
    metadata = [ChunkMetadata(filename="a.pdf", page_number=1, chunk_id=0, chunk_text="a chunk")]
    store.add(embeddings, metadata)

    removed = store.remove_by_filename("does-not-exist.pdf")

    assert removed == 0
    assert len(store) == 1


def test_add_mismatched_lengths_raises_value_error():
    store = VectorStore(dimension=8)
    embeddings = np.stack([_normalized_vector(1, 8), _normalized_vector(2, 8)])
    metadata = [ChunkMetadata(filename="a.pdf", page_number=1, chunk_id=0, chunk_text="only one")]

    try:
        store.add(embeddings, metadata)
        assert False, "expected ValueError"
    except ValueError:
        pass
