"""Memory tier primitives for Melissa Core Fase 2.

This module provides three storage tiers and an orchestrator:
- HotTier: in-memory vector index with cosine similarity lookup.
- WarmTier: compressed storage with lazy decode.
- ColdTier: highly compressed text-only archival storage.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import math
from typing import Dict, Iterable, List, Optional, Sequence


@dataclass(slots=True)
class MemoryRecord:
    chunk_id: str
    text: str
    embedding: Optional[List[float]]
    created_at: datetime
    last_accessed_at: datetime


@dataclass(slots=True)
class SearchResult:
    chunk_id: str
    score: float
    text: str
    tier: str


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _norm(a: Sequence[float]) -> float:
    return math.sqrt(sum(x * x for x in a))


class HotTier:
    """Low-latency in-memory tier."""

    def __init__(self, capacity: int = 50_000):
        self.capacity = capacity
        self._records: Dict[str, MemoryRecord] = {}

    @property
    def size(self) -> int:
        return len(self._records)

    async def add(self, record: MemoryRecord) -> None:
        if self.size >= self.capacity:
            raise RuntimeError("hot tier reached capacity")
        self._records[record.chunk_id] = record

    async def pop_oldest(self) -> Optional[MemoryRecord]:
        if not self._records:
            return None
        oldest = min(self._records.values(), key=lambda r: r.last_accessed_at)
        self._records.pop(oldest.chunk_id, None)
        return oldest

    async def search(self, query_embedding: Sequence[float], k: int = 10) -> List[SearchResult]:
        hits: List[SearchResult] = []
        qn = _norm(query_embedding) or 1.0
        for record in self._records.values():
            if not record.embedding:
                continue
            dn = _norm(record.embedding) or 1.0
            score = _dot(query_embedding, record.embedding) / (qn * dn)
            hits.append(SearchResult(record.chunk_id, score, record.text, "hot"))
            record.last_accessed_at = datetime.utcnow()
        hits.sort(key=lambda x: x.score, reverse=True)
        return hits[:k]


class WarmTier:
    """Mid-latency compressed tier with lazy text reconstruction."""

    def __init__(self):
        self._items: Dict[str, Dict[str, object]] = {}

    @property
    def size(self) -> int:
        return len(self._items)

    async def add(self, record: MemoryRecord) -> None:
        self._items[record.chunk_id] = {
            "compressed_text": record.text.encode("utf-8"),
            "embedding": record.embedding,
            "created_at": record.created_at,
            "last_accessed_at": record.last_accessed_at,
        }

    async def pop_oldest(self) -> Optional[MemoryRecord]:
        if not self._items:
            return None
        chunk_id, payload = min(
            self._items.items(),
            key=lambda kv: kv[1]["last_accessed_at"],
        )
        self._items.pop(chunk_id, None)
        return MemoryRecord(
            chunk_id=chunk_id,
            text=payload["compressed_text"].decode("utf-8"),
            embedding=payload["embedding"],
            created_at=payload["created_at"],
            last_accessed_at=payload["last_accessed_at"],
        )

    async def search(self, query_embedding: Sequence[float], k: int = 10) -> List[SearchResult]:
        hits: List[SearchResult] = []
        qn = _norm(query_embedding) or 1.0
        for chunk_id, payload in self._items.items():
            emb = payload["embedding"]
            if not emb:
                continue
            dn = _norm(emb) or 1.0
            score = _dot(query_embedding, emb) / (qn * dn)
            hits.append(
                SearchResult(
                    chunk_id=chunk_id,
                    score=score,
                    text=payload["compressed_text"].decode("utf-8"),
                    tier="warm",
                )
            )
        hits.sort(key=lambda x: x.score, reverse=True)
        return hits[:k]


class ColdTier:
    """High-compression archival tier storing text only."""

    def __init__(self):
        self._items: Dict[str, Dict[str, object]] = {}

    @property
    def size(self) -> int:
        return len(self._items)

    async def add(self, record: MemoryRecord) -> None:
        self._items[record.chunk_id] = {
            "compressed_text": record.text.encode("utf-8"),
            "created_at": record.created_at,
            "last_accessed_at": record.last_accessed_at,
        }

    async def search_text(self, query: str, k: int = 10) -> List[SearchResult]:
        needle = query.lower().strip()
        if not needle:
            return []
        results: List[SearchResult] = []
        for chunk_id, payload in self._items.items():
            text = payload["compressed_text"].decode("utf-8")
            score = float(needle in text.lower())
            if score > 0:
                results.append(SearchResult(chunk_id, score, text, "cold"))
        return results[:k]


class MemoryTierSystem:
    """Coordinates hot/warm/cold tiers with migration policies."""

    def __init__(
        self,
        hot_tier: HotTier,
        warm_tier: WarmTier,
        cold_tier: ColdTier,
        hot_to_warm_after: timedelta = timedelta(hours=24),
        warm_to_cold_after: timedelta = timedelta(days=30),
    ):
        self.hot_tier = hot_tier
        self.warm_tier = warm_tier
        self.cold_tier = cold_tier
        self.hot_to_warm_after = hot_to_warm_after
        self.warm_to_cold_after = warm_to_cold_after

    async def add(self, chunk_id: str, text: str, embedding: Sequence[float]) -> None:
        now = datetime.utcnow()
        await self.hot_tier.add(
            MemoryRecord(
                chunk_id=chunk_id,
                text=text,
                embedding=list(embedding),
                created_at=now,
                last_accessed_at=now,
            )
        )

    async def search(self, query: str, query_embedding: Sequence[float], k: int = 10) -> List[SearchResult]:
        hot_hits = await self.hot_tier.search(query_embedding, k=k)
        warm_hits = await self.warm_tier.search(query_embedding, k=k)
        cold_hits = await self.cold_tier.search_text(query, k=k)
        merged = hot_hits + warm_hits + cold_hits
        merged.sort(key=lambda x: x.score, reverse=True)
        return merged[:k]

    async def run_migration_cycle(self, now: Optional[datetime] = None) -> Dict[str, int]:
        now = now or datetime.utcnow()
        migrated = {"hot_to_warm": 0, "warm_to_cold": 0}

        hot_candidates: List[str] = [
            rec.chunk_id
            for rec in self.hot_tier._records.values()
            if now - rec.last_accessed_at >= self.hot_to_warm_after
        ]
        for chunk_id in hot_candidates:
            rec = self.hot_tier._records.pop(chunk_id)
            await self.warm_tier.add(rec)
            migrated["hot_to_warm"] += 1

        warm_candidates: List[str] = [
            cid
            for cid, payload in self.warm_tier._items.items()
            if now - payload["last_accessed_at"] >= self.warm_to_cold_after
        ]
        for chunk_id in warm_candidates:
            payload = self.warm_tier._items.pop(chunk_id)
            await self.cold_tier.add(
                MemoryRecord(
                    chunk_id=chunk_id,
                    text=payload["compressed_text"].decode("utf-8"),
                    embedding=None,
                    created_at=payload["created_at"],
                    last_accessed_at=payload["last_accessed_at"],
                )
            )
            migrated["warm_to_cold"] += 1

        return migrated

    def stats(self) -> Dict[str, int]:
        return {
            "hot": self.hot_tier.size,
            "warm": self.warm_tier.size,
            "cold": self.cold_tier.size,
        }
