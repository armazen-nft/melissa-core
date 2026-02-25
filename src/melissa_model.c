#include "melissa.h"

static ternary_t rand_ternary(void)
{
    int r = rand() % 3;
    return (ternary_t)(r - 1);
}

MelissaStatus model_init(TernaryModel *m, int layers, int hidden,
                         int input_size, int output_size)
{
    if (!m) return MELISSA_INVAL;
    if (layers < 1 || layers > MAX_LAYERS) return MELISSA_INVAL;
    if (hidden < 1 || hidden > MAX_HIDDEN) return MELISSA_INVAL;
    if (input_size < 1 || input_size > MAX_INPUT) return MELISSA_INVAL;
    if (output_size < 1 || output_size > MAX_OUTPUT) return MELISSA_INVAL;

    memset(m, 0, sizeof(*m));
    m->n_layers = layers;
    m->hidden_size = hidden;
    m->input_size = input_size;
    m->output_size = output_size;

    return MELISSA_OK;
}

void model_randomize(TernaryModel *m)
{
    int l, i, j;

    if (!m) return;
    srand((unsigned int)time(NULL));

    for (l = 0; l < m->n_layers; l++) {
        for (i = 0; i < m->hidden_size; i++) {
            m->bias[l][i] = (int8_t)rand_ternary();
            for (j = 0; j < m->hidden_size; j++) {
                m->weights[l][i][j] = rand_ternary();
            }
        }
    }
}

MelissaStatus model_save(const TernaryModel *m, const char *path)
{
    FILE *f;

    if (!m || !path) return MELISSA_INVAL;
    f = fopen(path, "wb");
    if (!f) return MELISSA_ERR;

    if (fwrite(m, sizeof(*m), 1, f) != 1) {
        fclose(f);
        return MELISSA_ERR;
    }

    fclose(f);
    return MELISSA_OK;
}

MelissaStatus model_load(TernaryModel *m, const char *path)
{
    FILE *f;

    if (!m || !path) return MELISSA_INVAL;
    f = fopen(path, "rb");
    if (!f) return MELISSA_ERR;

    if (fread(m, sizeof(*m), 1, f) != 1) {
        fclose(f);
        return MELISSA_ERR;
    }

    fclose(f);

    if (m->n_layers < 1 || m->n_layers > MAX_LAYERS) return MELISSA_ERR;
    if (m->hidden_size < 1 || m->hidden_size > MAX_HIDDEN) return MELISSA_ERR;
    if (m->input_size < 1 || m->input_size > MAX_INPUT) return MELISSA_ERR;
    if (m->output_size < 1 || m->output_size > MAX_OUTPUT) return MELISSA_ERR;

    return MELISSA_OK;
}

void model_print_info(const TernaryModel *m)
{
    long weights;

    if (!m) return;
    weights = (long)m->n_layers * m->hidden_size * m->hidden_size;

    printf("[model] layers=%d hidden=%d input=%d output=%d\n",
           m->n_layers, m->hidden_size, m->input_size, m->output_size);
    printf("[model] weights=%ld (~%ld bytes)\n",
           weights, weights * (long)sizeof(ternary_t));
}
