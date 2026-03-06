# 🧠 MelissaCore

> RAG-lite + adapter-based personal memory system. Local-first, offline, CPU-friendly.

MelissaCore is a **personal knowledge engine** that ingests your documents, audio,
video, and web pages into a searchable, compressed, evolving memory — augmenting a
lightweight language model with retrieval, personality adapters (LoRA), and an idle
learning agent.

---

## ✨ Features

| Module | Description |
|--------|-------------|
| **Ingestor** | PDF, OCR, audio (Whisper), video, web pages |
| **Chunker** | Sentence-aware semantic chunking with overlap |
| **Embedder** | ONNX INT8 quantized sentence-transformers (CPU fast) |
| **Vector DB** | FAISS IVF+PQ local index |
| **Memory Tiers** | Hot / Warm / Cold with zstd compression |
| **Personality** | LoRA adapters trained on replay buffer |
| **Idle Agent** | Background study, compression, adapter updates |
| **Governance** | SHA256 provenance, audit logs, consent flags |

---

## 🚀 Quickstart

```bash
git clone https://github.com/yourname/MelissaCore.git
cd MelissaCore
pip install -e ".[dev]"
cp config.example.toml config.toml

# Ingest a PDF
python scripts/ingest_pdf.py --path /path/to/document.pdf

# Query
python -c "
from src.retrieval.rag_runner import RAGRunner
rag = RAGRunner()
print(rag.query('What did I read about attention mechanisms?'))
"
```

## Prerequisites
- Python 3.10+
- `tesseract-ocr` → `apt install tesseract-ocr`
- `ffmpeg` → `apt install ffmpeg`

## Project Structure
```
MelissaCore/
├── docs/                   # Roadmap, architecture, manuals
├── src/
│   ├── ingestion/          # PDF, OCR, audio, video, web extractors
│   ├── embedding/          # Embedder + FAISS vector store
│   ├── retrieval/          # RAG runner + semantic search
│   ├── synthesis/          # LM + LoRA adapter integration
│   ├── compression/        # Hot/warm/cold memory + zstd
│   ├── personality/        # Style fingerprint + adapter trainer
│   ├── scheduler/          # Idle agent + background jobs
│   ├── utils/              # Logging, hashing, metadata
│   └── ui/                 # FastAPI local web interface
├── data/
│   ├── hot/
│   ├── warm/
│   └── cold/
├── scripts/
├── tests/
└── notebooks/
```

## Privacy
- Local-first: all data stays on device
- No telemetry: zero external calls by default
- Provenance: SHA256 + source + timestamp per chunk
- Consent flags: per-file opt-in for indexing / redistribution

See [docs/roadmap.md](docs/roadmap.md) for the full phased plan.
