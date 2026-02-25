#include "melissa.h"

/* =============================================================================
   Tokenizador texto → sequência ternária (100% offline, zero malloc, C89)
   Ideal para: linha de comando "oraculo Qual é o sentido da vida?"
   ============================================================================= */

/* Converte string para vetor de ternários (-1, 0, +1) */
void text_to_ternary(const char *text, ternary_t *out, int max_len, int *out_len)
{
    int i = 0, j = 0;

    if (out_len) {
        *out_len = 0;
    }

    if (!text || !out || !out_len || max_len < 1) {
        return;
    }

    while (text[i] && j < max_len) {
        unsigned char c = (unsigned char)text[i];
        /* Simple hash cíclico que gera -1, 0, +1 de forma determinística */
        ternary_t t = (ternary_t)((c % 3) - 1);

        /* Ignora espaços e pontuação para não poluir */
        if (c > 32 && c < 127) {
            out[j++] = t;
        }
        i++;
    }
    *out_len = j;
}

/* Converte texto direto para símbolo Daizen (0-3) – útil em CLI */
int string_to_daizen_symbol(const char *text)
{
    unsigned int hash = 0;
    const char *p = text;

    if (!text) {
        return 0;
    }

    while (*p) {
        hash = (hash * 31 + (unsigned char)*p++) % DAIZEN_SYMBOLS;
    }
    return (int)hash;
}

/* Exemplo de uso futuro no main:
   ternary_t ctx[MAX_INPUT];
   int len;
   text_to_ternary("Qual é o sentido da vida?", ctx, MAX_INPUT, &len);
   model_forward(&model, ctx, output);
*/
