#ifndef ENOCHIAN_EVOLUTION_H
#define ENOCHIAN_EVOLUTION_H

#include "enochian_token.h"

typedef struct {
    unsigned int generation;
    unsigned int seed;
} EnochianEvolution;

void enochian_evolution_init(EnochianEvolution *evolution, unsigned int seed);
MelissaStatus enochian_evolution_mutate(EnochianEvolution *evolution,
                                        const EnochianToken *source,
                                        EnochianToken *mutated);

#endif /* ENOCHIAN_EVOLUTION_H */
