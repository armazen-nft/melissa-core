#include "bifurcation.h"

#include "lua_bridge.h"
#include "../lua_bridge_internal.h"

#include <lauxlib.h>
#include <math.h>

static struct melissa_lua_bridge *get_bridge(lua_State *L) {
    lua_getfield(L, LUA_REGISTRYINDEX, "__melissa_bridge");
    struct melissa_lua_bridge *bridge = lua_touserdata(L, -1);
    lua_pop(L, 1);
    return bridge;
}

static int l_bifurcation_hint(lua_State *L) {
    struct melissa_lua_bridge *bridge = get_bridge(L);
    double delta = luaL_checknumber(L, 1);
    const char *ctx = luaL_optstring(L, 2, "");

    if (fabs(delta - MELISSA_FEIGENBAUM_DELTA) > 0.2) {
        lua_pushboolean(L, 0);
        lua_pushstring(L, "delta_out_of_range");
        return 2;
    }

    if (!bridge || !bridge->cfg.bifurcation_hint) {
        lua_pushboolean(L, 1);
        return 1;
    }

    melissa_bifurcation_req req = {.delta = delta, .chunk_context = ctx};
    int rc = bridge->cfg.bifurcation_hint(bridge->cfg.callback_ctx, &req);
    lua_pushboolean(L, rc == 0);
    return 1;
}

int melissa_lua_register_bifurcation(lua_State *L) {
    lua_getglobal(L, "melissa");
    if (!lua_istable(L, -1)) {
        lua_pop(L, 1);
        return -1;
    }

    lua_pushcfunction(L, l_bifurcation_hint);
    lua_setfield(L, -2, "bifurcation_hint");

    lua_pop(L, 1);
    return 0;
}
