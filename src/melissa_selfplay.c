#include "melissa.h"

#define DIFF_EASY   1
#define DIFF_MEDIUM 2
#define DIFF_HARD   3

SymProblem problem_generate(int difficulty)
{
    SymProblem p;
    memset(&p, 0, sizeof(p));

    switch (difficulty) {
    case DIFF_MEDIUM:
        p.op = '*';
        p.a = (rand() % 7) + 1;
        p.b = (rand() % 7) + 1;
        p.answer = p.a * p.b;
        break;
    case DIFF_HARD:
        p.op = '-';
        p.a = (rand() % 16) + 1;
        p.b = (rand() % 16) + 1;
        p.answer = p.a - p.b;
        break;
    case DIFF_EASY:
    default:
        p.op = '+';
        p.a = (rand() % 9) + 1;
        p.b = (rand() % 9) + 1;
        p.answer = p.a + p.b;
        break;
    }

    return p;
}

static void problem_encode(const SymProblem *p, ternary_t *vec, int vec_len)
{
    int i;
    memset(vec, 0, (size_t)vec_len * sizeof(ternary_t));
    if (vec_len < 4) return;

    vec[0] = SIGN(p->a - 8);
    vec[1] = SIGN(p->b - 8);

    switch (p->op) {
    case '+': vec[2] = 1;  vec[3] = 0;  break;
    case '-': vec[2] = 0;  vec[3] = -1; break;
    case '*': vec[2] = -1; vec[3] = 1;  break;
    default:  vec[2] = 0;  vec[3] = 0;  break;
    }

    for (i = 4; i < vec_len; i++) vec[i] = (ternary_t)((i % 3) - 1);
}

static int output_decode(const ternary_t *out, int out_len)
{
    int i;
    int val = 0;
    int weight = 1;

    for (i = 0; i < out_len; i++) {
        val += (int)out[i] * weight;
        weight = weight * 2;
    }

    return val;
}

int problem_solve(const SymProblem *p, const TernaryModel *m)
{
    static ternary_t input[MAX_INPUT];
    static ternary_t output[MAX_OUTPUT];

    problem_encode(p, input, m->input_size);
    model_forward(m, input, output);
    return output_decode(output, m->output_size);
}

int problem_verify(const SymProblem *p, int answer)
{
    return (answer == p->answer) ? 1 : 0;
}

void selfplay_update(TernaryModel *m, float reward)
{
    int l, i, j;
    int mutate_prob;

    if (!m) return;

    mutate_prob = (reward > 0.0f) ? 2 : 5;

    for (l = 0; l < m->n_layers; l++) {
        for (i = 0; i < m->hidden_size; i++) {
            for (j = 0; j < m->hidden_size; j++) {
                if ((rand() % 100) < mutate_prob) {
                    if (reward <= 0.0f) {
                        m->weights[l][i][j] = (ternary_t)((rand() % 3) - 1);
                    }
                }
            }
        }
    }
}

static void log_result(const SymProblem *p, int got, int correct, int epoch)
{
    FILE *f = fopen("selfplay.log", "a");
    if (!f) return;

    fprintf(f, "epoch=%d op=%c a=%d b=%d expected=%d got=%d %s\n",
            epoch, p->op, p->a, p->b, p->answer, got,
            correct ? "OK" : "FAIL");

    fclose(f);
}

void selfplay_run(TernaryModel *m, int epochs, SelfPlayStats *stats)
{
    int e, difficulty, got, correct;
    SymProblem p;
    float reward;

    if (!m || !stats) return;

    memset(stats, 0, sizeof(SelfPlayStats));
    printf("[selfplay] iniciando %d epocas...\n", epochs);

    for (e = 0; e < epochs; e++) {
        stats->epoch = e;

        if (e < epochs / 3) difficulty = DIFF_EASY;
        else if (e < 2 * epochs / 3) difficulty = DIFF_MEDIUM;
        else difficulty = DIFF_HARD;

        p = problem_generate(difficulty);
        got = problem_solve(&p, m);
        correct = problem_verify(&p, got);

        reward = correct ? 1.0f : -1.0f;
        selfplay_update(m, reward);

        stats->total++;
        if (correct) stats->wins++;
        else stats->losses++;

        log_result(&p, got, correct, e);

        if ((e + 1) % 100 == 0) {
            stats->accuracy = (float)stats->wins / (float)stats->total;
            printf("[selfplay] epoca %4d/%d - acuracia: %.1f%%\n",
                   e + 1, epochs, stats->accuracy * 100.0f);
        }
    }

    stats->accuracy = (float)stats->wins / (float)stats->total;
}

void selfplay_print_stats(const SelfPlayStats *s)
{
    if (!s) return;

    printf("\n=== Self-Play Stats ===\n");
    printf("  epocas   : %d\n", s->total);
    printf("  acertos  : %d\n", s->wins);
    printf("  erros    : %d\n", s->losses);
    printf("  acuracia : %.2f%%\n", s->accuracy * 100.0f);
    printf("=======================\n\n");
}
