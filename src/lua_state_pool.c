#include "lua_state_pool.h"

#include <pthread.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

struct lua_state_pool {
    lua_State **states;
    size_t size;
    size_t available;
    pthread_mutex_t mutex;
    pthread_cond_t cond;
};

lua_state_pool *lua_state_pool_create(size_t size) {
    if (size == 0) {
        return NULL;
    }

    lua_state_pool *pool = calloc(1, sizeof(*pool));
    if (!pool) {
        return NULL;
    }

    pool->states = calloc(size, sizeof(lua_State *));
    if (!pool->states) {
        free(pool);
        return NULL;
    }

    pool->size = size;
    pool->available = 0;
    pthread_mutex_init(&pool->mutex, NULL);
    pthread_cond_init(&pool->cond, NULL);
    return pool;
}

void lua_state_pool_destroy(lua_state_pool *pool) {
    if (!pool) {
        return;
    }
    pthread_cond_destroy(&pool->cond);
    pthread_mutex_destroy(&pool->mutex);
    free(pool->states);
    free(pool);
}

int lua_state_pool_acquire(lua_state_pool *pool, int timeout_ms, lua_State **out_state) {
    if (!pool || !out_state) {
        return -1;
    }

    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    ts.tv_sec += timeout_ms / 1000;
    ts.tv_nsec += (long)(timeout_ms % 1000) * 1000000L;
    if (ts.tv_nsec >= 1000000000L) {
        ts.tv_sec += 1;
        ts.tv_nsec -= 1000000000L;
    }

    pthread_mutex_lock(&pool->mutex);
    while (pool->available == 0) {
        int rc = pthread_cond_timedwait(&pool->cond, &pool->mutex, &ts);
        if (rc != 0) {
            pthread_mutex_unlock(&pool->mutex);
            return -1;
        }
    }

    *out_state = pool->states[--pool->available];
    pool->states[pool->available] = NULL;
    pthread_mutex_unlock(&pool->mutex);
    return 0;
}

void lua_state_pool_release(lua_state_pool *pool, lua_State *L) {
    if (!pool || !L) {
        return;
    }

    pthread_mutex_lock(&pool->mutex);
    if (pool->available < pool->size) {
        pool->states[pool->available++] = L;
        pthread_cond_signal(&pool->cond);
    }
    pthread_mutex_unlock(&pool->mutex);
}
