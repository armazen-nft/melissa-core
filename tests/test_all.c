#include "../include/melissa.h"

static int passed = 0;
static int failed = 0;

#define ASSERT(cond, msg) do { \
    if (cond) { printf("  [OK] %s\n", msg); passed++; } \
    else { printf("  [FAIL] %s [%s:%d]\n", msg, __FILE__, __LINE__); failed++; } \
} while (0)

static void test_model_init(void)
{
    TernaryModel m;
    MelissaStatus st;

    printf("\n[test_model_init]\n");

    st = model_init(&m, 4, 16, 8, 4);
    ASSERT(st == MELISSA_OK, "init valido retorna OK");
    ASSERT(m.n_layers == 4, "n_layers correto");
    ASSERT(m.hidden_size == 16, "hidden_size correto");
    ASSERT(m.input_size == 8, "input_size correto");
    ASSERT(m.output_size == 4, "output_size correto");

    st = model_init(&m, 0, 16, 8, 4);
    ASSERT(st == MELISSA_INVAL, "layers=0 retorna INVAL");
}

static void test_ternarize(void)
{
    printf("\n[test_ternarize]\n");
    ASSERT(ternarize(1.0f) == 1, "ternarize(1.0) = +1");
    ASSERT(ternarize(-1.0f) == -1, "ternarize(-1.0) = -1");
    ASSERT(ternarize(0.0f) == 0, "ternarize(0.0) = 0");
}

static void test_model_forward(void)
{
    TernaryModel m;
    ternary_t in[MAX_INPUT];
    ternary_t out[MAX_OUTPUT];
    int i;
    int valid;

    printf("\n[test_model_forward]\n");

    model_init(&m, 2, 16, MAX_INPUT, MAX_OUTPUT);
    model_randomize(&m);

    for (i = 0; i < MAX_INPUT; i++) in[i] = (ternary_t)((i % 3) - 1);
    model_forward(&m, in, out);

    valid = 1;
    for (i = 0; i < MAX_OUTPUT; i++) {
        if (out[i] < -1 || out[i] > 1) valid = 0;
    }
    ASSERT(valid, "outputs no intervalo ternario");
}

static void test_model_save_load(void)
{
    TernaryModel m1;
    TernaryModel m2;
    MelissaStatus st;
    const char *path = "/tmp/melissa_test.bin";

    printf("\n[test_model_save_load]\n");

    model_init(&m1, 4, 16, 8, 4);
    model_randomize(&m1);

    st = model_save(&m1, path);
    ASSERT(st == MELISSA_OK, "save retorna OK");

    memset(&m2, 0, sizeof(m2));
    st = model_load(&m2, path);
    ASSERT(st == MELISSA_OK, "load retorna OK");
    ASSERT(m2.n_layers == m1.n_layers, "n_layers preservado");
}

static void test_daizen(void)
{
    DaizenOracle d;
    MelissaStatus st;

    printf("\n[test_daizen]\n");

    st = daizen_init(&d);
    ASSERT(st == MELISSA_OK, "daizen_init OK");
    ASSERT(d.state == 0, "estado inicial repouso");
    ASSERT(daizen_step(&d, 99) >= 0, "step com clamp");
}

int main(void)
{
    printf("Melissa Core - test suite\n");

    test_model_init();
    test_ternarize();
    test_model_forward();
    test_model_save_load();
    test_daizen();

    printf("\nPassou: %d\nFalhou: %d\n", passed, failed);

    return (failed == 0) ? 0 : 1;
}
