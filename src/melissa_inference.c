#include "melissa.h"

ternary_t ternarize(float x)
{
    if (x > 0.33f) return 1;
    if (x < -0.33f) return -1;
    return 0;
}

static ternary_t ternarize_int(accum_t x, int dim)
{
    float norm = (float)x / (float)(dim > 0 ? dim : 1);
    return ternarize(norm);
}

static ternary_t relu_ternary(ternary_t x)
{
    return (x > 0) ? 1 : 0;
}

void layer_forward(const ternary_t *in,
                   ternary_t *out,
                   const ternary_t weights[][MAX_HIDDEN],
                   const int8_t *bias,
                   int dim)
{
    int i, j;
    accum_t sum;

    for (i = 0; i < dim; i++) {
        sum = (accum_t)bias[i];
        for (j = 0; j < dim; j++) {
            ternary_t w = weights[i][j];
            if (w > 0) sum += (accum_t)in[j];
            else if (w < 0) sum -= (accum_t)in[j];
        }
        out[i] = relu_ternary(ternarize_int(sum, dim));
    }
}

void model_forward(const TernaryModel *m,
                   const ternary_t *input,
                   ternary_t *output)
{
    static ternary_t buf_a[MAX_HIDDEN];
    static ternary_t buf_b[MAX_HIDDEN];
    ternary_t *cur;
    ternary_t *next;
    ternary_t *tmp;
    int l, i;

    if (!m || !input || !output) return;

    cur = buf_a;
    next = buf_b;

    memset(buf_a, 0, sizeof(buf_a));
    memset(buf_b, 0, sizeof(buf_b));

    for (i = 0; i < MIN(m->input_size, m->hidden_size); i++) cur[i] = input[i];

    for (l = 0; l < m->n_layers; l++) {
        memset(next, 0, sizeof(buf_a));
        layer_forward(cur,
                      next,
                      (const ternary_t (*)[MAX_HIDDEN])m->weights[l],
                      m->bias[l],
                      m->hidden_size);
        tmp = cur;
        cur = next;
        next = tmp;
    }

    memset(output, 0, (size_t)m->output_size * sizeof(ternary_t));
    for (i = 0; i < MIN(m->output_size, m->hidden_size); i++) output[i] = cur[i];
}
