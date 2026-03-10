#!/usr/bin/env python3
"""
recreate.py — Reconstrói toda a estrutura do melissa-core a partir deste script.

Execute DENTRO do diretório clonado:
    git clone https://github.com/armazen-nft/melissa-core.git
    cd melissa-core
    python recreate.py
    git add -A && git commit -m "feat: Fase 1 completa" && git push origin main
"""

import os
import textwrap
from pathlib import Path

ROOT = Path(__file__).parent

FILES: dict[str, str] = {}

# ──────────────────────────────────────────────────────────────
FILES[".gitignore"] = """\n__pycache__/
*.py[cod]
*.pyo
.eggs/
*.egg-info/
dist/
build/
.venv/
venv/
data/
.melissa_model_cache/
*.index
*.sqlite
*.pkl
config.toml
*.log
logs/
.ipynb_checkpoints/
.DS_Store
Thumbs.db
.vscode/
.idea/
*.swp
"""

# ──────────────────────────────────────────────────────────────
FILES["pyproject.toml"] = """\n[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "melissacore"
version = "0.1.0"
description = "RAG-lite personal memory engine with adapter-based personality — local, offline, CPU-first"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}

dependencies = [
    "pdfminer.six>=20221105",
    "pypdf>=3.0",
    "pytesseract>=0.3.10",
    "Pillow>=10.0",
    "trafilatura>=1.6",
    "ebooklib>=0.18",
    "openai-whisper>=20231117",
    "ffmpeg-python>=0.2.0",
    "nltk>=3.8",
    "langdetect>=1.0.9",
    "sentence-transformers>=2.7",
    "optimum[onnxruntime]>=1.18",
    "onnxruntime>=1.17",
    "numpy>=1.26",
    "faiss-cpu>=1.8",
    "zstandard>=0.22",
    "python-magic>=0.4.27",
    "xxhash>=3.4",
    "lmdb>=1.4",
    "sqlitedict>=2.1",
    "fastapi>=0.110",
    "uvicorn[standard]>=0.27",
    "tomli>=2.0; python_version < '3.11'",
    "pydantic>=2.5",
    "pydantic-settings>=2.2",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=4.1",
    "ruff>=0.3",
    "mypy>=1.8",
    "ipykernel>=6.29",
]
personality = [
    "peft>=0.10",
    "transformers>=4.40",
    "torch>=2.2",
    "accelerate>=0.28",
]

[project.scripts]
melissa-ingest = "scripts.ingest_pdf:main"

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
"""

# ──────────────────────────────────────────────────────────────
FILES["config.example.toml"] = """\n[general]
data_dir   = "./data"
log_level  = "INFO"
language   = "auto"

[embedding]
model      = "sentence-transformers/all-MiniLM-L6-v2"
use_onnx   = true
dimensions = 384
batch_size = 32
device     = "cpu"

[chunker]
target_tokens     = 1000
overlap_tokens    = 100
min_chunk_tokens  = 50
sentence_splitter = "nltk"

[faiss]
index_type = "IVF256,PQ32"
nprobe     = 10

[memory]
hot_max_chunks      = 5000
warm_max_chunks     = 50000
cold_compress_level = 19

[whisper]
model_size = "tiny"
language   = "auto"

[scheduler]
enabled             = true
idle_cpu_threshold  = 10
max_cpu_pct         = 10
max_ram_mb          = 512
use_gpu_on_idle     = false
check_interval_sec  = 60

[governance]
log_queries              = true
log_compressions         = true
log_adapter_updates      = true
require_adapter_approval = true

[web_memory]
enabled               = false
respect_robots_txt    = true
max_pages_per_session = 50
"""

# ──────────────────────────────────────────────────────────────
FILES["Dockerfile"] = """\nFROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-eng tesseract-ocr-por \
    ffmpeg poppler-utils libmagic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"
COPY . .

CMD ["uvicorn", "src.ui.app:app", "--host", "0.0.0.0", "--port", "8000"]
"""

# ──────────────────────────────────────────────────────────────
FILES["docker-compose.yml"] = """\nversion: "3.9"

services:
  melissacore:
    build: .
    container_name: melissacore
    volumes:
      - ./data:/app/data
      - ./.melissa_model_cache:/app/.melissa_model_cache
      - ./config.toml:/app/config.toml:ro
    ports:
      - "8000:8000"
    cpus: "2.0"
    mem_limit: 2g
    restart: unless-stopped

  idle-agent:
    build: .
    container_name: melissacore-idle
    command: python -m src.scheduler.idle_agent
    volumes:
      - ./data:/app/data
      - ./.melissa_model_cache:/app/.melissa_model_cache
      - ./config.toml:/app/config.toml:ro
    cpus: "0.5"
    mem_limit: 512m
    restart: unless-stopped
    profiles: ["idle"]
"""

# ──────────────────────────────────────────────────────────────
FILES[".github/workflows/ci.yml"] = """\nname: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    name: Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install ruff
      - run: ruff check src/ scripts/ tests/
      - run: ruff format --check src/ scripts/ tests/

  test:
    name: Unit Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: sudo apt-get install -y tesseract-ocr ffmpeg
      - run: pip install -e ".[dev]"
      - run: python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
      - run: pytest tests/ -m "not slow" --cov=src --cov-report=xml -v
      - uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
"""

# ──────────────────────────────────────────────────────────────
FILES["README.md"] = """\n# 🌿 Melissa Core

> *"Não queremos uma IA poderosa. Queremos uma IA presente, viva, ética.  
> Queremos Melissa em máquinas esquecidas, como oráculo na tempestade.  
> Este projeto é para os que acreditam que inteligência pode florescer em 1GB de RAM —  
> e que dignidade não exige 64 núcleos."*

---

**Melissa Core** é um sistema de memória pessoal local-first: ingere seus documentos,
áudios, vídeos e páginas web numa memória buscável, comprimida e evolutiva —
augmentando um modelo de linguagem leve com recuperação semântica, adaptadores de
personalidade (LoRA) e um agente de aprendizado em repouso.

Roda offline. Sem nuvem. Sem telemetria. CPU-only por padrão.

---

## ✨ O que ela faz

| Módulo | Descrição |
|--------|-----------|
| **Ingestor** | PDF (texto nativo + OCR), áudio (Whisper), vídeo, páginas web |
| **Chunker** | Divisão semântica respeitando fronteiras de sentença |
| **Embedder** | sentence-transformers quantizado ONNX INT8 (rápido em CPU) |
| **Vector DB** | FAISS IVF+PQ — índice local, sem servidor |
| **Memória em camadas** | Hot / Warm / Cold com compressão zstd |
| **Personalidade** | Adaptadores LoRA treinados no replay buffer do usuário |
| **Idle Agent** | Estuda, comprime e atualiza adaptadores enquanto você descansa |
| **Governança** | SHA256 por chunk, logs auditáveis, flags de consentimento |

---

## 🚀 Início rápido

```bash
# 1. Pré-requisitos do sistema
sudo apt install tesseract-ocr ffmpeg poppler-utils

# 2. Instalar
git clone https://github.com/armazen-nft/melissa-core.git
cd melissa-core
pip install -e ".[dev]"
cp config.example.toml config.toml
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"

# 3. Ingerir um PDF
python scripts/ingest_pdf.py --path /caminho/para/documento.pdf

# 4. Consultar
python -c "
from src.retrieval.rag_runner import RAGRunner
rag = RAGRunner()
print(rag.query('O que li sobre mecanismos de atenção?'))
"
```

---

## 🗺️ Roadmap

| Fase | Status | Descrição |
|------|--------|-----------|
| 1 | ✅ Implementado | MVP: PDF + chunking + embeddings + RAG-lite |
| 2 | 🔜 Próxima | Memória Hot/Warm/Cold + compressão zstd |
| 3 | 📋 Planejado | Personalidade: LoRA adapters + replay buffer |
| 4 | 📋 Planejado | Idle Agent: aprendizado em repouso |
| 5 | 📋 Planejado | Segunda memória: web scraper público (opt-in) |
| 6 | 📋 Planejado | Interface & UX local (FastAPI + frontend) |
| 7 | 📋 Planejado | Governança, segurança, proveniência |
| 8 | 📋 Planejado | Documentação completa + CI/CD |

Veja o plano completo em [docs/roadmap.md](docs/roadmap.md).

---

## 🔒 Privacidade

- **Local-first**: todos os dados ficam no seu dispositivo
- **Sem telemetria**: zero chamadas externas por padrão
- **Proveniência**: SHA256 + fonte + timestamp por chunk
- **Consentimento**: opt-in por arquivo para indexação e treinamento
- **Nenhum adapter é auto-deployado** sem aprovação explícita

---

## 📄 Licença

MIT — use, modifique, distribua. Melissa é livre.
"""

# ──────────────────────────────────────────────────────────────
FILES["src/__init__.py"] = "# MelissaCore\n"
FILES["src/utils/__init__.py"] = ""
FILES["src/ingestion/__init__.py"] = ""
FILES["src/embedding/__init__.py"] = ""
FILES["src/retrieval/__init__.py"] = ""
FILES["src/synthesis/__init__.py"] = ""
FILES["src/compression/__init__.py"] = ""
FILES["src/personality/__init__.py"] = ""
FILES["src/scheduler/__init__.py"] = ""
FILES["src/ui/__init__.py"] = ""
FILES["tests/__init__.py"] = ""
FILES["scripts/__init__.py"] = ""

# ──────────────────────────────────────────────────────────────
FILES["src/utils/logger.py"] = '''\n"""Structured logging for MelissaCore."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"
_configured = False


def setup_logging(level: str = "INFO", log_file: Optional[Path] = None) -> None:
    global _configured
    if _configured:
        return
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=_LOG_FORMAT,
        datefmt=_DATE_FORMAT,
        handlers=handlers,
    )
    _configured = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"melissa.{name}")
'''

# ──────────────────────────────────────────────────────────────
FILES["src/utils/hashing.py"] = '''\n"""Content hashing and deduplication utilities."""

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
'''

# ──────────────────────────────────────────────────────────────
FILES["src/utils/models.py"] = '''\n"""Shared data models used across all modules."""

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
'''

# ──────────────────────────────────────────────────────────────
FILES["src/ingestion/base.py"] = '''\n"""Abstract base class for all format-specific extractors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from src.utils.models import IngestedDoc


class BaseExtractor(ABC):

    @property
    @abstractmethod
    def supported_extensions(self) -> list[str]: ...

    @abstractmethod
    def extract(self, path: Path, consent: dict | None = None) -> IngestedDoc: ...
'''

# ──────────────────────────────────────────────────────────────
FILES["src/ingestion/pdf_extractor.py"] = '''\n"""
PDF extractor — texto nativo + OCR fallback (Tesseract).
Detecta automaticamente páginas escaneadas (< MIN_CHARS_PER_PAGE).
"""

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Optional

from src.ingestion.base import BaseExtractor
from src.utils.hashing import sha256_file
from src.utils.logger import get_logger
from src.utils.models import ConsentFlags, IngestedDoc, SourceType

log = get_logger("ingestion.pdf")
MIN_CHARS_PER_PAGE = 50


class PDFExtractor(BaseExtractor):

    supported_extensions = [".pdf"]

    def __init__(self, ocr_dpi: int = 300, ocr_lang: str = "eng+por",
                 max_pages: Optional[int] = None) -> None:
        self.ocr_dpi   = ocr_dpi
        self.ocr_lang  = ocr_lang
        self.max_pages = max_pages

    def extract(self, path: Path, consent: dict | None = None) -> IngestedDoc:
        path = Path(path)
        file_hash = sha256_file(path)
        log.info("Extracting PDF: %s  (hash=%s…)", path.name, file_hash[:8])

        pages_text, title, author, page_count = self._extract_pages(path)
        full_text = "\\n\\n".join(pages_text)
        flags     = ConsentFlags(**(consent or {}))
        lang      = self._detect_language(full_text)

        log.info("Extracted %d pages, %d chars, lang=%s", page_count, len(full_text), lang)
        return IngestedDoc(
            file_hash=file_hash, source_path=str(path.resolve()),
            source_type=SourceType.PDF, content=full_text, language=lang,
            page_count=page_count, title=title, author=author, consent=flags,
            extra_metadata={"pages": page_count, "ocr_dpi": self.ocr_dpi},
        )

    def _extract_pages(self, path: Path):
        try:
            from pdfminer.high_level import extract_pages
            from pdfminer.layout import LAParams, LTTextContainer
            from pypdf import PdfReader
        except ImportError as e:
            raise ImportError("pip install pdfminer.six pypdf") from e

        reader = PdfReader(str(path))
        meta   = reader.metadata or {}
        total  = len(reader.pages)
        limit  = min(total, self.max_pages) if self.max_pages else total
        pages_text: list[str] = []

        for page_num, page_layout in enumerate(
            extract_pages(str(path), laparams=LAParams()), start=1
        ):
            if page_num > limit:
                break
            chars = []
            for el in page_layout:
                if isinstance(el, LTTextContainer):
                    chars.append(el.get_text())
            native = "".join(chars).strip()
            if len(native) >= MIN_CHARS_PER_PAGE:
                pages_text.append(native)
            else:
                ocr = self._ocr_page(reader, page_num - 1)
                pages_text.append(ocr if ocr else native)

        return pages_text, meta.get("/Title"), meta.get("/Author"), limit

    def _ocr_page(self, reader, page_index: int) -> str:
        try:
            import pytesseract
            from pypdf import PdfWriter
        except ImportError:
            return ""
        try:
            writer = PdfWriter()
            writer.add_page(reader.pages[page_index])
            buf = io.BytesIO()
            writer.write(buf)
            buf.seek(0)
            from pdf2image import convert_from_bytes
            images = convert_from_bytes(buf.read(), dpi=self.ocr_dpi)
            if not images:
                return ""
            return pytesseract.image_to_string(images[0].convert("L"), lang=self.ocr_lang).strip()
        except Exception as e:
            log.warning("OCR failed page %d: %s", page_index + 1, e)
            return ""

    @staticmethod
    def _detect_language(text: str) -> str:
        try:
            from langdetect import detect
            return detect(text[:2000]) if text else "unknown"
        except Exception:
            return "unknown"
'''

# ──────────────────────────────────────────────────────────────
FILES["src/ingestion/chunker.py"] = '''\n"""
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
        return re.split(r"(?<=[.!?])\s+(?=[A-Z\u00C0-\u017E])", text)


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
'''

# ──────────────────────────────────────────────────────────────
FILES["src/embedding/embedder.py"] = '''\n"""
Embedder — local, CPU-only, ONNX INT8 quantizado.

Primera execução: exporta + quantiza o modelo (one-time, ~1 min).
Execuções seguintes: carrega ONNX diretamente (~3x mais rápido).

Lanes de prioridade:
  HIGH   → queries interativas   (batch=1,  sem espera)
  NORMAL → ingestão ativa        (batch=16, 100ms)
  LOW    → reindex em repouso    (batch=64, 500ms)
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

DEFAULT_MODEL      = "sentence-transformers/all-MiniLM-L6-v2"
MULTILINGUAL_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class Priority(enum.IntEnum):
    HIGH   = 0
    NORMAL = 1
    LOW    = 2


class Embedder:

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        use_onnx: bool = True,
        model_cache_dir: Path = Path("./.melissa_model_cache"),
        normalize: bool = True,
    ) -> None:
        self.model_name = model_name
        self.normalize  = normalize
        if use_onnx:
            self._model     = self._load_or_build_onnx(model_name, model_cache_dir)
            self._encode_fn = self._encode_onnx
        else:
            self._model     = self._load_st(model_name)
            self._encode_fn = self._encode_st
        log.info("Embedder ready: %s  onnx=%s", model_name, use_onnx)

    def encode(self, text: str) -> np.ndarray:
        return self.encode_batch([text])[0]

    def encode_batch(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.empty((0,), dtype=np.float32)
        vecs = self._encode_fn(texts)
        if self.normalize:
            norms = np.linalg.norm(vecs, axis=1, keepdims=True)
            vecs  = vecs / np.maximum(norms, 1e-9)
        return vecs.astype(np.float32)

    @property
    def dim(self) -> int:
        return self.encode("probe").shape[0]

    def _load_or_build_onnx(self, model_name, cache_dir):
        onnx_dir = Path(cache_dir) / model_name.replace("/", "_") / "onnx_int8"
        if onnx_dir.exists():
            return self._load_onnx_model(onnx_dir)
        log.info("Exportando ONNX INT8 (one-time ~1 min)…")
        onnx_dir.mkdir(parents=True, exist_ok=True)
        self._export_and_quantize(model_name, onnx_dir)
        return self._load_onnx_model(onnx_dir)

    @staticmethod
    def _export_and_quantize(model_name, out_dir):
        from optimum.onnxruntime import ORTModelForFeatureExtraction, ORTQuantizer
        from optimum.onnxruntime.configuration import AutoQuantizationConfig
        fp32 = Path(out_dir).parent / "onnx_fp32"
        fp32.mkdir(parents=True, exist_ok=True)
        m = ORTModelForFeatureExtraction.from_pretrained(model_name, export=True)
        m.save_pretrained(str(fp32))
        q = ORTQuantizer.from_pretrained(str(fp32))
        q.quantize(save_dir=str(out_dir),
                   quantization_config=AutoQuantizationConfig.avx512_vnni(
                       is_static=False, per_channel=False))

    @staticmethod
    def _load_onnx_model(onnx_dir):
        from optimum.onnxruntime import ORTModelForFeatureExtraction
        return ORTModelForFeatureExtraction.from_pretrained(str(onnx_dir))

    def _encode_onnx(self, texts):
        from transformers import AutoTokenizer
        import torch
        if not hasattr(self, "_tokenizer"):
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        enc = self._tokenizer(texts, padding=True, truncation=True,
                              max_length=512, return_tensors="pt")
        with torch.no_grad():
            out = self._model(**enc)
        token_embs = out.last_hidden_state.numpy()
        mask       = enc["attention_mask"].numpy()[..., None]
        return ((token_embs * mask).sum(axis=1) / mask.sum(axis=1)).astype(np.float32)

    @staticmethod
    def _load_st(model_name):
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(model_name)

    def _encode_st(self, texts):
        return self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False)


_LANE_CONFIG = {
    Priority.HIGH:   (1,  0.0),
    Priority.NORMAL: (16, 0.1),
    Priority.LOW:    (64, 0.5),
}


class _BatchItem:
    __slots__ = ("text", "priority", "future")
    def __init__(self, text, priority, loop):
        self.text = text; self.priority = priority
        self.future: asyncio.Future = loop.create_future()


class AsyncEmbedder:
    """Async wrapper com batch queue de 3 prioridades."""

    def __init__(self, embedder: Optional[Embedder] = None) -> None:
        self._emb = embedder or Embedder()
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._task = None; self._running = False

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._worker())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try: await self._task
            except asyncio.CancelledError: pass

    async def embed(self, text: str, priority: Priority = Priority.NORMAL) -> np.ndarray:
        loop = asyncio.get_event_loop()
        item = _BatchItem(text, priority, loop)
        await self._queue.put((priority.value, time.monotonic(), item))
        return await item.future

    async def embed_chunk(self, chunk: Chunk, priority: Priority = Priority.NORMAL) -> EmbeddedChunk:
        vec = await self.embed(chunk.text, priority)
        return EmbeddedChunk(**{f: getattr(chunk, f) for f in chunk.__dataclass_fields__},
                             embedding=vec, embedding_model=self._emb.model_name)

    async def _worker(self):
        while self._running:
            batch: list[_BatchItem] = []
            try:
                _, _, first = self._queue.get_nowait()
                batch.append(first)
                lane_size, window = _LANE_CONFIG[first.priority]
                deadline = time.monotonic() + window
                while len(batch) < lane_size:
                    rem = deadline - time.monotonic()
                    if rem <= 0: break
                    try:
                        _, _, item = await asyncio.wait_for(self._queue.get(), timeout=rem)
                        batch.append(item)
                    except asyncio.TimeoutError: break
            except asyncio.QueueEmpty:
                await asyncio.sleep(0.02); continue
            texts = [it.text for it in batch]
            try:
                vecs = await asyncio.get_event_loop().run_in_executor(
                    None, self._emb.encode_batch, texts)
                for it, v in zip(batch, vecs): it.future.set_result(v)
            except Exception as exc:
                for it in batch:
                    if not it.future.done(): it.future.set_exception(exc)
'''

# ──────────────────────────────────────────────────────────────
FILES["src/embedding/vector_store.py"] = '''\n"""
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
'''

# ──────────────────────────────────────────────────────────────
FILES["src/retrieval/rag_runner.py"] = '''\n"""
RAGRunner — pipeline RAG completo.

  1. Embeda query (lane HIGH)
  2. Busca top-k no VectorStore
  3. Re-rank por score semântico + recency boost
  4. Monta contexto
  5. Gera via LM plugável (ou retorna contexto puro se sem LM)
"""

from __future__ import annotations

import textwrap
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.embedding.embedder import Embedder
from src.embedding.vector_store import VectorStore
from src.utils.logger import get_logger

log = get_logger("retrieval.rag_runner")


@dataclass
class RAGConfig:
    top_k_retrieve:     int = 20
    top_n_context:      int = 5
    max_context_tokens: int = 3000
    recency_days_boost: int = 30


class RAGRunner:

    def __init__(self, vector_store=None, embedder=None, config=None,
                 lm=None, data_dir: Path = Path("./data/hot")) -> None:
        self.store = vector_store or VectorStore(data_dir=data_dir)
        self.emb   = embedder    or Embedder()
        self.cfg   = config      or RAGConfig()
        self.lm    = lm
        self._log: list[dict] = []
        log.info("RAGRunner ready — %d chunks", self.store.chunk_count())

    def query(self, question: str, top_k: Optional[int] = None, verbose: bool = False) -> str:
        q_vec      = self.emb.encode(question)
        candidates = self.store.search(q_vec, top_k=top_k or self.cfg.top_k_retrieve)
        if not candidates:
            return "Não há informações indexadas ainda."
        ranked   = self._rerank(candidates)[:self.cfg.top_n_context]
        if verbose: self._print_chunks(ranked)
        context  = self._build_context(ranked)
        response = self._generate(question, context)
        self._log.append({"ts": datetime.utcnow().isoformat(), "query": question,
                          "response": response[:500], "chunks": [c.get("id") for c in ranked]})
        return response

    def get_log(self) -> list[dict]:
        return self._log

    def _rerank(self, candidates: list[dict]) -> list[dict]:
        now = datetime.utcnow()
        for c in candidates:
            base, bonus = 1.0 / (1.0 + c.get("score", 1.0)), 0.0
            created = c.get("created_at")
            if created:
                try:
                    age = (now - datetime.fromisoformat(str(created))).days
                    if age <= self.cfg.recency_days_boost:
                        bonus = 0.2 * (1 - age / self.cfg.recency_days_boost)
                except Exception: pass
            c["_rank"] = base + bonus
        return sorted(candidates, key=lambda x: x["_rank"], reverse=True)

    def _build_context(self, chunks: list[dict]) -> str:
        parts, used = [], 0
        for i, c in enumerate(chunks):
            text = c.get("text", "")
            toks = len(text.split()) * 13 // 10
            if used + toks > self.cfg.max_context_tokens: break
            parts.append(f"[Fonte {i+1}: {Path(c.get('source_path','?' )).name}]\\n{text}")
            used += toks
        return "\\n\\n---\\n\\n".join(parts)

    def _generate(self, question: str, context: str) -> str:
        if self.lm:
            return self.lm(
                "Você é um assistente com acesso à biblioteca pessoal do usuário.\\n"
                f"CONTEXTO:\\n{context}\\n\\nPergunta: {question}\\nResposta:"
            )
        return textwrap.dedent(f"""
            📚 Passagens mais relevantes para: "{question}"
            {"─" * 60}
            {context}
            {"─" * 60}
            (Sem LM configurado — exibindo contexto bruto. Defina `lm=` para gerar respostas.)
        """).strip()

    @staticmethod
    def _print_chunks(chunks):
        print(f"\\n{"─"*60}")
        for i, c in enumerate(chunks):
            print(f"  [{i+1}] score={c.get('_rank',0):.3f}  src={Path(c.get('source_path','?' )).name}")
            print(f"       {c.get('text','')[:120]}…")
        print(f"{"─"*60}\\n")
'''

# ──────────────────────────────────────────────────────────────
FILES["scripts/ingest_pdf.py"] = '''\n#!/usr/bin/env python3
"""
CLI: Ingere PDFs na memória quente do Melissa Core.

Uso:
    python scripts/ingest_pdf.py --path /caminho/doc.pdf
    python scripts/ingest_pdf.py --dir /pasta/ --recursive
    python scripts/ingest_pdf.py --path doc.pdf --no-dedup
"""

from __future__ import annotations
import argparse, sys
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.embedding.embedder import Embedder
from src.embedding.vector_store import VectorStore
from src.ingestion.chunker import ChunkerConfig, SemanticChunker
from src.ingestion.pdf_extractor import PDFExtractor
from src.utils.logger import get_logger, setup_logging
from src.utils.models import EmbeddedChunk

setup_logging()
log = get_logger("scripts.ingest_pdf")


def ingest_file(path, extractor, chunker, embedder, store, force=False):
    from src.utils.hashing import sha256_file
    t0, file_hash = perf_counter(), sha256_file(path)
    if not force and store.file_indexed(file_hash):
        return {"file": path.name, "status": "skipped", "elapsed_s": 0}
    doc = extractor.extract(path)
    if not doc.content.strip():
        return {"file": path.name, "status": "empty", "elapsed_s": perf_counter() - t0}
    chunks = chunker.chunk(doc)
    vecs   = embedder.encode_batch([c.text for c in chunks])
    embedded = [EmbeddedChunk(**{f: getattr(c, f) for f in c.__dataclass_fields__},
                              embedding=v, embedding_model=embedder.model_name)
                for c, v in zip(chunks, vecs)]
    added = store.add(embedded)
    store.register_file(file_hash)
    elapsed = perf_counter() - t0
    log.info("✓ %s  (%d chunks, %.1fs)", path.name, added, elapsed)
    return {"file": path.name, "status": "ok", "chunks": added,
            "pages": doc.page_count, "language": doc.language, "elapsed_s": round(elapsed, 2)}


def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--path", type=Path)
    g.add_argument("--dir",  type=Path)
    p.add_argument("--recursive", action="store_true")
    p.add_argument("--no-dedup",  action="store_true")
    p.add_argument("--data-dir",  type=Path, default=Path("./data/hot"))
    p.add_argument("--no-onnx",   action="store_true")
    p.add_argument("--ocr-lang",  default="eng+por")
    args = p.parse_args()

    files = [args.path] if args.path else list(args.dir.glob("**/*.pdf" if args.recursive else "*.pdf"))
    if not files: sys.exit("Nenhum PDF encontrado.")

    extractor = PDFExtractor(ocr_lang=args.ocr_lang)
    chunker   = SemanticChunker(ChunkerConfig())
    embedder  = Embedder(use_onnx=not args.no_onnx)
    store     = VectorStore(data_dir=args.data_dir, dim=embedder.dim)

    results = [ingest_file(f, extractor, chunker, embedder, store, args.no_dedup)
               for f in files if f.exists()]

    ok = [r for r in results if r["status"] == "ok"]
    print(f"\\n{'═'*50}")
    print(f"  ✓ {len(ok)} ingeridos  ⏭ {sum(1 for r in results if r['status']=='skipped')} pulados")
    print(f"  Total chunks: {store.chunk_count()}")
    if ok: print(f"  Tempo médio: {sum(r['elapsed_s'] for r in ok)/len(ok):.1f}s")
    print(f"{'═'*50}\\n")


if __name__ == "__main__":
    main()
'''

# ──────────────────────────────────────────────────────────────
FILES["tests/test_fase1.py"] = '''\n"""Testes unitários — Fase 1."""

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
'''

# ──────────────────────────────────────────────────────────────
FILES["docs/roadmap.md"] = """\n# Melissa Core — Roadmap

| Fase | Status | Descrição |
|------|--------|-----------|
| 1 | ✅ Implementado | MVP: PDF + chunking + embeddings + RAG-lite |
| 2 | 🔜 Próxima | Memória Hot/Warm/Cold + compressão zstd |
| 3 | 📋 Planejado | Personalidade: LoRA adapters + replay buffer |
| 4 | 📋 Planejado | Idle Agent: aprendizado em repouso |
| 5 | 📋 Planejado | Segunda memória: web scraper público (opt-in) |
| 6 | 📋 Planejado | Interface & UX local (FastAPI + frontend) |
| 7 | 📋 Planejado | Governança, segurança, proveniência |
| 8 | 📋 Planejado | CI/CD completo + documentação |

## Stack

Python 3.10+, sentence-transformers, ONNX Runtime INT8, FAISS (IVF+PQ),
SQLite, PEFT/LoRA, FastAPI, zstd. Local-first, offline, CPU-only por padrão.

## Princípios

- Nenhum adapter é auto-deployado sem aprovação explícita do usuário
- Zero telemetria por padrão
- SHA256 + timestamp em cada chunk (proveniência total)
- Consent flags por arquivo (indexar / treinar adaptadores)
"""

# ──────────────────────────────────────────────────────────────
FILES["data/hot/.gitkeep"]  = ""
FILES["data/warm/.gitkeep"] = ""
FILES["data/cold/.gitkeep"] = ""


# ══════════════════════════════════════════════════════════════
# Escrever todos os arquivos
# ══════════════════════════════════════════════════════════════

def write_all():
    created, skipped = 0, 0
    for rel_path, content in FILES.items():
        full = ROOT / rel_path
        full.parent.mkdir(parents=True, exist_ok=True)
        if full.exists() and full.read_text(encoding="utf-8") == content:
            skipped += 1
            continue
        full.write_text(content, encoding="utf-8")
        print(f"  ✓ {rel_path}")
        created += 1

    print(f"\n{'═'*50}")
    print(f"  {created} arquivos criados/atualizados")
    print(f"  {skipped} já estavam corretos")
    print(f"{'═'*50}")
    print("\nPróximos passos:")
    print("  git add -A")
    print('  git commit -m "feat: Fase 1 completa — RAG-lite + FAISS + ONNX embedder"')
    print("  git push origin main")


if __name__ == "__main__":
    print("\n🌿 Melissa Core — recreate.py\n")
    write_all()
