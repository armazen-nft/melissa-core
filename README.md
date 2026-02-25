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
