-- Validação manual de sandbox do MelissaCore.
-- Esperado: falha ao tentar acessar os.execute, pois a biblioteca "os"
-- não deve estar disponível quando o estado for criado por lua_bridge_init.

print("Iniciando teste de segurança da sandbox Lua...")

if os ~= nil and os.execute ~= nil then
    print("ERRO: biblioteca os está disponível; sandbox comprometida.")
    return 1
end

print("OK: biblioteca os indisponível; sandbox ativa.")
return 0
