#include "enochian/enochian_token.h"

static void enochian_copy_text(char *dst, size_t dst_size, const char *src)
{
    size_t i = 0;

    if (!dst || dst_size == 0) {
        return;
    }

    if (!src) {
        dst[0] = '\0';
        return;
    }

    while (src[i] && i + 1 < dst_size) {
        dst[i] = src[i];
        i++;
    }
    dst[i] = '\0';
}

void enochian_token_init(EnochianToken *token)
{
    int i;

    if (!token) {
        return;
    }

    memset(token, 0, sizeof(*token));
    enochian_copy_text(token->glyph, sizeof(token->glyph), "Tok-Pa");
    enochian_copy_text(token->domain, sizeof(token->domain), "general");
    for (i = 0; i < ENOCHIAN_MAX_CONTEXT_LEN; ++i) {
        token->context[i] = 0;
    }
}

unsigned int enochian_token_checksum(const EnochianToken *token)
{
    unsigned int hash = 2166136261u;
    int i;
    const unsigned char *p;

    if (!token) {
        return 0;
    }

    p = (const unsigned char *)token->glyph;
    while (*p) {
        hash ^= *p++;
        hash *= 16777619u;
    }

    p = (const unsigned char *)token->domain;
    while (*p) {
        hash ^= *p++;
        hash *= 16777619u;
    }

    hash ^= (unsigned int)(token->phase + 257);
    hash *= 16777619u;
    hash ^= (unsigned int)(token->flux + 263);
    hash *= 16777619u;
    hash ^= (unsigned int)(token->ethic + 269);
    hash *= 16777619u;

    for (i = 0; i < token->context_len && i < ENOCHIAN_MAX_CONTEXT_LEN; ++i) {
        hash ^= (unsigned int)(token->context[i] + 3);
        hash *= 16777619u;
    }

    return hash;
}

void enochian_token_finalize(EnochianToken *token)
{
    if (!token) {
        return;
    }

    token->checksum = enochian_token_checksum(token);
}

MelissaStatus enochian_token_to_string(const EnochianToken *token,
                                       char *buffer,
                                       size_t buffer_size)
{
    int written;

    if (!token || !buffer || buffer_size == 0) {
        return MELISSA_INVAL;
    }

    written = snprintf(buffer,
                       buffer_size,
                       "%s[domain=%s,phase=%d,flux=%d,ethic=%d,ctx=%d,checksum=%u]",
                       token->glyph,
                       token->domain,
                       token->phase,
                       token->flux,
                       token->ethic,
                       token->context_len,
                       token->checksum);
    if (written < 0 || (size_t)written >= buffer_size) {
        return MELISSA_ERR;
    }
    return MELISSA_OK;
}

MelissaStatus enochian_token_from_string(const char *text,
                                         EnochianToken *token)
{
    char glyph[ENOCHIAN_MAX_SYMBOL_LEN];
    char domain[ENOCHIAN_MAX_DOMAIN_LEN];
    int phase;
    int flux;
    int ethic;
    int ctx_len;
    unsigned int checksum;
    int matched;

    if (!text || !token) {
        return MELISSA_INVAL;
    }

    matched = sscanf(text,
                     "%15[^[][%*[^=]=%15[^,],phase=%d,flux=%d,ethic=%d,ctx=%d,checksum=%u]",
                     glyph,
                     domain,
                     &phase,
                     &flux,
                     &ethic,
                     &ctx_len,
                     &checksum);
    if (matched != 7) {
        return MELISSA_ERR;
    }

    enochian_token_init(token);
    enochian_copy_text(token->glyph, sizeof(token->glyph), glyph);
    enochian_copy_text(token->domain, sizeof(token->domain), domain);
    token->phase = phase;
    token->flux = flux;
    token->ethic = ethic;
    token->context_len = CLAMP(ctx_len, 0, ENOCHIAN_MAX_CONTEXT_LEN);
    token->checksum = checksum;

    return MELISSA_OK;
}
