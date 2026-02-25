CC      = gcc

SRC_DIR  = src
INC_DIR  = include
BIN_DIR  = bin
OBJ_DIR  = obj
TEST_DIR = tests

SRCS     = $(SRC_DIR)/melissa_model.c \
           $(SRC_DIR)/melissa_inference.c \
           $(SRC_DIR)/melissa_selfplay.c \
           $(SRC_DIR)/daizen_core.c \
           $(SRC_DIR)/melissa_main.c

OBJS     = $(patsubst $(SRC_DIR)/%.c,$(OBJ_DIR)/%.o,$(SRCS))
TARGET   = $(BIN_DIR)/melissa

CFLAGS_BASE = -std=c89 -Wall -Wextra -Wpedantic -I$(INC_DIR) -D_POSIX_C_SOURCE=200112L
CFLAGS_DEBUG = $(CFLAGS_BASE) -g -O0 -DMELISSA_DEBUG
CFLAGS_RELEASE = $(CFLAGS_BASE) -O2 -DNDEBUG -fomit-frame-pointer -ffunction-sections -fdata-sections

LDFLAGS_RELEASE = -Wl,--gc-sections
LDFLAGS =
CFLAGS = $(CFLAGS_DEBUG)

CC_ARM  = arm-linux-gnueabi-gcc
CC_PPC  = powerpc-linux-gnu-gcc
CC_MIPS = mipsel-linux-gnu-gcc

CFLAGS_ARM  = $(CFLAGS_RELEASE) -march=armv6 -mfloat-abi=soft -static
CFLAGS_PPC  = $(CFLAGS_RELEASE) -mcpu=7400 -msoft-float -static
CFLAGS_MIPS = $(CFLAGS_RELEASE) -march=mips32 -msoft-float -EL -static

.PHONY: all release arm ppc mips all-arch train bench clean size help test

all: $(TARGET)

release: CFLAGS = $(CFLAGS_RELEASE)
release: LDFLAGS = $(LDFLAGS_RELEASE)
release: $(TARGET)

$(TARGET): $(OBJS) | $(BIN_DIR)
	$(CC) $(OBJS) -o $@ $(LDFLAGS) -lm
	@echo "  LD  $@"

$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c | $(OBJ_DIR)
	$(CC) $(CFLAGS) -c $< -o $@
	@echo "  CC  $<"

$(BIN_DIR) $(OBJ_DIR):
	mkdir -p $@

arm: | $(BIN_DIR)
	$(CC_ARM) $(CFLAGS_ARM) $(SRCS) -o $(BIN_DIR)/melissa_arm -lm

ppc: | $(BIN_DIR)
	$(CC_PPC) $(CFLAGS_PPC) $(SRCS) -o $(BIN_DIR)/melissa_ppc -lm

mips: | $(BIN_DIR)
	$(CC_MIPS) $(CFLAGS_MIPS) $(SRCS) -o $(BIN_DIR)/melissa_mips -lm

all-arch: arm ppc mips

N ?= 1000

train: all
	$(TARGET) --train $(N)

bench: all
	$(TARGET) --bench

info: all
	$(TARGET) --info

test:
	$(CC) $(CFLAGS_BASE) -I$(INC_DIR) $(TEST_DIR)/test_all.c \
		$(SRC_DIR)/melissa_model.c $(SRC_DIR)/melissa_inference.c \
		$(SRC_DIR)/melissa_selfplay.c $(SRC_DIR)/daizen_core.c -o $(BIN_DIR)/test_all -lm
	$(BIN_DIR)/test_all

clean:
	rm -rf $(OBJ_DIR) $(BIN_DIR)
	rm -f melissa.bin selfplay.log

size: all
	size $(TARGET) 2>/dev/null || ls -lh $(TARGET)

help:
	@echo "make | release | arm | ppc | mips | all-arch | train N=5000 | bench | info | test | clean"
