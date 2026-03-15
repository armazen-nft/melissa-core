#ifndef MELISSA_LUA_STATE_POOL_H
#define MELISSA_LUA_STATE_POOL_H

#include <stddef.h>
#include <lua.h>

typedef struct lua_state_pool lua_state_pool;

lua_state_pool *lua_state_pool_create(size_t size);
void lua_state_pool_destroy(lua_state_pool *pool);
int lua_state_pool_acquire(lua_state_pool *pool, int timeout_ms, lua_State **out_state);
void lua_state_pool_release(lua_state_pool *pool, lua_State *L);

#endif
