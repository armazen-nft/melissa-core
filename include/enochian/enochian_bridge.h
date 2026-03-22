#ifndef ENOCHIAN_BRIDGE_H
#define ENOCHIAN_BRIDGE_H

#include "enochian_consensus.h"
#include "enochian_evolution.h"

typedef struct {
    int exploration_bias;
    int justice_bias;
    int sustain_bias;
    int verified_tokens;
} MelissaEnochianState;

MelissaStatus melissa_enochian_token_from_state(const TernaryModel *model,
                                                const SelfPlayStats *stats,
                                                const char *domain,
                                                EnochianToken *token);
MelissaStatus melissa_enochian_apply_token(MelissaEnochianState *state,
                                           const EnochianToken *token);
MelissaStatus melissa_enochian_selfplay_consensus(const SelfPlayStats *stats,
                                                  const EnochianConsensus *consensus,
                                                  EnochianToken *resolved);

#endif /* ENOCHIAN_BRIDGE_H */
