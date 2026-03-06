"""Shared data models used across all modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

import numpy as np


class SourceType(str, Enum):
    PDF       = "pdf"
    IMAGE     = "image"
    AUDIO     = "audio"
    VIDEO     = "video"
    WEB       = "web"
    EPUB      = "epub"
    MARKDOWN  = "markdown"
    CODE      = "code"
    PLAINTEXT = "plaintext"


class MemoryTier(str, Enum):
    HOT  = "hot"
    WARM = "warm"
    COLD = "cold"


@dataclass
class ConsentFlags:
    index: bool = True
    redistribute: bool = False
    train_adapters: bool = True


@dataclass
class IngestedDoc:
    file_hash: str
    source_path: str
    source_type: SourceType
    content: str
    language: str
    ingested_at: datetime = field(default_factory=datetime.utcnow)
    page_count: Optional[int] = None
    title: Optional[str] = None
    author: Optional[str] = None
    consent: ConsentFlags = field(default_factory=ConsentFlags)
    extra_metadata: dict = field(default_factory=dict)


@dataclass
class ChunkPosition:
    doc_offset: int
    page: Optional[int] = None
    section: Optional[str] = None


@dataclass
class Chunk:
    id: str
    text: str
    token_count: int
    source_doc_id: str
    source_path: str
    source_type: SourceType
    language: str
    position: ChunkPosition
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)


@dataclass
class EmbeddedChunk(Chunk):
    embedding: Optional[np.ndarray] = None
    embedding_model: str = ""
    embedded_at: datetime = field(default_factory=datetime.utcnow)
    tier: MemoryTier = MemoryTier.HOT
