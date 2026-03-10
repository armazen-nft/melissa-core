"""Compression engine and benchmark helpers for Melissa Fase 2."""

from __future__ import annotations

from dataclasses import dataclass
import statistics
import time
from typing import Dict, Iterable, List
import zlib


@dataclass(frozen=True)
class CompressionProfile:
    name: str
    level: int
    description: str


PROFILES = {
    "ultra-fast": CompressionProfile("ultra-fast", 1, "lowest latency"),
    "fast": CompressionProfile("fast", 3, "low latency + moderate ratio"),
    "balanced": CompressionProfile("balanced", 6, "default production profile"),
    "warm": CompressionProfile("warm", 10, "warm tier optimized ratio"),
    "max": CompressionProfile("max", 19, "cold archival max ratio"),
}


class ZstdCompressionEngine:
    """zlib-backed engine with zstd-like profile surface for portability."""

    def __init__(self, profile: str = "balanced"):
        if profile not in PROFILES:
            raise ValueError(f"unknown profile: {profile}")
        self.profile = PROFILES[profile]

    def compress(self, text: str) -> bytes:
        level = min(max(self.profile.level, 1), 9)
        return zlib.compress(text.encode("utf-8"), level=level)

    def decompress(self, payload: bytes) -> str:
        return zlib.decompress(payload).decode("utf-8")


@dataclass
class BenchmarkResult:
    profile: str
    input_bytes: int
    output_bytes: int
    ratio: float
    compress_ms: float
    decompress_ms: float


class CompressionBenchmarks:
    def __init__(self, samples: Iterable[str]):
        self.samples = list(samples)

    def run_profile(self, profile: str) -> BenchmarkResult:
        engine = ZstdCompressionEngine(profile)
        raw = "\n".join(self.samples)
        raw_bytes = len(raw.encode("utf-8"))

        t0 = time.perf_counter()
        payload = engine.compress(raw)
        t1 = time.perf_counter()
        decoded = engine.decompress(payload)
        t2 = time.perf_counter()

        if decoded != raw:
            raise RuntimeError("compression roundtrip mismatch")

        out_bytes = len(payload)
        ratio = raw_bytes / max(out_bytes, 1)
        return BenchmarkResult(
            profile=profile,
            input_bytes=raw_bytes,
            output_bytes=out_bytes,
            ratio=ratio,
            compress_ms=(t1 - t0) * 1000,
            decompress_ms=(t2 - t1) * 1000,
        )

    def run_all(self) -> List[BenchmarkResult]:
        return [self.run_profile(profile) for profile in PROFILES]


@dataclass
class TierMigrationSummary:
    warm_ratio: float
    cold_ratio: float
    promoted_to_warm: int
    promoted_to_cold: int


class TierMigrationSimulator:
    """Simple simulator to estimate tier footprint after migrations."""

    def __init__(self, entries: Iterable[str]):
        self.entries = list(entries)

    def simulate(self) -> TierMigrationSummary:
        warm_engine = ZstdCompressionEngine("warm")
        cold_engine = ZstdCompressionEngine("max")

        raw_sizes = [len(s.encode("utf-8")) for s in self.entries]
        warm_sizes = [len(warm_engine.compress(s)) for s in self.entries]
        cold_sizes = [len(cold_engine.compress(s)) for s in self.entries]

        warm_ratio = statistics.mean(raw_sizes) / max(statistics.mean(warm_sizes), 1)
        cold_ratio = statistics.mean(raw_sizes) / max(statistics.mean(cold_sizes), 1)

        return TierMigrationSummary(
            warm_ratio=warm_ratio,
            cold_ratio=cold_ratio,
            promoted_to_warm=len(self.entries),
            promoted_to_cold=len(self.entries),
        )
