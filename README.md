
# 🌿 Melissa Core

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
