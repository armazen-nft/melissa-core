# FASE 2 — Memory Tiers

## Objetivo
Adicionar memória hierárquica (hot/warm/cold) mantendo compatibilidade de API da Fase 1.

## Arquitetura
- **Hot tier**: índice em memória para baixa latência e busca vetorial.
- **Warm tier**: dados comprimidos, lazy load, preserva embedding.
- **Cold tier**: arquivamento com alta compressão (texto only).

## Capacidades e SLOs
| Tier | Capacidade | Índice | Latência alvo | Compressão |
| --- | --- | --- | --- | --- |
| Hot | 5k–50k | Vetorial in-memory | < 5 ms | n/a |
| Warm | Ilimitada | Lazy decode | 10–50 ms | ~3.5x |
| Cold | Ilimitada | Busca textual | 100–500 ms | ~12x |

## API pública
```python
memory = MelissaFase2Integrator(embedder, config)
await memory.add(chunk_id, text)
results = await memory.search(query, k=10)
```

## Migração
- Hot → Warm: por padrão após 24h sem acesso.
- Warm → Cold: por padrão após 30 dias sem acesso.
- Loop pode rodar em background sem alterar chamadas existentes.

## Roadmap
- Fase 3: reranking híbrido.
- Fase 4: persistência em disco por partições.
- Fase 5: replicação local opcional.
- Fase 6: políticas dinâmicas de tiering por custo.
- Fase 7: telemetria de qualidade por consulta.
- Fase 8: tuning automático de perfis de compressão.
