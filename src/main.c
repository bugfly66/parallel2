#include <math.h>
#include <omp.h>
#include <string.h>
// 串行版本
double c_serial_sum(int n) {
    double sum = 0.0;
    for (int i = 1; i <= n; i++) {
        sum += log((double)i) / (double)i;
    }
    return sum;
}

// OpenMP并行版本
double c_parallel_sum(int n) {
    double sum = 0.0;
    #pragma omp parallel for reduction(+:sum)
    for (int i = 1; i <= n; i++) {
        sum += log((double)i) / (double)i;
    }
    return sum;
}

// 串行矩阵乘法
void c_mat_mul_serial(const double *a, const double *b, double *c, int n) {
    memset(c, 0, n * n * sizeof(double));
    for (int i = 0; i < n; i++) {
        for (int k = 0; k < n; k++) {
            double a_ik = a[i * n + k];
            for (int j = 0; j < n; j++) {
                c[i * n + j] += a_ik * b[k * n + j];
            }
        }
    }
}

// 并行矩阵乘法 (OpenMP)
void c_mat_mul_parallel(const double *a, const double *b, double *c, int n) {
    memset(c, 0, n * n * sizeof(double));
    #pragma omp parallel for
    for (int i = 0; i < n; i++) {
        for (int k = 0; k < n; k++) {
            double a_ik = a[i * n + k];
            for (int j = 0; j < n; j++) {
                c[i * n + j] += a_ik * b[k * n + j];
            }
        }
    }
}
