#ifndef MELISSA_LUA_BRIDGE_H
#define MELISSA_LUA_BRIDGE_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define MELISSA_LUA_BRIDGE_API_VERSION 1

#define MELISSA_FEIGENBAUM_DELTA 4.66920160910299

typedef enum {
    MELISSA_MEMORY_TIER_SHORT_TERM = 0,
    MELISSA_MEMORY_TIER_LONG_TERM = 1,
    MELISSA_MEMORY_TIER_EPHEMERAL = 2
} melissa_memory_tier;

typedef struct {
    const char *key;
    melissa_memory_tier tier;
} melissa_memory_read_req;

typedef struct {
    const char *key;
    const char *value;
    melissa_memory_tier tier;
} melissa_memory_write_req;

typedef struct {
    const char *model_name;
    const char *prompt;
} melissa_model_infer_req;

typedef struct {
    double delta;
    const char *chunk_context;
} melissa_bifurcation_req;

typedef struct {
    uint64_t executions;
    uint64_t failed_executions;
    uint64_t instruction_limit_hits;
    uint64_t api_version_mismatch;
    uint64_t state_pool_timeouts;
} melissa_lua_bridge_stats;

typedef struct melissa_lua_bridge melissa_lua_bridge;

typedef const char *(*melissa_memory_read_cb)(void *ctx, const melissa_memory_read_req *req);
typedef int (*melissa_memory_write_cb)(void *ctx, const melissa_memory_write_req *req);
typedef const char *(*melissa_model_infer_cb)(void *ctx, const melissa_model_infer_req *req);
typedef int (*melissa_bifurcation_cb)(void *ctx, const melissa_bifurcation_req *req);

typedef struct {
    const char *boot_script_path;
    size_t pool_size;
    int instruction_limit;
    int acquire_timeout_ms;
    melissa_memory_read_cb memory_read;
    melissa_memory_write_cb memory_write;
    melissa_model_infer_cb model_infer;
    melissa_bifurcation_cb bifurcation_hint;
    void *callback_ctx;
} melissa_lua_bridge_config;

melissa_lua_bridge *melissa_lua_bridge_create(const melissa_lua_bridge_config *cfg);
void melissa_lua_bridge_destroy(melissa_lua_bridge *bridge);

int melissa_lua_exec_core(melissa_lua_bridge *bridge,
                          const char *script,
                          const char *entrypoint,
                          const char *payload_json,
                          char *output,
                          size_t output_size);

int melissa_lua_check_api_version(melissa_lua_bridge *bridge,
                                  int required_api_version,
                                  char *errbuf,
                                  size_t errbuf_size);

void melissa_lua_bridge_get_stats(const melissa_lua_bridge *bridge,
                                  melissa_lua_bridge_stats *out_stats);

#ifdef __cplusplus
}
#endif

#endif
