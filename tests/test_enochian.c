#include <assert.h>
#include <stdio.h>

#include "melissa.h"
#include "enochian/enochian_bridge.h"

static void fill_model(TernaryModel *model)
{
    int i;
    memset(model, 0, sizeof(*model));
    model->n_layers = 1;
    model->hidden_size = 4;
    model->input_size = 4;
    model->output_size = 2;
    for (i = 0; i < 4; ++i) {
        model->weights[0][0][i] = (ternary_t)((i % 3) - 1);
    }
}

int main(void)
{
    TernaryModel model;
    SelfPlayStats stats;
    EnochianToken token;
    EnochianToken parsed;
    EnochianToken mutated;
    EnochianToken resolved;
    EnochianConsensus consensus;
    EnochianEvolution evolution;
    MelissaEnochianState state;
    char buffer[160];

    fill_model(&model);
    memset(&stats, 0, sizeof(stats));
    stats.wins = 9;
    stats.losses = 2;
    stats.total = 11;
    stats.accuracy = 0.72f;
    stats.epoch = 14;

    assert(melissa_enochian_token_from_state(&model, &stats, "arithmetic", &token) == MELISSA_OK);
    assert(token.context_len == 4);
    assert(token.checksum == enochian_token_checksum(&token));

    assert(enochian_token_to_string(&token, buffer, sizeof(buffer)) == MELISSA_OK);
    assert(enochian_token_from_string(buffer, &parsed) == MELISSA_OK);
    assert(strcmp(parsed.glyph, token.glyph) == 0);
    assert(strcmp(parsed.domain, token.domain) == 0);

    enochian_consensus_init(&consensus);
    assert(enochian_consensus_add(&consensus, &token) == MELISSA_OK);
    assert(enochian_consensus_add(&consensus, &parsed) == MELISSA_OK);
    assert(melissa_enochian_selfplay_consensus(&stats, &consensus, &resolved) == MELISSA_OK);
    assert(resolved.checksum == enochian_token_checksum(&resolved));

    enochian_evolution_init(&evolution, 7u);
    assert(enochian_evolution_mutate(&evolution, &token, &mutated) == MELISSA_OK);
    assert(mutated.checksum == enochian_token_checksum(&mutated));

    memset(&state, 0, sizeof(state));
    assert(melissa_enochian_apply_token(&state, &mutated) == MELISSA_OK);
    assert(state.verified_tokens == 1);
    assert(state.justice_bias >= mutated.ethic);

    puts("test_enochian: ok");
    return 0;
}
