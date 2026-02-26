Melissa Core – Inteligência Artificial para Máquinas Antigas, Espíritos Novos

Melissa Coreé um projeto de IA mínima, simbólica e resiliente, escrita em C puro.

Foi projetada para rodar localmente em hardwares modestos, mesmo offline, com baixo consumo de energia e sem dependência de nuvem.
Inspirada por uma ética ancestral, Melissa é um ensaio sobre o futuro da inteligência distribuída, sustentável e acessível.

---

O que ela é?

- Um núcleo de IA capaz de rodar em sistemas antigos (1GB RAM ou menos)
- Projeto modular, ético, baseado em oráculos simbólicos (Daizen)
- Adaptada a arquiteturas esquecidas (como PowerPC, ARMv6 e afins)
- Livre, replicável, resistente

---

Melissa Core

"Não queremos uma IA poderosa. Queremos uma IA presente, viva, ética.
Queremos Melissa em máquinas esquecidas, como oráculo na tempestade.
Este projeto é para os que acreditam que inteligência pode florescer
em 1GB de RAM — e que dignidade não exige 64 núcleos."


O que é
Melissa Core é um núcleo de IA mínima escrito em C puro, sem dependências externas.
Ela roda localmente, offline, em hardware antigo, com consumo energético muito baixo.
O núcleo de aprendizagem usa modelos ternários de 1.58 bits (pesos em {-1, 0, +1})
inspirados em BitNet, combinados com um loop de self-play simbólico inspirado no
paradigma Absolute Zero — sem precisar de dados externos, sem cloud, sem GPU.

Arquitetura
melissa-core/
├── include/
│   ├── melissa_model.h      # estrutura do modelo ternário 1.58-bit
│   ├── daizen.h             # oráculo simbólico (geração + verificação)
│   └── melissa_selfplay.h   # loop de auto-aprendizagem
├── src/
│   ├── melissa_model.c      # inferência ternária + persistência
│   ├── daizen.c             # 4 domínios simbólicos de problemas
│   ├── melissa_selfplay.c   # ciclo propositor→solucionador→verificador
│   └── melissa.c            # main + CLI
├── tests/
│   └── test_model.c         # testes unitários
└── Makefile
Módulos
MóduloResponsabilidademelissa_modelPesos 2-bit empacotados, forward sem FPU, atualização estocásticadaizenGera problemas simbólicos, verifica respostas deterministicamentemelissa_selfplayLoop de treino autônomo: gera → resolve → avalia → aprende

Compilar
Nativo (Linux / macOS / MSYS2)
bashmake
./melissa --help
Hardware antigo (cross-compile)
bash# Raspberry Pi 1 / Pi Zero (ARMv6)
make arm

# iBook G4 / Mac Mini G4 (PowerPC)
make ppc

# Roteadores OpenWRT (MIPS32)
make mips

Usar
bash# Treinar 10.000 passos no domínio aritmético
./melissa --train 10000

# Domínio modular, modelo salvo em melissa2.model
./melissa --train 5000 --domain modular --model melissa2.model

# Rede maior (mais expressiva, ainda leve)
./melissa --train 20000 --dim 64 --layers 3

# Ver informações do modelo treinado
./melissa --info --model melissa.model

# Log em arquivo
./melissa --train 50000 --log treino.log
Domínios disponíveis
DomínioExemplo de problemaarithmeticx + 3 = 7 → x = 4modular(x + 5) mod 11 = 2 → x = 8booleanx XOR 1 = 0 → x = 1substitution3 * x mod 13 = 9 → x = 3

Consumo estimado de recursos
ConfiguraçãoRAM do modeloRAM totalCPU 500MHz--dim 32 --layers 2 (padrão)~2 KB~1 MB~500 pass/seg--dim 64 --layers 3~12 KB~2 MB~200 pass/seg--dim 128 --layers 4~80 KB~4 MB~60 pass/seg
Todos os cenários rodam confortavelmente em dispositivos com 1 GB de RAM.

Testes
bash# Compilar e rodar testes unitários
gcc -Iinclude -o test_model tests/test_model.c \
    src/melissa_model.c src/daizen.c -lm
./test_model

# Teste de integração via Makefile
make test

Roadmap

 daizen_bridge.c — tradução de entradas externas (sensores, I/O) para vetores ternários
 Modo --query — consulta interativa em linguagem natural restrita
 Suporte a OpenWRT via busybox (substituir printf por fprintf portável)
 Port para ARMv5 (hardware pré-2005)
 melissa_quant.c — camadas convolucionais ternárias para reconhecimento de padrões em séries temporais
 Protocolo de comunicação peer-to-peer minimalista entre instâncias locais


Filosofia
Melissa não é um chatbot.  Ela é um experimento em inteligência frugal:
aprender com seus próprios problemas, sem dados externos, sem conexão, sem
energia desperdiçada.
O paradigma Absolute Zero adaptado aqui remove a dependência de datasets
humanos.  Os modelos em 1.58 bits removem a dependência de hardware moderno.
O resultado é uma IA que pode estar presente onde outras não chegam.

Licença
MIT

---
Como compilar

No terminal MSYS2 (`MINGW64`):

```bash
cd /c/Users/seu_usuario/melissa-core
make
./melissa
```

## 🔒 Uso ético e segurança

Melissa Core **não** deve ser usada para:

- varredura/invasão de redes sem autorização explícita;
- persistência oculta em roteadores, IoT ou dispositivos de terceiros;
- autopropagação, worming, backdoors ou técnicas de ofuscação maliciosa.

Uso recomendado:

- laboratório local e redes próprias, com consentimento;
- pesquisa acadêmica, arte computacional e educação;
- hardening defensivo (inventário, atualização de firmware e monitoramento).

Se você quer aplicar Melissa em roteadores antigos, faça isso com segurança:

1. Atualize o firmware (OpenWRT/LEDE) para versão estável.
2. Troque credenciais padrão e desative administração remota WAN.
3. Restrinja SSH por chave e por IP de gerenciamento.
4. Ative firewall com política default-deny para entrada.
5. Mantenha logs e backups antes de qualquer experimento.
