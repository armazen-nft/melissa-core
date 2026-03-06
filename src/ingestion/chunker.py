"""
Semantic Boundary Chunker
--------------------------
Splits an IngestedDoc into Chunks respecting sentence boundaries.
Never cuts mid-sentence. Adds configurable token overlap.

Strategy:
  1. Sentence-split with NLTK (offline, lightweight).
  2. Greedy-pack sentences until target_tokens exceeded.
  3. Add overlap: prepend tail of previous chunk.
  4. Merge orphan headers (< min_tokens) into successor.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterator

from src.utils.hashing import chunk_id
from src.utils.logger import get_logger
from src.utils.models import Chunk, ChunkPosition, IngestedDoc

log = get_logger("ingestion.chunker")


def _approx_token_count(text: str) -> int:
    words = len(text.split())
    return max(1, int(words * 1.3))


def _split_sentences(text: str) -> list[str]:
    try:
        import nltk

        try:
            return nltk.sent_tokenize(text)
        except LookupError:
            nltk.download("punkt", quiet=True)
            nltk.download("punkt_tab", quiet=True)
            return nltk.sent_tokenize(text)
    except ImportError:
        return re.split(r"(?<=[.!?])\s+(?=[A-Z\u00C0-\u017E])", text)


@dataclass
class ChunkerConfig:
    target_tokens: int = 1000
    overlap_tokens: int = 100
    min_chunk_tokens: int = 50


class SemanticChunker:

    def __init__(self, config: ChunkerConfig | None = None) -> None:
        self.cfg = config or ChunkerConfig()

    def chunk(self, doc: IngestedDoc) -> list[Chunk]:
        sentences = _split_sentences(doc.content)
        log.debug("Chunking doc %s…: %d sentences", doc.file_hash[:8], len(sentences))

        raw = list(self._greedy_pack(sentences))
        raw = self._add_overlap(raw)
        raw = self._merge_orphans(raw)

        chunks: list[Chunk] = []
        offset = 0
        for i, text in enumerate(raw):
            cid = chunk_id(doc.file_hash, i, text)
            chunks.append(
                Chunk(
                    id=cid,
                    text=text,
                    token_count=_approx_token_count(text),
                    source_doc_id=doc.file_hash,
                    source_path=doc.source_path,
                    source_type=doc.source_type,
                    language=doc.language,
                    position=ChunkPosition(doc_offset=offset),
                    metadata={"title": doc.title, "author": doc.author, "chunk_index": i},
                )
            )
            offset += len(text)

        log.info(
            "Chunked doc %s… into %d chunks (avg ~%d tokens)",
            doc.file_hash[:8],
            len(chunks),
            sum(c.token_count for c in chunks) // max(len(chunks), 1),
        )
        return chunks

    def _greedy_pack(self, sentences: list[str]) -> Iterator[str]:
        current: list[str] = []
        current_tokens = 0
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            t = _approx_token_count(sent)
            if t >= self.cfg.target_tokens:
                if current:
                    yield " ".join(current)
                    current, current_tokens = [], 0
                yield sent
                continue
            if current_tokens + t > self.cfg.target_tokens and current:
                yield " ".join(current)
                current, current_tokens = [], 0
            current.append(sent)
            current_tokens += t
        if current:
            yield " ".join(current)

    def _add_overlap(self, chunks: list[str]) -> list[str]:
        if len(chunks) <= 1:
            return chunks
        result = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_words = chunks[i - 1].split()
            tail_words = int(self.cfg.overlap_tokens / 1.3)
            overlap_text = " ".join(prev_words[-tail_words:])
            result.append(overlap_text + " " + chunks[i])
        return result

    def _merge_orphans(self, chunks: list[str]) -> list[str]:
        if not chunks:
            return chunks
        result: list[str] = []
        pending = ""
        for chunk in chunks:
            combined = (pending + " " + chunk).strip() if pending else chunk
            if _approx_token_count(combined) < self.cfg.min_chunk_tokens:
                pending = combined
            else:
                result.append(combined)
                pending = ""
        if pending:
            if result:
                result[-1] = result[-1] + " " + pending
            else:
                result.append(pending)
        return result
