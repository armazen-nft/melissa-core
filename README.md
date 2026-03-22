Melissa Core – Inteligência Artificial para Máquinas Antigas, Espíritos Novos

Melissa Core é um projeto de IA mínima, simbólica e resiliente, escrita em C puro.

Foi projetada para rodar localmente em hardwares modestos, mesmo offline, com baixo consumo de energia e sem dependência de nuvem. Inspirada por uma ética ancestral, Melissa é um ensaio sobre o futuro da inteligência distribuída, sustentável e acessível.

---

## O que ela é?

- Um núcleo de IA capaz de rodar em sistemas antigos (1GB RAM ou menos)
- Projeto modular, ético, baseado em oráculos simbólicos (Daizen)
- Adaptada a arquiteturas esquecidas (como PowerPC, ARMv6 e afins)
- Livre, replicável, resistente

---

## O que este fork adiciona

Este fork implanta um módulo **Enochian** em C puro para transformar o Melissa Core em um núcleo pronto para comunicação simbólica entre agentes locais. A nova camada segue a mesma filosofia do projeto: sem dependências externas, com estruturas pequenas, funcionamento offline e foco em portabilidade.

### Novo layout

```text
melissa-core/
├── include/
│   ├── melissa.h
│   └── enochian/
│       ├── enochian_token.h
│       ├── enochian_consensus.h
│       ├── enochian_evolution.h
│       └── enochian_bridge.h
├── src/
│   ├── melissa_tokenizer.c
│   └── enochian/
│       ├── enochian_token.c
│       ├── enochian_consensus.c
│       ├── enochian_evolution.c
│       └── enochian_bridge.c
├── tests/
│   └── test_enochian.c
└── Makefile
```

## Módulo Enochian

### `enochian_token`

Define o token simbólico mínimo usado para troca entre agentes:

- `glyph`: nome curto do token (`Tok-Pa`, etc.)
- `domain`: domínio semântico (`arithmetic`, `justice`, `general`)
- `phase`: tendência de exploração/estabilidade
- `flux`: intensidade operacional compacta
- `ethic`: prioridade ética normalizada
- `context[]`: vetor ternário transportável
- `checksum`: integridade determinística

### `enochian_consensus`

Mantém até 8 votos locais e resolve um token final por maioria ponderada de:

- glifo
- domínio
- afinidade ética

Isso permite que várias interpretações locais cheguem a uma formulação comum sem bibliotecas externas nem alocação dinâmica.

### `enochian_evolution`

Implementa uma mutação leve baseada em LCG, útil para:

- explorar variações semânticas de tokens
- testar regimes de exploração frugal
- evoluir mensagens sem custo alto de CPU

### `enochian_bridge`

Faz a ponte entre Melissa e Enochian:

- `melissa_enochian_token_from_state()` converte `TernaryModel + SelfPlayStats` em token simbólico
- `melissa_enochian_apply_token()` traduz o token em vieses locais de exploração, justiça e sustentabilidade
- `melissa_enochian_selfplay_consensus()` usa a telemetria de self-play para reforçar ou ajustar o consenso local

## Compilar

### Build padrão

```bash
make
```

### Rodar testes

```bash
make test
```

### Compilar apenas o alvo Enochian

```bash
make enochian
```

## Exemplo conceitual de uso futuro

```bash
# Gera um token a partir de um estado Melissa
./test_enochian

# Futuro CLI proposto
./melissa --train 10000 --domain arithmetic --model arith.model
./melissa --enochian --model arith.model --port 8765
./melissa --enochian --connect 127.0.0.1:8765 \
  --send "Tok-Pa[domain=arithmetic,phase=4,flux=8,ethic=7,ctx=4,checksum=123]"
```

## Testes

O arquivo `tests/test_enochian.c` valida:

- geração de token a partir do estado Melissa
- serialização e parsing determinísticos
- consenso local
- mutação/evolução de token
- aplicação do token na ponte Melissa–Enochian

## Filosofia

Melissa não é um chatbot. Ela é um experimento em inteligência frugal: aprender com seus próprios problemas, sem dados externos, sem conexão obrigatória e sem energia desperdiçada. Este fork estende essa visão para uma comunicação peer-to-peer simbólica e ética entre instâncias locais.

## Licença

MIT
