
"""
Semantic Boundary Chunker — divide IngestedDoc em Chunks
respeitando fronteiras de sentença, com overlap configurável.
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
    return max(1, int(len(text.split()) * 1.3))


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
        return re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-ž])", text)


@dataclass
class ChunkerConfig:
    target_tokens:    int = 1000
    overlap_tokens:   int = 100
    min_chunk_tokens: int = 50


class SemanticChunker:

    def __init__(self, config: ChunkerConfig | None = None) -> None:
        self.cfg = config or ChunkerConfig()

    def chunk(self, doc: IngestedDoc) -> list[Chunk]:
        sentences = _split_sentences(doc.content)
        raw = list(self._greedy_pack(sentences))
        raw = self._add_overlap(raw)
        raw = self._merge_orphans(raw)
        chunks, offset = [], 0
        for i, text in enumerate(raw):
            chunks.append(Chunk(
                id=chunk_id(doc.file_hash, i, text), text=text,
                token_count=_approx_token_count(text),
                source_doc_id=doc.file_hash, source_path=doc.source_path,
                source_type=doc.source_type, language=doc.language,
                position=ChunkPosition(doc_offset=offset),
                metadata={"title": doc.title, "author": doc.author, "chunk_index": i},
            ))
            offset += len(text)
        log.info("Chunked %s… → %d chunks", doc.file_hash[:8], len(chunks))
        return chunks

    def _greedy_pack(self, sentences: list[str]) -> Iterator[str]:
        current, cur_tok = [], 0
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            t = _approx_token_count(sent)
            if t >= self.cfg.target_tokens:
                if current:
                    yield " ".join(current)
                    current, cur_tok = [], 0
                yield sent
                continue
            if cur_tok + t > self.cfg.target_tokens and current:
                yield " ".join(current)
                current, cur_tok = [], 0
            current.append(sent)
            cur_tok += t
        if current:
            yield " ".join(current)

    def _add_overlap(self, chunks: list[str]) -> list[str]:
        if len(chunks) <= 1:
            return chunks
        result = [chunks[0]]
        tail_n = int(self.cfg.overlap_tokens / 1.3)
        for i in range(1, len(chunks)):
            overlap = " ".join(chunks[i - 1].split()[-tail_n:])
            result.append(overlap + " " + chunks[i])
        return result

    def _merge_orphans(self, chunks: list[str]) -> list[str]:
        result, pending = [], ""
        for chunk in chunks:
            combined = (pending + " " + chunk).strip() if pending else chunk
            if _approx_token_count(combined) < self.cfg.min_chunk_tokens:
                pending = combined
            else:
                result.append(combined)
                pending = ""
        if pending:
            if result:
                result[-1] += " " + pending
            else:
                result.append(pending)
        return result
