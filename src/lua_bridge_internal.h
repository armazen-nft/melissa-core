#ifndef MELISSA_LUA_BRIDGE_INTERNAL_H
#define MELISSA_LUA_BRIDGE_INTERNAL_H

#include "lua_bridge.h"

struct melissa_lua_bridge {
    melissa_lua_bridge_config cfg;
    struct lua_state_pool *pool;
    melissa_lua_bridge_stats stats;
};

#endif
