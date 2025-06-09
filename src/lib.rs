#![feature(test)]


extern crate test;
use rayon::prelude::*;
use std::sync::{Arc, Mutex};
use std::thread;

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
    let chunk_size = (n + num_threads - 1) / num_threads;  // 向上取整除法

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
#[allow(unused)]
fn parallel_sum(n: usize) -> f64 {
    (1..=n).into_par_iter().map(|i| (i as f64).ln() / i as f64).sum()
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
//    const LEN:usize = 100;
    include!("len.rs"); // 引入动态生成的 len.rs 文件

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
    fn benchmark_parallel_sum(b: &mut Bencher){
        b.iter(||{
            test::black_box(parallel_sum(LEN));
        });
    }
    #[bench]
    fn benchmark_serial_sum(b: &mut Bencher){
        b.iter(||{
            test::black_box(serial_sum(LEN));
        });
    }

}

