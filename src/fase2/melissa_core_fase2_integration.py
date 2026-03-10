"""Public integration entry point for Melissa Core Fase 2 memory tiers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import asyncio
from typing import Any, Awaitable, Callable, Dict, List, Sequence

from .melissa_core_fase2_memory_tiers import ColdTier, HotTier, MemoryTierSystem, SearchResult, WarmTier


EmbedderFn = Callable[[str], Awaitable[Sequence[float]]]


@dataclass(slots=True)
class Fase2Config:
    hot_capacity: int = 50_000
    hot_to_warm_hours: int = 24
    warm_to_cold_days: int = 30
    migration_interval_seconds: int = 60


class DeploymentRecipes:
    @staticmethod
    def production() -> Fase2Config:
        return Fase2Config(hot_capacity=50_000, hot_to_warm_hours=24, warm_to_cold_days=30)

    @staticmethod
    def development() -> Fase2Config:
        return Fase2Config(hot_capacity=5_000, hot_to_warm_hours=1, warm_to_cold_days=3)

    @staticmethod
    def memory_constrained() -> Fase2Config:
        return Fase2Config(hot_capacity=2_000, hot_to_warm_hours=6, warm_to_cold_days=14)

    @staticmethod
    def latency_optimized() -> Fase2Config:
        return Fase2Config(hot_capacity=100_000, hot_to_warm_hours=48, warm_to_cold_days=45)


class MelissaFase2Integrator:
    """Fase 1-compatible add/search API with tiered memory backend."""

    def __init__(self, embedder: EmbedderFn, config: Fase2Config | None = None):
        self.embedder = embedder
        self.config = config or Fase2Config()
        self.memory_tiers = MemoryTierSystem(
            hot_tier=HotTier(capacity=self.config.hot_capacity),
            warm_tier=WarmTier(),
            cold_tier=ColdTier(),
            hot_to_warm_after=timedelta(hours=self.config.hot_to_warm_hours),
            warm_to_cold_after=timedelta(days=self.config.warm_to_cold_days),
        )
        self._background_task: asyncio.Task | None = None
        self._shutdown = asyncio.Event()

    async def add(self, chunk_id: str, text: str) -> None:
        embedding = await self.embedder(text)
        await self.memory_tiers.add(chunk_id, text, embedding)

    async def search(self, query: str, k: int = 10) -> List[SearchResult]:
        embedding = await self.embedder(query)
        return await self.memory_tiers.search(query, embedding, k=k)

    async def migration_once(self) -> Dict[str, int]:
        return await self.memory_tiers.run_migration_cycle()

    async def start_background_migration(self) -> None:
        if self._background_task and not self._background_task.done():
            return
        self._shutdown.clear()
        self._background_task = asyncio.create_task(self._migration_loop())

    async def stop_background_migration(self) -> None:
        self._shutdown.set()
        if self._background_task:
            await self._background_task

    async def _migration_loop(self) -> None:
        while not self._shutdown.is_set():
            await self.memory_tiers.run_migration_cycle()
            try:
                await asyncio.wait_for(
                    self._shutdown.wait(),
                    timeout=self.config.migration_interval_seconds,
                )
            except asyncio.TimeoutError:
                continue
