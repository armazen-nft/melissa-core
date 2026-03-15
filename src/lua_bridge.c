#include "lua_bridge.h"

#include "bindings/bifurcation.h"
#include "bindings/memory.h"
#include "bindings/model.h"
#include "lua_bridge_internal.h"
#include "lua_state_pool.h"

#include <lauxlib.h>
#include <lualib.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void instruction_hook(lua_State *L, lua_Debug *ar) {
    (void)ar;
    int *counter = (int *)lua_getextraspace(L);
    (*counter)--;
    if (*counter <= 0) {
        luaL_error(L, "instruction limit exceeded");
    }
}

static int open_sandbox(lua_State *L) {
    luaL_requiref(L, "_G", luaopen_base, 1);
    lua_pop(L, 1);

    luaL_requiref(L, LUA_MATHLIBNAME, luaopen_math, 1);
    lua_pop(L, 1);
    luaL_requiref(L, LUA_STRLIBNAME, luaopen_string, 1);
    lua_pop(L, 1);
    luaL_requiref(L, LUA_TABLIBNAME, luaopen_table, 1);
    lua_pop(L, 1);
    luaL_requiref(L, LUA_UTF8LIBNAME, luaopen_utf8, 1);
    lua_pop(L, 1);

    const char *blocked[] = {"load", "loadfile", "dofile", "collectgarbage", "require", NULL};
    for (int i = 0; blocked[i]; i++) {
        lua_pushnil(L);
        lua_setglobal(L, blocked[i]);
    }

    lua_newtable(L);
    lua_setglobal(L, "io");
    lua_newtable(L);
    lua_setglobal(L, "os");
    lua_newtable(L);
    lua_setglobal(L, "package");
    lua_newtable(L);
    lua_setglobal(L, "debug");
    return 0;
}

static int load_file(lua_State *L, const char *path) {
    if (luaL_loadfile(L, path) != LUA_OK) {
        return -1;
    }
    if (lua_pcall(L, 0, 0, 0) != LUA_OK) {
        return -1;
    }
    return 0;
}

static lua_State *new_state(struct melissa_lua_bridge *bridge) {
    lua_State *L = luaL_newstate();
    if (!L) {
        return NULL;
    }

    if (open_sandbox(L) != 0) {
        lua_close(L);
        return NULL;
    }

    lua_pushlightuserdata(L, bridge);
    lua_setfield(L, LUA_REGISTRYINDEX, "__melissa_bridge");

    lua_newtable(L);
    lua_pushnumber(L, MELISSA_FEIGENBAUM_DELTA);
    lua_setfield(L, -2, "FEIGENBAUM_DELTA");
    lua_pushinteger(L, MELISSA_MEMORY_TIER_SHORT_TERM);
    lua_setfield(L, -2, "MEM_SHORT_TERM");
    lua_pushinteger(L, MELISSA_MEMORY_TIER_LONG_TERM);
    lua_setfield(L, -2, "MEM_LONG_TERM");
    lua_pushinteger(L, MELISSA_MEMORY_TIER_EPHEMERAL);
    lua_setfield(L, -2, "MEM_EPHEMERAL");
    lua_setglobal(L, "melissa");

    if (melissa_lua_register_memory(L) != 0 ||
        melissa_lua_register_model(L) != 0 ||
        melissa_lua_register_bifurcation(L) != 0) {
        lua_close(L);
        return NULL;
    }

    if (bridge->cfg.boot_script_path && load_file(L, bridge->cfg.boot_script_path) != 0) {
        lua_close(L);
        return NULL;
    }
    return L;
}

melissa_lua_bridge *melissa_lua_bridge_create(const melissa_lua_bridge_config *cfg) {
    if (!cfg || cfg->pool_size == 0 || cfg->instruction_limit <= 0) {
        return NULL;
    }

    melissa_lua_bridge *bridge = calloc(1, sizeof(*bridge));
    if (!bridge) {
        return NULL;
    }
    bridge->cfg = *cfg;
    bridge->pool = lua_state_pool_create(cfg->pool_size);
    if (!bridge->pool) {
        free(bridge);
        return NULL;
    }

    for (size_t i = 0; i < cfg->pool_size; ++i) {
        lua_State *L = new_state(bridge);
        if (!L) {
            melissa_lua_bridge_destroy(bridge);
            return NULL;
        }
        lua_state_pool_release(bridge->pool, L);
    }
    return bridge;
}

void melissa_lua_bridge_destroy(melissa_lua_bridge *bridge) {
    if (!bridge) {
        return;
    }

    lua_State *L = NULL;
    while (lua_state_pool_acquire(bridge->pool, 1, &L) == 0) {
        lua_close(L);
    }
    lua_state_pool_destroy(bridge->pool);
    free(bridge);
}

int melissa_lua_check_api_version(melissa_lua_bridge *bridge,
                                  int required_api_version,
                                  char *errbuf,
                                  size_t errbuf_size) {
    if (!bridge) {
        return -1;
    }
    if (required_api_version == MELISSA_LUA_BRIDGE_API_VERSION) {
        return 0;
    }
    bridge->stats.api_version_mismatch++;
    if (errbuf && errbuf_size > 0) {
        snprintf(errbuf, errbuf_size, "required_api_version=%d current=%d", required_api_version,
                 MELISSA_LUA_BRIDGE_API_VERSION);
    }
    return -1;
}

int melissa_lua_exec_core(melissa_lua_bridge *bridge,
                          const char *script,
                          const char *entrypoint,
                          const char *payload_json,
                          char *output,
                          size_t output_size) {
    if (!bridge || !script || !entrypoint || !output || output_size == 0) {
        return -1;
    }

    lua_State *L = NULL;
    if (lua_state_pool_acquire(bridge->pool, bridge->cfg.acquire_timeout_ms, &L) != 0) {
        bridge->stats.state_pool_timeouts++;
        return -1;
    }

    bridge->stats.executions++;
    int *counter = (int *)lua_getextraspace(L);
    *counter = bridge->cfg.instruction_limit;
    lua_sethook(L, instruction_hook, LUA_MASKCOUNT, 1);

    int rc = 0;
    if (luaL_loadstring(L, script) != LUA_OK || lua_pcall(L, 0, 0, 0) != LUA_OK) {
        bridge->stats.failed_executions++;
        rc = -1;
        goto done;
    }

    lua_getglobal(L, entrypoint);
    if (!lua_isfunction(L, -1)) {
        bridge->stats.failed_executions++;
        rc = -1;
        goto done;
    }

    lua_pushstring(L, payload_json ? payload_json : "{}");
    if (lua_pcall(L, 1, 1, 0) != LUA_OK) {
        if (strstr(lua_tostring(L, -1), "instruction limit exceeded")) {
            bridge->stats.instruction_limit_hits++;
        }
        bridge->stats.failed_executions++;
        rc = -1;
        goto done;
    }

    const char *result = lua_tostring(L, -1);
    if (!result) {
        result = "";
    }
    snprintf(output, output_size, "%s", result);

    lua_getglobal(L, "_required_api_version");
    if (lua_isnumber(L, -1)) {
        int req = (int)lua_tointeger(L, -1);
        if (melissa_lua_check_api_version(bridge, req, NULL, 0) != 0) {
            rc = -1;
        }
    }
    lua_pop(L, 1);

done:
    lua_sethook(L, NULL, 0, 0);
    lua_settop(L, 0);
    lua_state_pool_release(bridge->pool, L);
    return rc;
}

void melissa_lua_bridge_get_stats(const melissa_lua_bridge *bridge,
                                  melissa_lua_bridge_stats *out_stats) {
    if (!bridge || !out_stats) {
        return;
    }
    *out_stats = bridge->stats;
}
