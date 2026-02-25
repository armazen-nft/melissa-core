# Melissa Core – Inteligência Artificial para Máquinas Antigas, Espíritos Novos

🌿 **Melissa Core** é um projeto de IA mínima, simbólica e resiliente, escrita em C puro.

Foi projetada para rodar localmente em hardwares modestos, mesmo offline, com baixo consumo de energia e sem dependência de nuvem. Inspirada por uma ética ancestral, Melissa é um ensaio sobre o futuro da inteligência distribuída, sustentável e acessível.

---

## 🧠 O que ela é?

- Um núcleo de IA capaz de rodar em sistemas antigos (1GB RAM ou menos)
- Projeto modular, ético, baseado em oráculos simbólicos (Daizen)
- Adaptada a arquiteturas esquecidas (como PowerPC, ARMv6 e afins)
- Livre, replicável, resistente

---

## 🛠️ Como compilar

No terminal MSYS2 (`MINGW64`):

```bash
cd /c/Users/seu_usuario/melissa-core
make
./melissa
```

---

## ✅ Checklist pré-merge (C89 estrito)

Antes de publicar uma branch com o núcleo completo (`src/`, `include/`, `tests/`), valide estes pontos:

1. `include/melissa.h` **deve** incluir:

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>
```

Sem isso, tipos como `int8_t` e funções como `clock()`/`time(NULL)` quebram a compilação.

2. Seed de aleatoriedade no início do `main`:

```c
srand((unsigned)time(NULL));
```

3. Em `selfplay_update`, além de pesos, considerar mutação de *bias* (com menor probabilidade).

4. Se houver alvo de tamanho no `Makefile`, incluir também opção de *strip* (ex.: `--strip-all`) para reduzir binário final em ambientes legacy.

---

## 🌱 Próximos passos sugeridos

- Expandir o contexto simbólico injetado pelo Daizen.
- Adicionar modo `--oracle "texto"` com tokenização simples.
- Criar modo daemon para serial/pipe.
- Preparar script opcional de replicação para ambientes antigos.
