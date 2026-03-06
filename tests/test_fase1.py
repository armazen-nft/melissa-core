"""Unit tests — Fase 1 core modules."""

from __future__ import annotations

import numpy as np
import pytest

from src.ingestion.chunker import ChunkerConfig, SemanticChunker, _approx_token_count
from src.utils.hashing import chunk_id, sha256_text
from src.utils.models import IngestedDoc, SourceType


def _make_doc(text: str) -> IngestedDoc:
    return IngestedDoc(
        file_hash="test_hash_abc123",
        source_path="/tmp/test.pdf",
        source_type=SourceType.PDF,
        content=text,
        language="en",
    )


def test_chunker_basic():
    doc = _make_doc("Hello world. " * 200)
    chunker = SemanticChunker(ChunkerConfig(target_tokens=100, overlap_tokens=10))
    chunks = chunker.chunk(doc)
    assert len(chunks) >= 2
    for c in chunks:
        assert c.text.strip()
        assert c.id
        assert c.source_doc_id == "test_hash_abc123"


def test_chunker_short_doc():
    doc = _make_doc("A short document with just a few sentences.")
    chunker = SemanticChunker()
    chunks = chunker.chunk(doc)
    assert len(chunks) == 1


def test_chunker_deterministic():
    doc = _make_doc("Sentence one. Sentence two. Sentence three. " * 50)
    chunker = SemanticChunker(ChunkerConfig(target_tokens=50, overlap_tokens=10))
    assert [c.id for c in chunker.chunk(doc)] == [c.id for c in chunker.chunk(doc)]


def test_approx_token_count():
    assert _approx_token_count("hello world foo bar") == 5
    assert _approx_token_count("") == 1


def test_sha256_text():
    h = sha256_text("hello")
    assert len(h) == 64
    assert sha256_text("hello") == sha256_text("hello")
    assert sha256_text("hello") != sha256_text("world")


def test_chunk_id_stable():
    cid = chunk_id("sourcehash", 0, "some text here")
    assert len(cid) == 16
    assert chunk_id("sourcehash", 0, "some text here") == cid


def test_chunk_id_unique():
    a = chunk_id("hash", 0, "text a")
    b = chunk_id("hash", 1, "text a")
    c = chunk_id("hash", 0, "text b")
    assert len({a, b, c}) == 3


@pytest.mark.slow
def test_embedder_shape():
    from src.embedding.embedder import Embedder

    emb = Embedder(use_onnx=False)
    vec = emb.encode("test sentence")
    assert vec.ndim == 1
    assert vec.dtype == np.float32
    assert vec.shape[0] == emb.dim


@pytest.mark.slow
def test_embedder_normalize():
    from src.embedding.embedder import Embedder

    emb = Embedder(use_onnx=False, normalize=True)
    vec = emb.encode("test normalization")
    norm = np.linalg.norm(vec)
    assert abs(norm - 1.0) < 1e-5


@pytest.mark.slow
def test_embedder_batch():
    from src.embedding.embedder import Embedder

    emb = Embedder(use_onnx=False)
    texts = ["first", "second", "third"]
    vecs = emb.encode_batch(texts)
    assert vecs.shape == (3, emb.dim)
