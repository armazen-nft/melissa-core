#ifndef ENOCHIAN_CONSENSUS_H
#define ENOCHIAN_CONSENSUS_H

#include "enochian_token.h"

#define ENOCHIAN_MAX_VOTES 8

typedef struct {
    EnochianToken votes[ENOCHIAN_MAX_VOTES];
    int count;
    int agreement_score;
} EnochianConsensus;

void enochian_consensus_init(EnochianConsensus *consensus);
MelissaStatus enochian_consensus_add(EnochianConsensus *consensus,
                                     const EnochianToken *token);
MelissaStatus enochian_consensus_resolve(const EnochianConsensus *consensus,
                                         EnochianToken *resolved);

#endif /* ENOCHIAN_CONSENSUS_H */
