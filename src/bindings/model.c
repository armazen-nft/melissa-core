#include "model.h"

#include "lua_bridge.h"
#include "../lua_bridge_internal.h"

#include <lauxlib.h>

static struct melissa_lua_bridge *get_bridge(lua_State *L) {
    lua_getfield(L, LUA_REGISTRYINDEX, "__melissa_bridge");
    struct melissa_lua_bridge *bridge = lua_touserdata(L, -1);
    lua_pop(L, 1);
    return bridge;
}

static int l_model_infer(lua_State *L) {
    struct melissa_lua_bridge *bridge = get_bridge(L);
    const char *model_name = luaL_checkstring(L, 1);
    const char *prompt = luaL_checkstring(L, 2);

    if (!bridge || !bridge->cfg.model_infer) {
        lua_pushnil(L);
        return 1;
    }

    melissa_model_infer_req req = {.model_name = model_name, .prompt = prompt};
    const char *resp = bridge->cfg.model_infer(bridge->cfg.callback_ctx, &req);
    if (!resp) {
        lua_pushnil(L);
    } else {
        lua_pushstring(L, resp);
    }
    return 1;
}

int melissa_lua_register_model(lua_State *L) {
    lua_getglobal(L, "melissa");
    if (!lua_istable(L, -1)) {
        lua_pop(L, 1);
        return -1;
    }

    lua_pushcfunction(L, l_model_infer);
    lua_setfield(L, -2, "model_infer");

    lua_pop(L, 1);
    return 0;
}
