
"""Testes unitários — Fase 1."""

from __future__ import annotations
import numpy as np
import pytest

from src.ingestion.chunker import ChunkerConfig, SemanticChunker, _approx_token_count
from src.utils.models import IngestedDoc, SourceType


def _doc(text):
    return IngestedDoc(file_hash="testhash123", source_path="/tmp/t.pdf",
                       source_type=SourceType.PDF, content=text, language="en")


def test_chunker_basic():
    chunks = SemanticChunker(ChunkerConfig(target_tokens=100, overlap_tokens=10)).chunk(_doc("Hello. " * 200))
    assert len(chunks) >= 2
    for c in chunks:
        assert c.text.strip() and c.id and c.source_doc_id == "testhash123"


def test_chunker_short():
    assert len(SemanticChunker().chunk(_doc("Uma frase curta."))) == 1


def test_chunker_deterministic():
    chunker = SemanticChunker(ChunkerConfig(target_tokens=50))
    doc     = _doc("Frase um. Frase dois. Frase três. " * 50)
    assert [c.id for c in chunker.chunk(doc)] == [c.id for c in chunker.chunk(doc)]


def test_token_count():
    assert _approx_token_count("a b c d") == 5
    assert _approx_token_count("") == 1


from src.utils.hashing import sha256_text, chunk_id


def test_sha256():
    h = sha256_text("hello")
    assert len(h) == 64 and h == sha256_text("hello") and h != sha256_text("world")


def test_chunk_id():
    cid = chunk_id("src", 0, "texto")
    assert len(cid) == 16 and cid == chunk_id("src", 0, "texto")
    assert len({chunk_id("src", 0, "a"), chunk_id("src", 1, "a"), chunk_id("src", 0, "b")}) == 3


@pytest.mark.slow
def test_embedder_shape():
    from src.embedding.embedder import Embedder
    emb = Embedder(use_onnx=False)
    vec = emb.encode("teste")
    assert vec.ndim == 1 and vec.dtype == np.float32


@pytest.mark.slow
def test_embedder_normalized():
    from src.embedding.embedder import Embedder
    vec = Embedder(use_onnx=False, normalize=True).encode("teste")
    assert abs(np.linalg.norm(vec) - 1.0) < 1e-5


@pytest.mark.slow
def test_embedder_batch():
    from src.embedding.embedder import Embedder
    emb  = Embedder(use_onnx=False)
    vecs = emb.encode_batch(["a", "b", "c"])
    assert vecs.shape == (3, emb.dim)
