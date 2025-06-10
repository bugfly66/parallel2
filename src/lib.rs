#![feature(test)]

extern crate test;
#[allow(unused)]
use lazy_static::lazy_static;
use libc::{c_double, c_int};
use rand::Rng;
use rayon::prelude::*;
use std::sync::{Arc, Mutex};
use std::thread;
unsafe extern "C" {
    // 串行版本函数
    #[allow(unused)]
    fn c_serial_sum(n: c_int) -> c_double;
    // OpenMP 并行版本函数
    #[allow(unused)]
    fn c_parallel_sum(n: c_int) -> c_double;
    #[allow(unused)]
    fn c_mat_mul_serial(a: *const c_double, b: *const c_double, c: *mut c_double, n: c_int);
    #[allow(unused)]
    fn c_mat_mul_parallel(a: *const c_double, b: *const c_double, c: *mut c_double, n: c_int);
}
// 计算和的函数（安全版本）
#[allow(unused)]
fn calculate_sum(n: usize, num_threads: usize) -> f64 {
    // 使用不会溢出的计算函数
    fn compute_term(i: usize) -> f64 {
        (i as f64).ln() / (i as f64)
    }

    // 创建线程句柄容器
    let mut handles = Vec::with_capacity(num_threads);
    // 使用局部变量替代互斥锁
    let results = Arc::new(Mutex::new(vec![0.0; num_threads]));

    // 计算每个线程的任务范围
    let chunk_size = (n + num_threads - 1) / num_threads; // 向上取整除法

    for thread_id in 0..num_threads {
        let results_clone = Arc::clone(&results);
        let start = thread_id * chunk_size + 1;
        let end = usize::min((thread_id + 1) * chunk_size, n);

        // 跳过空范围（当n很小时）
        if start > end {
            continue;
        }

        handles.push(thread::spawn(move || {
            let mut local_sum = 0.0;
            for j in start..=end {
                local_sum += compute_term(j);
            }

            // 仅在线程结束时更新一次结果
            let mut res = results_clone.lock().unwrap();
            res[thread_id] = local_sum;
        }));
    }

    // 等待所有线程完成
    for handle in handles {
        handle.join().unwrap();
    }

    // 汇总结果（不需要互斥锁，因为所有线程已结束）
    let results = results.lock().unwrap();
    results.iter().sum()
}
// 串行矩阵乘法
#[allow(unused)]
fn mat_mul_serial(a: &[f64], b: &[f64], c: &mut [f64], n: usize) {
    for i in 0..n {
        for k in 0..n {
            let a_ik = a[i * n + k];
            for j in 0..n {
                c[i * n + j] += a_ik * b[k * n + j];
            }
        }
    }
}

// 并行矩阵乘法 (Rayon)
#[allow(unused)]
fn mat_mul_parallel(a: &[f64], b: &[f64], c: &mut [f64], n: usize) {
    c.par_chunks_mut(n).enumerate().for_each(|(i, c_row)| {
        for k in 0..n {
            let a_ik = a[i * n + k];
            for j in 0..n {
                c_row[j] += a_ik * b[k * n + j];
            }
        }
    });
}

// 生成随机矩阵
#[allow(unused)]
fn random_matrix(n: usize) -> Vec<f64> {
    let mut rng = rand::rng();
    (0..n * n).map(|_| rng.random_range(0.0..1.0)).collect()
}
// 验证结果是否相同
#[allow(unused)]
fn verify_result(a: &[f64], b: &[f64], n: usize) -> bool {
    for i in 0..n {
        for j in 0..n {
            let idx = i * n + j;
            if (a[idx] - b[idx]).abs() > 1e-5 {
                println!("Mismatch at ({}, {}): {:.6} vs {:.6}", i, j, a[idx], b[idx]);
                return false;
            }
        }
    }
    true
}
#[allow(unused)]
fn parallel_sum(n: usize) -> f64 {
    (1..=n)
        .into_par_iter()
        .map(|i| (i as f64).ln() / i as f64)
        .sum()
}

// 串行版本
#[allow(unused)]
fn serial_sum(n: usize) -> f64 {
    (1..=n).map(|i| (i as f64).ln() / (i as f64)).sum()
}

#[cfg(test)]
mod tests {
    use super::*;
    use test::Bencher;

    include!("len.rs"); // 引入动态生成的 len.rs 文件
    lazy_static! {
        static ref RANDOM_MAT_A: Vec<f64> = random_matrix(MLEN);
        static ref RANDOM_MAT_B: Vec<f64> = random_matrix(MLEN);
    }
    #[test]
    fn test_mul_matrix() {
        // assert!(verify_result(&RANDOM_MAT_A, &RANDOM_MAT_A, MLEN
        // assert!(verify_result(&RANDOM_MAT_B, &RANDOM_MAT_B, MLEN));
        let mut resc1 = vec![0.; LEN * LEN];
        mat_mul_serial(&RANDOM_MAT_A, &RANDOM_MAT_B, &mut &mut resc1, MLEN);
        let mut resc2 = vec![0.; LEN * LEN];
        mat_mul_parallel(&RANDOM_MAT_A, &RANDOM_MAT_B, &mut &mut resc2, MLEN);
        assert!(verify_result(&resc1, &resc2, MLEN));
        unsafe {
            c_mat_mul_serial(
                RANDOM_MAT_A.as_ptr(),
                RANDOM_MAT_B.as_ptr(),
                resc1.as_mut_ptr(),
                MLEN.try_into().unwrap(),
            );
        }
        unsafe {
            c_mat_mul_parallel(
                RANDOM_MAT_A.as_ptr(),
                RANDOM_MAT_B.as_ptr(),
                resc2.as_mut_ptr(),
                MLEN.try_into().unwrap(),
            );
        }
        assert!(verify_result(&resc1, &resc2, MLEN));
    }
    /// 测试矩阵乘法结果
    #[test]
    fn test_sum() {
        let sum_parallel = unsafe { c_parallel_sum(LEN.try_into().unwrap()) };
        let sum_serial = unsafe { c_serial_sum(LEN.try_into().unwrap()) };
        // 检查结果 浮点数计算有误差所以将其控制为1e-6
        assert!((sum_parallel - sum_serial).abs() < 1e-6);
        let sum_parallel = parallel_sum(LEN);
        //测试c语言实现的rust实现的答案是否一样
        assert!((sum_parallel - sum_serial).abs() < 1e-6);
        let sum_serial = serial_sum(LEN);
        assert!((sum_parallel - sum_serial).abs() < 1e-6);
    }
    /// 测试矩阵乘法
    #[test]
    fn test_mat_mul000() { 
        let a = vec![1.0; 3*3];
        let b = vec![2.0; 3*3];
        let mut c = vec![0.0;3*3];
        mat_mul_serial(&a, &b, &mut c, 3);
        assert!(  c == vec![6.0; 3*3]  );}
    // 基准测试函数
    #[bench]
    fn thread16_sum(b: &mut Bencher) {
        b.iter(|| {
            // 使用黑盒包装来防止优化
            test::black_box(calculate_sum(LEN, 16));
        });
    }
    #[bench]
    fn thread1_sum(b: &mut Bencher) {
        b.iter(|| {
            // 使用黑盒包装来防止优化
            test::black_box(calculate_sum(LEN, 1));
        });
    }
    #[bench]
    fn thread4_sum(b: &mut Bencher) {
        b.iter(|| {
            // 使用黑盒包装来防止优化
            test::black_box(calculate_sum(LEN, 4));
        });
    }

    #[bench]
    fn benchmark_parallel_sum(b: &mut Bencher) {
        b.iter(|| {
            test::black_box(parallel_sum(LEN));
        });
    }
    #[bench]
    fn benchmark_serial_sum(b: &mut Bencher) {
        b.iter(|| {
            test::black_box(serial_sum(LEN));
        });
    }
    #[bench]
    fn benchmark_c_serial_sum(b: &mut Bencher) {
        b.iter(|| {
            test::black_box(unsafe { c_serial_sum(LEN.try_into().unwrap()) });
        });
    }
    #[bench]
    fn benchmark_c_parallel_sum(b: &mut Bencher) {
        b.iter(|| {
            test::black_box(unsafe { c_parallel_sum(LEN.try_into().unwrap()) });
        });
    }
    #[bench]
    fn benchmarkc_c_mat_mul_parallel(b: &mut Bencher) {
        let mut c = vec![0.0; MLEN * MLEN];
        b.iter(|| {
            test::black_box(unsafe {
                c_mat_mul_parallel(
                    RANDOM_MAT_A.as_ptr(),
                    RANDOM_MAT_B.as_ptr(),
                    c.as_mut_ptr(),
                    MLEN.try_into().unwrap(),
                )
            });
        });
    }
    #[bench]
    fn benchmarkc_c_mat_mul_serial(b: &mut Bencher) {
        let mut c = vec![0.0; MLEN * MLEN];
        b.iter(|| {
            test::black_box(unsafe {
                c_mat_mul_serial(
                    RANDOM_MAT_A.as_ptr(),
                    RANDOM_MAT_B.as_ptr(),
                    c.as_mut_ptr(),
                    MLEN.try_into().unwrap(),
                )
            });
        });
    }
    #[bench]
    fn benchmark_mat_mul_serial(b: &mut Bencher) {
        let mut c = vec![0.0; MLEN * MLEN];
        b.iter(|| {
            test::black_box(mat_mul_serial(&RANDOM_MAT_A, &RANDOM_MAT_B, &mut c, MLEN));
        });
    }
    #[bench]
    fn benchmark_mat_mul_parallel(b: &mut Bencher) {
        let mut c = vec![0.0; MLEN * MLEN];
        b.iter(|| {
            test::black_box(mat_mul_parallel(&RANDOM_MAT_A, &RANDOM_MAT_B, &mut c, MLEN));
        });
    }
}
