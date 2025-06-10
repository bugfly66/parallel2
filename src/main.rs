use rayon::prelude::*;
use rand::Rng;
use std::time::Instant;

// 串行矩阵乘法
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
fn mat_mul_parallel(a: &[f64], b: &[f64], c: &mut [f64], n: usize) {
    c.par_chunks_mut(n)
        .enumerate()
        .for_each(|(i, c_row)| {
            for k in 0..n {
                let a_ik = a[i * n + k];
                for j in 0..n {
                    c_row[j] += a_ik * b[k * n + j];
                }
            }
        });
}

// 生成随机矩阵
fn random_matrix(n: usize) -> Vec<f64> {
    let mut rng = rand::rng();
    (0..n*n).map(|_| rng.random_range(0.0..1.0)).collect()
}
// 验证结果是否相同
fn verify_result(a: &[f64], b: &[f64], n: usize) -> bool {
    for i in 0..n {
        for j in 0..n {
            let idx = i * n + j;
            if (a[idx] - b[idx]).abs() > 1e-5 {
                println!("Mismatch at ({}, {}): {:.6} vs {:.6}", 
                         i, j, a[idx], b[idx]);
                return false;
            }
        }
    }
    true
}

fn main() {
    let sizes = vec![64, 128, 256, 512, 1024]; // 测试不同矩阵尺寸
    
    for &n in &sizes {
        println!("\n测试矩阵大小: {}x{}", n, n);
        
        // 生成随机矩阵
        let a = random_matrix(n);
        let b = random_matrix(n);
        let mut c_serial = vec![0.0; n * n];
        let mut c_parallel = vec![0.0; n * n];
        
        // 测试串行版本
        let start = Instant::now();
        mat_mul_serial(&a, &b, &mut c_serial, n);
        let serial_duration = start.elapsed();
        
        // 测试并行版本
        let start = Instant::now();
        mat_mul_parallel(&a, &b, &mut c_parallel, n);
        let parallel_duration = start.elapsed();
        
        // 验证结果
        println!("结果验证: {}",
            if verify_result(&c_serial, &c_parallel, n) {
                "成功"
            } else {
                "失败! 结果不一致"
            }
        );
        
        // 输出性能数据
        println!("串行耗时: {:.3}ms", serial_duration.as_millis());
        println!("并行耗时: {:.3}ms", parallel_duration.as_millis());
        println!("加速比: {:.2}x", 
                 serial_duration.as_secs_f64() / parallel_duration.as_secs_f64());
    }
}