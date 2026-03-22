#include "enochian/enochian_consensus.h"

void enochian_consensus_init(EnochianConsensus *consensus)
{
    if (!consensus) {
        return;
    }
    memset(consensus, 0, sizeof(*consensus));
}

MelissaStatus enochian_consensus_add(EnochianConsensus *consensus,
                                     const EnochianToken *token)
{
    if (!consensus || !token) {
        return MELISSA_INVAL;
    }
    if (consensus->count >= ENOCHIAN_MAX_VOTES) {
        return MELISSA_ERR;
    }

    consensus->votes[consensus->count++] = *token;
    return MELISSA_OK;
}

MelissaStatus enochian_consensus_resolve(const EnochianConsensus *consensus,
                                         EnochianToken *resolved)
{
    int i;
    int best_index = 0;
    int best_score = -1;

    if (!consensus || !resolved || consensus->count <= 0) {
        return MELISSA_INVAL;
    }

    for (i = 0; i < consensus->count; ++i) {
        int j;
        int score = 0;
        for (j = 0; j < consensus->count; ++j) {
            if (strcmp(consensus->votes[i].glyph, consensus->votes[j].glyph) == 0) {
                score += 2;
            }
            if (strcmp(consensus->votes[i].domain, consensus->votes[j].domain) == 0) {
                score += 1;
            }
            if (consensus->votes[i].ethic == consensus->votes[j].ethic) {
                score += 1;
            }
        }
        if (score > best_score) {
            best_score = score;
            best_index = i;
        }
    }

    *resolved = consensus->votes[best_index];
    return MELISSA_OK;
}
