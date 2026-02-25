#include "melissa.h"

static const int DEFAULT_TRANSITIONS[DAIZEN_STATES][DAIZEN_SYMBOLS] = {
    { 0, 1, 7, 5 },
    { 0, 2, 5, 3 },
    { 1, 3, 5, 2 },
    { 2, 4, 6, 3 },
    { 0, 6, 5, 4 },
    { 7, 2, 5, 1 },
    { 0, 1, 7, 6 },
    { 0, 1, 7, 0 }
};

static const char *DEFAULT_LABELS[DAIZEN_STATES] = {
    "repouso", "atencao", "analise", "sintese",
    "resposta", "duvida", "reforco", "silencio"
};

static const float DEFAULT_CONFIDENCE[DAIZEN_STATES] = {
    0.9f, 0.7f, 0.6f, 0.5f,
    0.8f, 0.3f, 0.75f, 0.95f
};

MelissaStatus daizen_init(DaizenOracle *d)
{
    int s, sym;

    if (!d) return MELISSA_INVAL;

    d->state = 0;

    for (s = 0; s < DAIZEN_STATES; s++) {
        d->confidence[s] = DEFAULT_CONFIDENCE[s];
        strncpy(d->labels[s], DEFAULT_LABELS[s], 15);
        d->labels[s][15] = '\0';

        for (sym = 0; sym < DAIZEN_SYMBOLS; sym++) {
            d->transitions[s][sym] = DEFAULT_TRANSITIONS[s][sym];
        }
    }

    return MELISSA_OK;
}

int daizen_step(DaizenOracle *d, int symbol)
{
    if (!d) return -1;

    symbol = CLAMP(symbol, 0, DAIZEN_SYMBOLS - 1);
    d->state = d->transitions[d->state][symbol];
    d->state = CLAMP(d->state, 0, DAIZEN_STATES - 1);

    return d->state;
}

const char *daizen_label(const DaizenOracle *d)
{
    if (!d) return "?";
    return d->labels[d->state];
}

void daizen_inject(DaizenOracle *d,
                   const TernaryModel *m,
                   ternary_t *context,
                   int ctx_len)
{
    int i, state_bits;
    float conf;

    if (!d || !context || ctx_len < 3) return;

    memset(context, 0, (size_t)ctx_len * sizeof(ternary_t));

    state_bits = d->state;
    conf = d->confidence[d->state];

    context[0] = (state_bits > 3) ? -1 : 1;
    context[1] = (conf > 0.7f) ? 1 : ((conf > 0.4f) ? 0 : -1);

    for (i = 2; i < MIN(ctx_len, 2 + DAIZEN_STATES); i++) {
        int bit = (state_bits >> (i - 2)) & 1;
        context[i] = (ternary_t)(bit ? 1 : -1);
    }

    (void)m;
}

void daizen_print(const DaizenOracle *d)
{
    if (!d) return;
    printf("[daizen] estado=%d (%s) confianca=%.2f\n",
           d->state,
           d->labels[d->state],
           d->confidence[d->state]);
}
