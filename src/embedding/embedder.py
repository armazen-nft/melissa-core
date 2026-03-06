"""
Embedder — local, CPU-only, ONNX INT8 quantized.

On first run with use_onnx=True, model is exported + quantized once and
saved to model_cache_dir. Subsequent runs load ONNX directly (~3x faster).

Priority lanes:
  HIGH   → interactive queries  (batch=1,  no wait)
  NORMAL → active ingest        (batch=16, 100ms window)
  LOW    → idle reindex         (batch=64, 500ms window)
"""

from __future__ import annotations

import asyncio
import enum
import time
from pathlib import Path
from typing import Optional

import numpy as np

from src.utils.logger import get_logger
from src.utils.models import Chunk, EmbeddedChunk

log = get_logger("embedding.embedder")

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
MULTILINGUAL_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class Priority(enum.IntEnum):
    HIGH = 0
    NORMAL = 1
    LOW = 2


class Embedder:
    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        use_onnx: bool = True,
        model_cache_dir: Path = Path("./.melissa_model_cache"),
        normalize: bool = True,
    ) -> None:
        self.model_name = model_name
        self.normalize = normalize
        self._model = None

        if use_onnx:
            self._model = self._load_or_build_onnx(model_name, model_cache_dir)
            self._encode_fn = self._encode_onnx
        else:
            self._model = self._load_st(model_name)
            self._encode_fn = self._encode_st

        log.info("Embedder ready: model=%s  onnx=%s", model_name, use_onnx)

    def encode(self, text: str) -> np.ndarray:
        return self.encode_batch([text])[0]

    def encode_batch(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.empty((0,), dtype=np.float32)
        vecs = self._encode_fn(texts)
        if self.normalize:
            norms = np.linalg.norm(vecs, axis=1, keepdims=True)
            vecs = vecs / np.maximum(norms, 1e-9)
        return vecs.astype(np.float32)

    @property
    def dim(self) -> int:
        return self.encode("probe").shape[0]

    def _load_or_build_onnx(self, model_name: str, cache_dir: Path):
        onnx_dir = cache_dir / model_name.replace("/", "_") / "onnx_int8"
        if onnx_dir.exists():
            log.info("Loading cached ONNX model from %s", onnx_dir)
            return self._load_onnx_model(onnx_dir)
        log.info("Exporting + quantizing ONNX model (one-time, ~1 min)…")
        onnx_dir.mkdir(parents=True, exist_ok=True)
        self._export_and_quantize(model_name, onnx_dir)
        return self._load_onnx_model(onnx_dir)

    @staticmethod
    def _export_and_quantize(model_name: str, out_dir: Path) -> None:
        try:
            from optimum.onnxruntime import ORTModelForFeatureExtraction, ORTQuantizer
            from optimum.onnxruntime.configuration import AutoQuantizationConfig
        except ImportError as e:
            raise ImportError("pip install 'optimum[onnxruntime]'") from e

        fp32_dir = out_dir.parent / "onnx_fp32"
        fp32_dir.mkdir(parents=True, exist_ok=True)
        model = ORTModelForFeatureExtraction.from_pretrained(model_name, export=True)
        model.save_pretrained(str(fp32_dir))

        quantizer = ORTQuantizer.from_pretrained(str(fp32_dir))
        qconfig = AutoQuantizationConfig.avx512_vnni(is_static=False, per_channel=False)
        quantizer.quantize(save_dir=str(out_dir), quantization_config=qconfig)
        log.info("ONNX INT8 model saved to %s", out_dir)

    @staticmethod
    def _load_onnx_model(onnx_dir: Path):
        try:
            from optimum.onnxruntime import ORTModelForFeatureExtraction
            return ORTModelForFeatureExtraction.from_pretrained(str(onnx_dir))
        except ImportError as e:
            raise ImportError("pip install optimum[onnxruntime]") from e

    def _encode_onnx(self, texts: list[str]) -> np.ndarray:
        try:
            from transformers import AutoTokenizer
        except ImportError as e:
            raise ImportError("pip install transformers") from e

        if not hasattr(self, "_tokenizer"):
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)

        import torch
        enc = self._tokenizer(texts, padding=True, truncation=True,
                              max_length=512, return_tensors="pt")
        with torch.no_grad():
            out = self._model(**enc)

        token_embs = out.last_hidden_state.numpy()
        mask = enc["attention_mask"].numpy()[..., None]
        vecs = (token_embs * mask).sum(axis=1) / mask.sum(axis=1)
        return vecs.astype(np.float32)

    @staticmethod
    def _load_st(model_name: str):
        try:
            from sentence_transformers import SentenceTransformer
            return SentenceTransformer(model_name)
        except ImportError as e:
            raise ImportError("pip install sentence-transformers") from e

    def _encode_st(self, texts: list[str]) -> np.ndarray:
        return self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False)


_LANE_CONFIG: dict[Priority, tuple[int, float]] = {
    Priority.HIGH: (1, 0.0),
    Priority.NORMAL: (16, 0.1),
    Priority.LOW: (64, 0.5),
}


class _BatchItem:
    __slots__ = ("text", "priority", "future")
    def __init__(self, text: str, priority: Priority, loop: asyncio.AbstractEventLoop):
        self.text = text
        self.priority = priority
        self.future: asyncio.Future = loop.create_future()


class AsyncEmbedder:
    """Async wrapper with priority-lane batching."""

    def __init__(self, embedder: Optional[Embedder] = None) -> None:
        self._emb = embedder or Embedder()
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._task = None
        self._running = False

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._worker())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def embed(self, text: str, priority: Priority = Priority.NORMAL) -> np.ndarray:
        loop = asyncio.get_event_loop()
        item = _BatchItem(text, priority, loop)
        await self._queue.put((priority.value, time.monotonic(), item))
        return await item.future

    async def embed_chunk(self, chunk: Chunk, priority: Priority = Priority.NORMAL) -> EmbeddedChunk:
        vec = await self.embed(chunk.text, priority)
        return EmbeddedChunk(
            **{f: getattr(chunk, f) for f in chunk.__dataclass_fields__},
            embedding=vec,
            embedding_model=self._emb.model_name,
        )

    async def _worker(self) -> None:
        while self._running:
            batch: list[_BatchItem] = []
            try:
                _, _, first = self._queue.get_nowait()
                batch.append(first)
                lane_size, window = _LANE_CONFIG[first.priority]
                deadline = time.monotonic() + window
                while len(batch) < lane_size:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        break
                    try:
                        _, _, item = await asyncio.wait_for(self._queue.get(), timeout=remaining)
                        batch.append(item)
                    except asyncio.TimeoutError:
                        break
            except asyncio.QueueEmpty:
                await asyncio.sleep(0.02)
                continue

            texts = [it.text for it in batch]
            try:
                vecs = await asyncio.get_event_loop().run_in_executor(
                    None, self._emb.encode_batch, texts
                )
                for item, vec in zip(batch, vecs):
                    item.future.set_result(vec)
            except Exception as exc:
                for item in batch:
                    if not item.future.done():
                        item.future.set_exception(exc)
