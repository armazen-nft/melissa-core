#ifndef MELISSA_H
#define MELISSA_H

/* ================================================================
 * melissa.h — Núcleo de tipos e constantes
 * Projetado para rodar em <1GB RAM, sem FPU, sem libs externas.
 * Arquiteturas-alvo: ARMv6, PowerPC, MIPS, x86 legado.
 * ================================================================ */

#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

/* ── Versão ────────────────────────────────────────────────────── */
#define MELISSA_VERSION_MAJOR 0
#define MELISSA_VERSION_MINOR 1
#define MELISSA_VERSION_PATCH 0

/* ── Limites de memória ─────────────────────────────────────────── */
#define MAX_LAYERS        8
#define MAX_HIDDEN       64
#define MAX_INPUT        16
#define MAX_OUTPUT        8
#define MAX_WEIGHTS   (MAX_HIDDEN * MAX_HIDDEN * MAX_LAYERS)

/* ── Tipos ternários ─────────────────────────────────────────────── */
typedef int8_t  ternary_t;
typedef int32_t accum_t;

/* ── Modelo ternário (BitNet-lite) ───────────────────────────────── */
typedef struct {
    ternary_t weights[MAX_LAYERS][MAX_HIDDEN][MAX_HIDDEN];
    int8_t    bias[MAX_LAYERS][MAX_HIDDEN];
    int       n_layers;
    int       hidden_size;
    int       input_size;
    int       output_size;
} TernaryModel;

/* ── Estado do self-play ─────────────────────────────────────────── */
typedef struct {
    int     wins;
    int     losses;
    int     total;
    float   accuracy;
    int     epoch;
} SelfPlayStats;

/* ── Problema simbólico ──────────────────────────────────────────── */
typedef struct {
    int   a;
    int   b;
    char  op;
    int   answer;
} SymProblem;

/* ── Oráculo Daizen ──────────────────────────────────────────────── */
#define DAIZEN_STATES    8
#define DAIZEN_SYMBOLS   4

typedef struct {
    int     state;
    int     transitions[DAIZEN_STATES][DAIZEN_SYMBOLS];
    char    labels[DAIZEN_STATES][16];
    float   confidence[DAIZEN_STATES];
} DaizenOracle;

/* ── Resultado genérico ──────────────────────────────────────────── */
typedef enum {
    MELISSA_OK     =  0,
    MELISSA_ERR    = -1,
    MELISSA_NOMEM  = -2,
    MELISSA_INVAL  = -3
} MelissaStatus;

/* ── Macros utilitárias ──────────────────────────────────────────── */
#define SIGN(x)      ((x) > 0 ? 1 : ((x) < 0 ? -1 : 0))
#define CLAMP(x,a,b) ((x)<(a)?(a):((x)>(b)?(b):(x)))
#define MIN(a,b)     ((a)<(b)?(a):(b))
#define MAX(a,b)     ((a)>(b)?(a):(b))

/* melissa_model.c */
MelissaStatus model_init(TernaryModel *m, int layers, int hidden,
                         int input_size, int output_size);
void          model_randomize(TernaryModel *m);
MelissaStatus model_save(const TernaryModel *m, const char *path);
MelissaStatus model_load(TernaryModel *m, const char *path);
void          model_print_info(const TernaryModel *m);

/* melissa_inference.c */
ternary_t     ternarize(float x);
void          layer_forward(const ternary_t *in,
                            ternary_t *out,
                            const ternary_t weights[][MAX_HIDDEN],
                            const int8_t *bias,
                            int dim);
void          model_forward(const TernaryModel *m,
                            const ternary_t *input,
                            ternary_t *output);

/* melissa_selfplay.c */
SymProblem    problem_generate(int difficulty);
int           problem_solve(const SymProblem *p, const TernaryModel *m);
int           problem_verify(const SymProblem *p, int answer);
void          selfplay_run(TernaryModel *m, int epochs, SelfPlayStats *stats);
void          selfplay_update(TernaryModel *m, float reward);
void          selfplay_print_stats(const SelfPlayStats *s);

/* daizen_core.c */
MelissaStatus daizen_init(DaizenOracle *d);
int           daizen_step(DaizenOracle *d, int symbol);
const char   *daizen_label(const DaizenOracle *d);
void          daizen_inject(DaizenOracle *d, const TernaryModel *m,
                            ternary_t *context, int ctx_len);
void          daizen_print(const DaizenOracle *d);

/* melissa_main.c */
void          melissa_banner(void);

#endif
