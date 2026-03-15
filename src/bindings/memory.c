#include "memory.h"

#include "lua_bridge.h"
#include "../lua_bridge_internal.h"

#include <lauxlib.h>

static struct melissa_lua_bridge *get_bridge(lua_State *L) {
    lua_getfield(L, LUA_REGISTRYINDEX, "__melissa_bridge");
    struct melissa_lua_bridge *bridge = lua_touserdata(L, -1);
    lua_pop(L, 1);
    return bridge;
}

static int l_memory_read(lua_State *L) {
    struct melissa_lua_bridge *bridge = get_bridge(L);
    const char *key = luaL_checkstring(L, 1);
    int tier = (int)luaL_checkinteger(L, 2);

    if (!bridge || !bridge->cfg.memory_read) {
        lua_pushnil(L);
        return 1;
    }

    melissa_memory_read_req req = {.key = key, .tier = (melissa_memory_tier)tier};
    const char *value = bridge->cfg.memory_read(bridge->cfg.callback_ctx, &req);
    if (!value) {
        lua_pushnil(L);
    } else {
        lua_pushstring(L, value);
    }
    return 1;
}

static int l_memory_write(lua_State *L) {
    struct melissa_lua_bridge *bridge = get_bridge(L);
    const char *key = luaL_checkstring(L, 1);
    const char *value = luaL_checkstring(L, 2);
    int tier = (int)luaL_checkinteger(L, 3);

    if (!bridge || !bridge->cfg.memory_write) {
        lua_pushboolean(L, 0);
        return 1;
    }

    melissa_memory_write_req req = {.key = key, .value = value, .tier = (melissa_memory_tier)tier};
    int rc = bridge->cfg.memory_write(bridge->cfg.callback_ctx, &req);
    lua_pushboolean(L, rc == 0);
    return 1;
}

int melissa_lua_register_memory(lua_State *L) {
    lua_getglobal(L, "melissa");
    if (!lua_istable(L, -1)) {
        lua_pop(L, 1);
        return -1;
    }

    lua_pushcfunction(L, l_memory_read);
    lua_setfield(L, -2, "memory_read");

    lua_pushcfunction(L, l_memory_write);
    lua_setfield(L, -2, "memory_write");

    lua_pop(L, 1);
    return 0;
}
