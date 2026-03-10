
"""
VectorStore — FAISS local + SQLite metadata.
Auto-migra de IndexFlatL2 para IVF+PQ ao ultrapassar 1.000 chunks.
"""

from __future__ import annotations

import json
import pickle
from dataclasses import asdict
from pathlib import Path
from typing import Optional

import numpy as np

from src.utils.logger import get_logger
from src.utils.models import EmbeddedChunk

log = get_logger("embedding.vector_store")
FLAT_THRESHOLD = 1_000
DEFAULT_NPROBE = 10


class VectorStore:

    def __init__(self, data_dir: Path = Path("./data/hot"), dim: int = 384,
                 index_type: Optional[str] = None, nprobe: int = DEFAULT_NPROBE) -> None:
        self.data_dir   = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.dim        = dim
        self.index_type = index_type
        self.nprobe     = nprobe
        self._index_path  = self.data_dir / "faiss.index"
        self._meta_path   = self.data_dir / "meta.sqlite"
        self._hash_path   = self.data_dir / "file_hashes.json"
        self._id_map_path = self.data_dir / "id_map.pkl"
        self._index       = None
        self._id_map: list[str] = []
        self._file_hashes: set[str] = set()
        self._meta_db     = None
        self._load()

    def add(self, chunks: list[EmbeddedChunk]) -> int:
        new = [c for c in chunks if c.id not in self._id_map]
        if not new: return 0
        vecs = np.stack([c.embedding for c in new]).astype(np.float32)
        self._ensure_index(len(self._id_map) + len(new), vecs)
        if hasattr(self._index, "is_trained") and not self._index.is_trained:
            self._index.train(vecs)
        self._index.add(vecs)
        db = self._get_meta_db()
        for c in new:
            self._id_map.append(c.id)
            doc = asdict(c); doc.pop("embedding", None)
            db[c.id] = json.dumps(doc, default=str)
        db.commit(); self._save()
        log.info("Added %d chunks (total=%d)", len(new), len(self._id_map))
        return len(new)

    def search(self, query_vector: np.ndarray, top_k: int = 20) -> list[dict]:
        if self._index is None or not self._id_map: return []
        if hasattr(self._index, "nprobe"): self._index.nprobe = self.nprobe
        q = query_vector.reshape(1, -1).astype(np.float32)
        distances, indices = self._index.search(q, min(top_k, len(self._id_map)))
        db = self._get_meta_db()
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self._id_map): continue
            raw = db.get(self._id_map[idx])
            if raw is None: continue
            meta = json.loads(raw); meta["score"] = float(dist)
            results.append(meta)
        return results

    def register_file(self, file_hash: str) -> None:
        self._file_hashes.add(file_hash); self._save_hashes()

    def file_indexed(self, file_hash: str) -> bool:
        return file_hash in self._file_hashes

    def chunk_count(self) -> int:
        return len(self._id_map)

    def _ensure_index(self, total_after: int, vecs: np.ndarray) -> None:
        import faiss
        if self._index is None:
            if total_after < FLAT_THRESHOLD or self.index_type == "Flat":
                self._index = faiss.IndexFlatL2(self.dim)
            else:
                itype = self.index_type or "IVF256,PQ32"
                self._index = faiss.index_factory(self.dim, itype, faiss.METRIC_L2)
        elif isinstance(self._index, faiss.IndexFlatL2) and total_after >= FLAT_THRESHOLD:
            itype = self.index_type or "IVF256,PQ32"
            new   = faiss.index_factory(self.dim, itype, faiss.METRIC_L2)
            if self._id_map:
                old = self._index.reconstruct_n(0, len(self._id_map))
                new.train(old); new.add(old)
            self._index = new

    def _get_meta_db(self):
        if self._meta_db is None:
            from sqlitedict import SqliteDict
            self._meta_db = SqliteDict(str(self._meta_path), autocommit=False)
        return self._meta_db

    def _save(self) -> None:
        import faiss
        if self._index is not None: faiss.write_index(self._index, str(self._index_path))
        with open(self._id_map_path, "wb") as f: pickle.dump(self._id_map, f)
        self._save_hashes()

    def _load(self) -> None:
        import faiss
        if self._index_path.exists():
            self._index = faiss.read_index(str(self._index_path))
        if self._id_map_path.exists():
            with open(self._id_map_path, "rb") as f: self._id_map = pickle.load(f)
        if self._hash_path.exists():
            with open(self._hash_path) as f: self._file_hashes = set(json.load(f))

    def _save_hashes(self) -> None:
        with open(self._hash_path, "w") as f: json.dump(list(self._file_hashes), f)
