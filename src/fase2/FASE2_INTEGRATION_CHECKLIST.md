# FASE 2 Integration Checklist

1. Criar pasta `src/fase2`.
2. Copiar os módulos:
   - `melissa_core_fase2_memory_tiers.py`
   - `melissa_core_fase2_compression_bench.py`
   - `melissa_core_fase2_integration.py`
3. Expor integrador no módulo de entrada (`src/melissa.py`).
4. Atualizar `README.md` com instruções de uso e receitas de deployment.
5. Validar sintaxe Python (`python -m compileall src/fase2 src/melissa.py`).
6. Rodar benchmark de compressão opcional para baseline.
7. Commitar e abrir PR.
