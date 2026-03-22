#include "enochian/enochian_evolution.h"

static unsigned int enochian_lcg(unsigned int *state)
{
    *state = (*state * 1103515245u) + 12345u;
    return *state;
}

void enochian_evolution_init(EnochianEvolution *evolution, unsigned int seed)
{
    if (!evolution) {
        return;
    }
    evolution->generation = 0;
    evolution->seed = seed ? seed : 1u;
}

MelissaStatus enochian_evolution_mutate(EnochianEvolution *evolution,
                                        const EnochianToken *source,
                                        EnochianToken *mutated)
{
    unsigned int value;
    int slot;

    if (!evolution || !source || !mutated) {
        return MELISSA_INVAL;
    }

    *mutated = *source;
    evolution->generation++;

    value = enochian_lcg(&evolution->seed);
    mutated->phase = (int)(value % 7u) - 3;

    value = enochian_lcg(&evolution->seed);
    mutated->flux += (int)(value % 5u) - 2;

    value = enochian_lcg(&evolution->seed);
    mutated->ethic = CLAMP(mutated->ethic + ((int)(value % 3u) - 1), 0, 9);

    value = enochian_lcg(&evolution->seed);
    slot = (int)(value % ENOCHIAN_MAX_CONTEXT_LEN);
    mutated->context[slot] = (ternary_t)((value % 3u) - 1);
    if (mutated->context_len < ENOCHIAN_MAX_CONTEXT_LEN) {
        mutated->context_len++;
    }

    enochian_token_finalize(mutated);
    return MELISSA_OK;
}
