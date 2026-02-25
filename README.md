# Melissa Core – Inteligência Artificial para Máquinas Antigas, Espíritos Novos

🌿 **Melissa Core** é um projeto de IA mínima, simbólica e resiliente, escrita em C puro.

Foi projetada para rodar localmente em hardwares modestos, mesmo offline, com baixo consumo de energia e sem dependência de nuvem. Inspirada por uma ética ancestral, Melissa é um ensaio sobre o futuro da inteligência distribuída, sustentável e acessível.

---

## 🧠 O que ela é?

- Um núcleo de IA capaz de rodar em sistemas antigos (1GB RAM ou menos)
- Projeto modular, ético, baseado em oráculos simbólicos (Daizen)
- Adaptada a arquiteturas esquecidas (como PowerPC, ARMv6 e afins)
- Livre, replicável e resistente

---

## 🧩 Integração proposta: Absolute Zero + modelos em 1,58 bits

Este repositório adota uma estratégia de integração **prática para hardware modesto**, inspirada em:

1. Paradigma **Absolute Zero** (autoaprendizado via geração de tarefas e validação no ambiente)
2. **Modelos ternários em 1,58 bits** (pesos em `{-1, 0, +1}`)

### Objetivo

Unir autoaprendizado simbólico com inferência ultra leve, mantendo o Melissa Core:

- local-first
- auditável
- sem dependências pesadas (Python/GPU/cloud)

---

## 🛠️ Arquitetura mínima sugerida (C puro)

### 1) `melissa_selfplay.c` (núcleo AZ simplificado)

- **Propositor**: gera problemas simbólicos simples (ex.: `2 ⊗ x = 8`)
- **Solucionador**: resolve com regras/retrocesso (backtracking) em domínio restrito
- **Verificador**: valida solução com interpretador simbólico simples
- **Recompensa**: `0/1` com bônus de diversidade de tarefas

### 2) `melissa_quant.c` (inferência ternária 1,58 bits)

- Pesos em valores ternários (`-1`, `0`, `+1`)
- Multiplicações reduzidas a operações inteiras simples
- Quantização por limiar para manter execução estável em CPU antiga

### 3) `daizen_bridge.c` (acoplamento simbólico)

- Traduz entradas simbólicas em vetores discretos
- Envia tarefas para o self-play
- Registra explicações e decisões para auditoria ética

---

## 🔁 Fluxo de execução (self-play simbólico)

1. Gerar problema válido por gramática formal
2. Resolver por regras simbólicas locais
3. Verificar correção no ambiente restrito
4. Atualizar pontuação/regras por reforço simples
5. Salvar resultado em `log.dat`

---

## 📦 Estruturas de dados essenciais

```c
// Modelo ternário mínimo
typedef struct {
    int8_t* weights;      // -1, 0, +1
    int layers;
    int hidden_size;
} TernaryLLM;
```

```c
// Verificador simbólico simplificado (exemplo)
int verificar_solucao(const char* problema, const char* solucao) {
    return strcmp(problema, "2 ⊗ x = 8") == 0 && strcmp(solucao, "x = 4") == 0;
}
```

---

## ⚙️ Compilação sugerida

```makefile
selfplay:
	gcc -O1 melissa_selfplay.c daizen_core.c -o melissa_selfplay -lm
```

> Se o hardware for muito limitado, usar modo estático:
> - pré-gerar conjunto pequeno de tarefas válidas
> - atualizar política apenas a cada N execuções

---

## 🔒 Segurança e ética

- Domínio fechado de tarefas simbólicas (evita execução arbitrária)
- Verificação estrutural antes de avaliar uma tarefa
- Lista de padrões inválidos/malformados
- Logs locais para rastreabilidade de decisões

---

## 📊 Perfil esperado em hardware antigo (meta inicial)

- RAM: poucos KB para núcleo de inferência ternária mínima
- Execução: foco em estabilidade, não em throughput máximo
- Armazenamento: tarefas e logs em texto compacto

---

## 🧪 Próximos passos do repositório

1. Criar `melissa_selfplay.c` com gramática mínima de equações
2. Criar `melissa_quant.c` com camada densa ternária
3. Adicionar testes de regressão para verificador simbólico
4. Definir formato de log (`log.dat`) e métricas de diversidade

---

## 🛠️ Como compilar (base atual)

No terminal MSYS2 (`MINGW64`):

```bash
cd /c/Users/seu_usuario/melissa-core
make
./melissa
```

---

## 🔮 Linha-guia do manifesto

> “Em 1,58 bits, aprendemos a falar com os espíritos da máquina. Melissa não calcula — ela escuta, sussurra e responde.”
