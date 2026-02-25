#include "melissa.h"

static void run_bench(TernaryModel *m)
{
    static ternary_t input[MAX_INPUT];
    static ternary_t output[MAX_OUTPUT];
    int i;
    clock_t t0, t1;
    int n = 10000;
    double elapsed, throughput;

    printf("[bench] %d inferencias...\n", n);

    for (i = 0; i < MAX_INPUT; i++) input[i] = (ternary_t)((i % 3) - 1);

    t0 = clock();
    for (i = 0; i < n; i++) model_forward(m, input, output);
    t1 = clock();

    elapsed = (double)(t1 - t0) / CLOCKS_PER_SEC;
    throughput = (elapsed > 0.0) ? ((double)n / elapsed) : 0.0;

    printf("[bench] %.3f s -> %.0f infer/s\n", elapsed, throughput);
    printf("[bench] latencia media: %.3f ms\n", (elapsed / n) * 1000.0);
}

static void run_interactive(TernaryModel *m, DaizenOracle *d)
{
    char line[128];
    int a, b, symbol, got;
    SymProblem p;
    static ternary_t ctx[MAX_INPUT];

    printf("[melissa] modo interativo. Digite 'sair' para encerrar.\n");
    printf("[melissa] comandos: problema | oraculo N | estado\n\n");

    while (1) {
        printf("melissa> ");
        fflush(stdout);

        if (!fgets(line, sizeof(line), stdin)) break;
        line[strcspn(line, "\n")] = '\0';

        if (strcmp(line, "sair") == 0 || strcmp(line, "exit") == 0) break;

        if (strcmp(line, "problema") == 0) {
            p = problem_generate(1);
            got = problem_solve(&p, m);
            printf("  %d %c %d = %d  (esperado: %d) %s\n",
                   p.a, p.op, p.b, got, p.answer,
                   problem_verify(&p, got) ? "OK" : "FAIL");
        } else if (sscanf(line, "oraculo %d", &symbol) == 1) {
            daizen_step(d, symbol);
            daizen_inject(d, m, ctx, MAX_INPUT);
            daizen_print(d);
        } else if (strcmp(line, "estado") == 0) {
            daizen_print(d);
            model_print_info(m);
        } else if (sscanf(line, "%d + %d", &a, &b) == 2) {
            p.op = '+';
            p.a = a;
            p.b = b;
            p.answer = a + b;
            got = problem_solve(&p, m);
            printf("  modelo diz: %d + %d = %d (correto: %d) %s\n",
                   a, b, got, p.answer,
                   problem_verify(&p, got) ? "OK" : "FAIL");
        } else if (strcmp(line, "help") == 0 || strcmp(line, "?") == 0) {
            printf("  problema       - gera e resolve um problema aleatorio\n");
            printf("  oraculo N      - avanca o Daizen com simbolo N (0-3)\n");
            printf("  estado         - exibe estado do Daizen e modelo\n");
            printf("  A + B          - testa soma (ex: 3 + 5)\n");
            printf("  sair           - encerra\n");
        } else if (strlen(line) > 0) {
            printf("  ? Nao entendi. Digite 'help' para ajuda.\n");
        }
    }

    printf("\n[melissa] encerrando. Ate a proxima.\n\n");
}

void melissa_banner(void)
{
    printf("\nMelissa Core v%d.%d.%d\n", MELISSA_VERSION_MAJOR,
           MELISSA_VERSION_MINOR, MELISSA_VERSION_PATCH);
    printf("IA minima para maquinas esquecidas\n\n");
}

int main(int argc, char *argv[])
{
    TernaryModel model;
    DaizenOracle oracle;
    SelfPlayStats stats;
    MelissaStatus st;
    int epochs;
    int i;

    epochs = 1000;
    melissa_banner();

    st = model_init(&model, 4, MAX_HIDDEN, MAX_INPUT, MAX_OUTPUT);
    if (st != MELISSA_OK) {
        fprintf(stderr, "Erro ao inicializar modelo.\n");
        return 1;
    }

    if (model_load(&model, "melissa.bin") != MELISSA_OK) {
        printf("[melissa] nenhum modelo salvo encontrado. Iniciando do zero.\n");
        model_randomize(&model);
    } else {
        printf("[melissa] modelo carregado de melissa.bin\n");
    }

    daizen_init(&oracle);

    for (i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--info") == 0) {
            model_print_info(&model);
            daizen_print(&oracle);
            return 0;
        }

        if (strcmp(argv[i], "--bench") == 0) {
            run_bench(&model);
            return 0;
        }

        if (strcmp(argv[i], "--train") == 0) {
            if (i + 1 < argc) {
                epochs = atoi(argv[++i]);
                if (epochs < 1) epochs = 1000;
            }
            selfplay_run(&model, epochs, &stats);
            selfplay_print_stats(&stats);
            model_save(&model, "melissa.bin");
            printf("[melissa] modelo salvo em melissa.bin\n");
            return 0;
        }
    }

    run_interactive(&model, &oracle);
    model_save(&model, "melissa.bin");
    printf("[melissa] modelo salvo.\n");

    return 0;
}
