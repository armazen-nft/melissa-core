"""
RAGRunner — Retrieval-Augmented Generation pipeline.

Flow:
  1. Embed user query (HIGH priority lane).
  2. Search VectorStore for top-k candidates.
  3. Re-rank by semantic score + recency boost.
  4. Build context prompt from top-n chunks.
  5. Generate via local LM (or return context-only if no LM loaded).
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
    top_k_retrieve: int = 20
    top_n_context: int = 5
    max_context_tokens: int = 3000
    recency_days_boost: int = 30


class RAGRunner:
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embedder: Optional[Embedder] = None,
        config: Optional[RAGConfig] = None,
        lm=None,
        data_dir: Path = Path("./data/hot"),
    ) -> None:
        self.store = vector_store or VectorStore(data_dir=data_dir)
        self.emb = embedder or Embedder()
        self.cfg = config or RAGConfig()
        self.lm = lm
        self._interaction_log: list[dict] = []
        log.info("RAGRunner ready — %d chunks indexed", self.store.chunk_count())

    def query(
        self,
        question: str,
        top_k: Optional[int] = None,
        verbose: bool = False,
    ) -> str:
        k = top_k or self.cfg.top_k_retrieve

        q_vec = self.emb.encode(question)
        candidates = self.store.search(q_vec, top_k=k)

        if not candidates:
            msg = "I don't have any relevant information indexed yet."
            self._log_interaction(question, msg, [])
            return msg

        ranked = self._rerank(candidates, question)[: self.cfg.top_n_context]
        if verbose:
            self._print_chunks(ranked)

        context = self._build_context(ranked)
        response = self._generate(question, context)
        self._log_interaction(question, response, ranked)
        return response

    def get_interaction_log(self) -> list[dict]:
        return self._interaction_log

    def _rerank(self, candidates: list[dict], query: str) -> list[dict]:
        now = datetime.utcnow()
        boost_days = self.cfg.recency_days_boost
        for c in candidates:
            base = 1.0 / (1.0 + c.get("score", 1.0))
            recency_bonus = 0.0
            created = c.get("created_at")
            if created:
                try:
                    dt = datetime.fromisoformat(str(created))
                    age_days = (now - dt).days
                    if age_days <= boost_days:
                        recency_bonus = 0.2 * (1 - age_days / boost_days)
                except Exception:
                    pass
            c["_rank_score"] = base + recency_bonus
        return sorted(candidates, key=lambda x: x["_rank_score"], reverse=True)

    def _build_context(self, chunks: list[dict]) -> str:
        parts: list[str] = []
        used = 0
        for i, c in enumerate(chunks):
            text = c.get("text", "")
            source = c.get("source_path", "unknown")
            chunk_tokens = len(text.split()) * 13 // 10
            if used + chunk_tokens > self.cfg.max_context_tokens:
                break
            parts.append(f"[Source {i+1}: {Path(source).name}]\n{text}")
            used += chunk_tokens
        return "\n\n---\n\n".join(parts)

    def _generate(self, question: str, context: str) -> str:
        if self.lm is not None:
            return self.lm(self._build_prompt(question, context))
        return textwrap.dedent(
            f"""
            📚 Most relevant passages for: "{question}"
            {'─' * 60}
            {context}
            {'─' * 60}
            (No LM loaded — showing raw context. Set `lm=` to enable generation.)
        """
        ).strip()

    @staticmethod
    def _build_prompt(question: str, context: str) -> str:
        return (
            "You are a knowledgeable assistant with access to the user's personal library.\n"
            "Use the following retrieved passages to answer the question.\n"
            "If the passages don't contain enough information, say so clearly.\n\n"
            f"--- CONTEXT ---\n{context}\n--- END CONTEXT ---\n\n"
            f"Question: {question}\nAnswer:"
        )

    def _log_interaction(self, question: str, response: str, chunks: list[dict]) -> None:
        self._interaction_log.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "query": question,
                "response": response[:500],
                "chunk_ids": [c.get("id") for c in chunks],
            }
        )

    @staticmethod
    def _print_chunks(chunks: list[dict]) -> None:
        print(f"\n{'─'*60}")
        for i, c in enumerate(chunks):
            print(
                f"  [{i+1}] score={c.get('_rank_score', 0):.3f}  "
                f"src={Path(c.get('source_path','?')).name}"
            )
            print(f"       {c.get('text','')[:120]}…")
        print(f"{'─'*60}\n")
