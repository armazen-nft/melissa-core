#include "enochian/enochian_bridge.h"

static int melissa_sum_context(const ternary_t *context, int len)
{
    int i;
    int sum = 0;

    for (i = 0; i < len; ++i) {
        sum += context[i];
    }
    return sum;
}

MelissaStatus melissa_enochian_token_from_state(const TernaryModel *model,
                                                const SelfPlayStats *stats,
                                                const char *domain,
                                                EnochianToken *token)
{
    int i;
    int limit;

    if (!model || !stats || !token) {
        return MELISSA_INVAL;
    }

    enochian_token_init(token);
    if (domain && *domain) {
        strncpy(token->domain, domain, sizeof(token->domain) - 1);
        token->domain[sizeof(token->domain) - 1] = '\0';
    }

    token->phase = CLAMP(stats->wins - stats->losses, -9, 9);
    token->flux = CLAMP((stats->epoch % 10) + model->hidden_size, 0, 99);
    token->ethic = CLAMP((int)(stats->accuracy * 10.0f), 0, 9);

    limit = MIN(model->input_size, ENOCHIAN_MAX_CONTEXT_LEN);
    for (i = 0; i < limit; ++i) {
        token->context[i] = model->weights[0][0][i];
    }
    token->context_len = limit;
    enochian_token_finalize(token);
    return MELISSA_OK;
}

MelissaStatus melissa_enochian_apply_token(MelissaEnochianState *state,
                                           const EnochianToken *token)
{
    int context_sum;

    if (!state || !token) {
        return MELISSA_INVAL;
    }

    context_sum = melissa_sum_context(token->context, token->context_len);
    state->exploration_bias += token->phase + context_sum;
    state->justice_bias += token->ethic;
    state->sustain_bias += token->flux > 5 ? 1 : 0;
    state->verified_tokens += token->checksum == enochian_token_checksum(token) ? 1 : 0;

    return MELISSA_OK;
}

MelissaStatus melissa_enochian_selfplay_consensus(const SelfPlayStats *stats,
                                                  const EnochianConsensus *consensus,
                                                  EnochianToken *resolved)
{
    MelissaStatus status;

    if (!stats || !consensus || !resolved) {
        return MELISSA_INVAL;
    }

    status = enochian_consensus_resolve(consensus, resolved);
    if (status != MELISSA_OK) {
        return status;
    }

    resolved->ethic = CLAMP(resolved->ethic + (int)(stats->accuracy * 2.0f), 0, 9);
    resolved->phase = CLAMP(resolved->phase + (stats->wins - stats->losses), -9, 9);
    enochian_token_finalize(resolved);
    return MELISSA_OK;
}
