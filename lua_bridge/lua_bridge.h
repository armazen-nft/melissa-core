#ifndef MELISSA_LUA_BRIDGE_H
#define MELISSA_LUA_BRIDGE_H

#include "melissa.h"
#include "lua.h"

/* Inicializa um estado Lua em modo sandbox (somente libs seguras). */
MelissaStatus lua_bridge_init(lua_State **out_state);

/* Libera um estado Lua previamente criado por lua_bridge_init. */
void lua_bridge_close(lua_State *state);

#endif /* MELISSA_LUA_BRIDGE_H */
