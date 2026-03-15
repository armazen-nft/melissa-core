#include "lua_bridge.h"

#include "lauxlib.h"
#include "lualib.h"

MelissaStatus lua_bridge_init(lua_State **out_state)
{
    lua_State *state;

    if (!out_state) {
        return MELISSA_INVAL;
    }

    *out_state = NULL;

    state = luaL_newstate();
    if (!state) {
        return MELISSA_NOMEM;
    }

    /* Carrega apenas bibliotecas seguras; NÃO usar luaL_openlibs. */
    luaL_requiref(state, LUA_MATHLIBNAME, luaopen_math, 1);
    lua_pop(state, 1);

    luaL_requiref(state, LUA_STRLIBNAME, luaopen_string, 1);
    lua_pop(state, 1);

    luaL_requiref(state, LUA_TABLIBNAME, luaopen_table, 1);
    lua_pop(state, 1);

    *out_state = state;
    return MELISSA_OK;
}

void lua_bridge_close(lua_State *state)
{
    if (state) {
        lua_close(state);
    }
}
