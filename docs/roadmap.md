
# Melissa Core — Roadmap

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
