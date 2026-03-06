#!/usr/bin/env python3
"""
CLI: Ingest one or more PDF files into MelissaCore hot memory.

Usage:
    python scripts/ingest_pdf.py --path /path/to/doc.pdf
    python scripts/ingest_pdf.py --dir /path/to/folder --recursive
    python scripts/ingest_pdf.py --path doc.pdf --no-dedup
"""

from __future__ import annotations

import argparse
import sys
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


def ingest_file(
    path: Path,
    extractor: PDFExtractor,
    chunker: SemanticChunker,
    embedder: Embedder,
    store: VectorStore,
    force: bool = False,
) -> dict:
    from src.utils.hashing import sha256_file

    t0 = perf_counter()
    file_hash = sha256_file(path)

    if not force and store.file_indexed(file_hash):
        log.info("SKIP (already indexed): %s", path.name)
        return {"file": path.name, "status": "skipped", "elapsed_s": 0}

    log.info("Extracting: %s", path.name)
    doc = extractor.extract(path)

    if not doc.content.strip():
        log.warning("Empty content — skipping: %s", path.name)
        return {"file": path.name, "status": "empty", "elapsed_s": perf_counter() - t0}

    chunks = chunker.chunk(doc)
    log.info("  → %d chunks", len(chunks))

    texts = [c.text for c in chunks]
    log.info("  → Embedding %d chunks…", len(chunks))
    t_emb = perf_counter()
    vecs = embedder.encode_batch(texts)
    log.info("  → Embedded in %.1fs", perf_counter() - t_emb)

    embedded = [
        EmbeddedChunk(
            **{f: getattr(chunk, f) for f in chunk.__dataclass_fields__},
            embedding=vec,
            embedding_model=embedder.model_name,
        )
        for chunk, vec in zip(chunks, vecs)
    ]

    added = store.add(embedded)
    store.register_file(file_hash)

    elapsed = perf_counter() - t0
    log.info("✓ Ingested: %s  (%d chunks, %.1fs)", path.name, added, elapsed)
    return {
        "file": path.name,
        "status": "ok",
        "chunks": added,
        "pages": doc.page_count,
        "language": doc.language,
        "elapsed_s": round(elapsed, 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest PDFs into MelissaCore")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--path", type=Path)
    group.add_argument("--dir", type=Path)
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--no-dedup", action="store_true")
    parser.add_argument("--data-dir", type=Path, default=Path("./data/hot"))
    parser.add_argument("--no-onnx", action="store_true")
    parser.add_argument("--ocr-lang", default="eng+por")
    args = parser.parse_args()

    if args.path:
        files = [args.path]
    else:
        pattern = "**/*.pdf" if args.recursive else "*.pdf"
        files = list(args.dir.glob(pattern))
        if not files:
            log.error("No PDF files found in %s", args.dir)
            sys.exit(1)
        log.info("Found %d PDF files", len(files))

    extractor = PDFExtractor(ocr_lang=args.ocr_lang)
    chunker = SemanticChunker(ChunkerConfig())
    embedder = Embedder(use_onnx=not args.no_onnx)
    store = VectorStore(data_dir=args.data_dir, dim=embedder.dim)

    results = []
    for f in files:
        if not f.exists():
            log.error("File not found: %s", f)
            continue
        results.append(ingest_file(f, extractor, chunker, embedder, store, force=args.no_dedup))

    ok = [r for r in results if r["status"] == "ok"]
    skipped = [r for r in results if r["status"] == "skipped"]
    failed = [r for r in results if r["status"] not in ("ok", "skipped")]

    print(f"\n{'═'*50}")
    print("  Ingest complete")
    print(f"  ✓ {len(ok)} ingested  ⏭ {len(skipped)} skipped  ✗ {len(failed)} failed")
    print(f"  Total chunks indexed: {store.chunk_count()}")
    if ok:
        print(f"  Avg time/file: {sum(r['elapsed_s'] for r in ok)/len(ok):.1f}s")
    print(f"{'═'*50}\n")


if __name__ == "__main__":
    main()
