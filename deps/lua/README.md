# Lua vendorizado

Este diretório é reservado para os fontes oficiais do Lua (ex.: `deps/lua/src/*.c`).

Devido à indisponibilidade de acesso de rede no ambiente de execução do agente,
os fontes não puderam ser baixados automaticamente neste commit.

Para completar a integração localmente:

1. Baixe o tarball oficial de Lua 5.4.x.
2. Extraia `src/` para `deps/lua/src`.
3. Rode `make` para gerar `liblua.a` e `libmelissa_core.a`.
