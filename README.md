# Melissa Core

> "Não queremos uma IA poderosa. Queremos uma IA presente, viva, ética."

**Melissa Core** é um núcleo de IA mínima escrito em C89 puro, sem dependências externas.

## O que é

- IA local e offline para hardware antigo.
- Modelo ternário com pesos em `{-1, 0, +1}`.
- Loop de self-play simbólico.
- Oráculo FSM (`Daizen`) para injeção de contexto.

## Estrutura

- `include/melissa.h`: tipos, limites e API pública.
- `src/melissa_model.c`: inicialização, persistência e inspeção do modelo.
- `src/melissa_inference.c`: inferência ternária sem FPU.
- `src/melissa_selfplay.c`: treino autônomo via geração/verificação de problemas.
- `src/daizen_core.c`: FSM simbólica de percepção.
- `src/melissa_main.c`: CLI e modos de execução.
- `tests/test_all.c`: suite de testes sem framework externo.

## Build

```bash
make
./bin/melissa --info
```

## Treino

```bash
make train N=5000
```

## Benchmark

```bash
make bench
```

## Testes

```bash
make test
```

## Cross-compile

```bash
make arm
make ppc
make mips
```
