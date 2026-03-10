
#!/usr/bin/env python3
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
    print(f"\n{'═'*50}")
    print(f"  ✓ {len(ok)} ingeridos  ⏭ {sum(1 for r in results if r['status']=='skipped')} pulados")
    print(f"  Total chunks: {store.chunk_count()}")
    if ok: print(f"  Tempo médio: {sum(r['elapsed_s'] for r in ok)/len(ok):.1f}s")
    print(f"{'═'*50}\n")


if __name__ == "__main__":
    main()
