#ifndef ENOCHIAN_TOKEN_H
#define ENOCHIAN_TOKEN_H

#include "../melissa.h"

#define ENOCHIAN_MAX_SYMBOL_LEN 16
#define ENOCHIAN_MAX_DOMAIN_LEN 16
#define ENOCHIAN_MAX_CONTEXT_LEN 16

typedef struct {
    char      glyph[ENOCHIAN_MAX_SYMBOL_LEN];
    char      domain[ENOCHIAN_MAX_DOMAIN_LEN];
    int       phase;
    int       flux;
    int       ethic;
    ternary_t context[ENOCHIAN_MAX_CONTEXT_LEN];
    int       context_len;
    unsigned int checksum;
} EnochianToken;

void enochian_token_init(EnochianToken *token);
void enochian_token_finalize(EnochianToken *token);
unsigned int enochian_token_checksum(const EnochianToken *token);
MelissaStatus enochian_token_to_string(const EnochianToken *token,
                                       char *buffer,
                                       size_t buffer_size);
MelissaStatus enochian_token_from_string(const char *text,
                                         EnochianToken *token);

#endif /* ENOCHIAN_TOKEN_H */
