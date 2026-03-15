CC ?= gcc
AR ?= ar
CFLAGS ?= -O2 -Wall -Wextra -std=c99 -Iinclude -Ilua_bridge -Ideps/lua/src

LUA_SRC_DIR := deps/lua/src
LUA_CORE_SRCS := $(filter-out $(LUA_SRC_DIR)/lua.c $(LUA_SRC_DIR)/luac.c,$(wildcard $(LUA_SRC_DIR)/*.c))
LUA_CORE_OBJS := $(LUA_CORE_SRCS:.c=.o)

CORE_SRCS := src/melissa_tokenizer.c lua_bridge/lua_bridge.c
CORE_OBJS := $(CORE_SRCS:.c=.o)

.PHONY: all clean check-lua-sources

all: check-lua-sources libmelissa_core.a liblua.a

check-lua-sources:
	@test -f $(LUA_SRC_DIR)/lua.h || (echo "Erro: fontes Lua ausentes em $(LUA_SRC_DIR)." && echo "Veja deps/lua/README.md para instruções." && exit 1)

liblua.a: $(LUA_CORE_OBJS)
	$(AR) rcs $@ $^

libmelissa_core.a: $(CORE_OBJS)
	$(AR) rcs $@ $^

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(CORE_OBJS) $(LUA_CORE_OBJS) libmelissa_core.a liblua.a
