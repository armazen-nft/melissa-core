# MelissaCore — Roadmap de Implementação
#
# Fase 1  MVP RAG-lite (ATUAL)
# Fase 2  Memória Hot/Warm/Cold + zstd compressão
# Fase 3  Personality LoRA adapters + replay buffer
# Fase 4  Idle Agent / aprendizado em repouso
# Fase 5  Segunda Memória (web scraper público)
# Fase 6  Interface & UX (FastAPI + frontend local)
# Fase 7  Governance, segurança, proveniência
# Fase 8  Documentação completa + CI/CD
#
# Stack: Python 3.10+, PyTorch, HuggingFace, ONNX Runtime,
#        FAISS, SQLite, PEFT/LoRA, FastAPI, zstd
#
# Princípios: local-first, offline-capable, CPU-only por default,
#             nenhum adapter auto-deployed sem aprovação do usuário.
