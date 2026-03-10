
"""Content hashing and deduplication utilities."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Union


def sha256_file(path: Union[str, Path]) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def chunk_id(source_hash: str, position: int, text: str) -> str:
    payload = f"{source_hash}:{position}:{text[:64]}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
