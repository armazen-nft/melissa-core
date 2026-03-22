CC ?= gcc
CFLAGS ?= -std=c99 -Wall -Wextra -Werror -pedantic -Iinclude

ENOCHIAN_SRCS = \
	src/melissa_tokenizer.c \
	src/enochian/enochian_token.c \
	src/enochian/enochian_consensus.c \
	src/enochian/enochian_evolution.c \
	src/enochian/enochian_bridge.c

.PHONY: all test enochian clean

all: enochian

enochian: test_enochian

test_enochian: tests/test_enochian.c $(ENOCHIAN_SRCS)
	$(CC) $(CFLAGS) -o $@ tests/test_enochian.c $(ENOCHIAN_SRCS)

test: test_enochian
	./test_enochian

clean:
	rm -f test_enochian
