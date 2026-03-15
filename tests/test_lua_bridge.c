#include "lua_bridge.h"

#include <stdio.h>
#include <string.h>

#define ASSERT_TRUE(x) do { if (!(x)) return __LINE__; } while (0)

typedef struct {
    char last_key[64];
    char last_val[128];
    int bifurcation_calls;
} cb_ctx;

static const char *memory_read_cb(void *ctx, const melissa_memory_read_req *req) {
    (void)ctx;
    if (strcmp(req->key, "route_seed") == 0) return "alpha";
    return NULL;
}

static int memory_write_cb(void *ctx, const melissa_memory_write_req *req) {
    cb_ctx *c = (cb_ctx *)ctx;
    snprintf(c->last_key, sizeof(c->last_key), "%s", req->key);
    snprintf(c->last_val, sizeof(c->last_val), "%s", req->value);
    return 0;
}

static const char *model_infer_cb(void *ctx, const melissa_model_infer_req *req) {
    (void)ctx;
    (void)req;
    return "model-ok";
}

static int bifurcation_cb(void *ctx, const melissa_bifurcation_req *req) {
    cb_ctx *c = (cb_ctx *)ctx;
    c->bifurcation_calls++;
    return (req->delta > 4.0) ? 0 : -1;
}

static melissa_lua_bridge *mk_bridge(cb_ctx *ctx) {
    melissa_lua_bridge_config cfg = {
        .boot_script_path = "scripts/boot.lua",
        .pool_size = 2,
        .instruction_limit = 20000,
        .acquire_timeout_ms = 100,
        .memory_read = memory_read_cb,
        .memory_write = memory_write_cb,
        .model_infer = model_infer_cb,
        .bifurcation_hint = bifurcation_cb,
        .callback_ctx = ctx,
    };
    return melissa_lua_bridge_create(&cfg);
}

static int test_exec_basic(void) {
    cb_ctx ctx = {0};
    melissa_lua_bridge *b = mk_bridge(&ctx);
    ASSERT_TRUE(b != NULL);
    char out[256] = {0};
    ASSERT_TRUE(melissa_lua_exec_core(b, "function run(p) return 'ok:'..p end", "run", "x", out, sizeof(out)) == 0);
    ASSERT_TRUE(strcmp(out, "ok:x") == 0);
    melissa_lua_bridge_destroy(b);
    return 0;
}

static int test_sandbox(void) {
    cb_ctx ctx = {0};
    melissa_lua_bridge *b = mk_bridge(&ctx);
    ASSERT_TRUE(b != NULL);
    char out[128] = {0};
    ASSERT_TRUE(melissa_lua_exec_core(b, "function run(_) if os.execute then return 'bad' end return 'safe' end", "run", "{}", out, sizeof(out)) == 0);
    ASSERT_TRUE(strcmp(out, "safe") == 0);
    melissa_lua_bridge_destroy(b);
    return 0;
}

static int test_instruction_limit(void) {
    cb_ctx ctx = {0};
    melissa_lua_bridge *b = mk_bridge(&ctx);
    ASSERT_TRUE(b != NULL);
    char out[64] = {0};
    int rc = melissa_lua_exec_core(b, "function run(_) while true do end return 'n' end", "run", "{}", out, sizeof(out));
    ASSERT_TRUE(rc != 0);
    melissa_lua_bridge_stats s;
    melissa_lua_bridge_get_stats(b, &s);
    ASSERT_TRUE(s.instruction_limit_hits >= 1);
    melissa_lua_bridge_destroy(b);
    return 0;
}

static int test_memory(void) {
    cb_ctx ctx = {0};
    melissa_lua_bridge *b = mk_bridge(&ctx);
    ASSERT_TRUE(b != NULL);
    char out[64] = {0};
    ASSERT_TRUE(melissa_lua_exec_core(b, "function run(_) melissa.memory_write('k','v',0) return melissa.memory_read('route_seed',1) end", "run", "{}", out, sizeof(out)) == 0);
    ASSERT_TRUE(strcmp(out, "alpha") == 0);
    ASSERT_TRUE(strcmp(ctx.last_key, "k") == 0);
    melissa_lua_bridge_destroy(b);
    return 0;
}

static int test_model(void) {
    cb_ctx ctx = {0};
    melissa_lua_bridge *b = mk_bridge(&ctx);
    ASSERT_TRUE(b != NULL);
    char out[64] = {0};
    ASSERT_TRUE(melissa_lua_exec_core(b, "function run(_) return melissa.model_infer('m','p') end", "run", "{}", out, sizeof(out)) == 0);
    ASSERT_TRUE(strcmp(out, "model-ok") == 0);
    melissa_lua_bridge_destroy(b);
    return 0;
}

static int test_bifurcation(void) {
    cb_ctx ctx = {0};
    melissa_lua_bridge *b = mk_bridge(&ctx);
    ASSERT_TRUE(b != NULL);
    char out[64] = {0};
    ASSERT_TRUE(melissa_lua_exec_core(b, "function run(_) return tostring(melissa.bifurcation_hint(4.66,'chunk')) end", "run", "{}", out, sizeof(out)) == 0);
    ASSERT_TRUE(strcmp(out, "true") == 0);
    ASSERT_TRUE(ctx.bifurcation_calls == 1);
    melissa_lua_bridge_destroy(b);
    return 0;
}

static int test_api_version(void) {
    cb_ctx ctx = {0};
    melissa_lua_bridge *b = mk_bridge(&ctx);
    ASSERT_TRUE(b != NULL);
    char out[64] = {0};
    ASSERT_TRUE(melissa_lua_exec_core(b, "_required_api_version=999; function run(_) return 'x' end", "run", "{}", out, sizeof(out)) != 0);
    melissa_lua_bridge_stats s;
    melissa_lua_bridge_get_stats(b, &s);
    ASSERT_TRUE(s.api_version_mismatch >= 1);
    melissa_lua_bridge_destroy(b);
    return 0;
}

int main(void) {
    int (*tests[])(void) = {
        test_exec_basic,
        test_sandbox,
        test_instruction_limit,
        test_memory,
        test_model,
        test_bifurcation,
        test_api_version,
    };

    const char *names[] = {
        "exec_basic",
        "sandbox",
        "instruction_limit",
        "memory",
        "model",
        "bifurcation",
        "api_version",
    };

    for (size_t i = 0; i < sizeof(tests) / sizeof(tests[0]); ++i) {
        int rc = tests[i]();
        if (rc != 0) {
            fprintf(stderr, "FAIL %s at line %d\n", names[i], rc);
            return 1;
        }
        printf("OK %s\n", names[i]);
    }
    return 0;
}
