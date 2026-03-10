
"""
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
            parts.append(f"[Fonte {i+1}: {Path(c.get('source_path','?' )).name}]\n{text}")
            used += toks
        return "\n\n---\n\n".join(parts)

    def _generate(self, question: str, context: str) -> str:
        if self.lm:
            return self.lm(
                "Você é um assistente com acesso à biblioteca pessoal do usuário.\n"
                f"CONTEXTO:\n{context}\n\nPergunta: {question}\nResposta:"
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
        print(f"\n{'─' * 60}")
        for i, c in enumerate(chunks):
            print(f"  [{i+1}] score={c.get('_rank',0):.3f}  src={Path(c.get('source_path','?' )).name}")
            print(f"       {c.get('text','')[:120]}…")
        print(f"{'─' * 60}\n")
