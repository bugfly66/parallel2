import subprocess
import os
import re
import matplotlib.pyplot as plt
import numpy as np

# 定义两组不同的测试规模
sum_len_values = [
    # 小规模（并行开销明显区域）
    10, 20, 50, 100, 
    
    # 中小规模（并行开始有效区域）
    200, 400, 700, 1000, 
    
    # 中等规模（典型并行加速区域）
    2000, 3000, 5000, 7000,
    
    # 大规模（并行效率稳定区域）
    10000, 15000, 20000, 30000, 
    
    # 超大规模（系统极限测试）
    50000, 75000, 100000,
]

mat_len_values = [
    # 小矩阵（并行开销明显区域）
    10, 20, 50, 
    
    # 中等矩阵（并行开始有效区域）
    100, 150, 200, 
    
    # 较大矩阵（典型并行加速区域）
    300, 400, 500,
    
    # 大矩阵（并行效率稳定区域）
    600, 700, 800,
    
    # 超大矩阵（系统极限测试）
    1000, 1200, 1500, 2048
]

# 结果字典初始化 - 包含所有基准测试类型
results = {
    # 求和相关的
    'parallel_sum': {},
    'serial_sum': {},
    'thread1_sum': {},
    'thread4_sum': {},
    'thread16_sum': {},
    'c_serial_sum': {},
    'c_parallel_sum': {},
    
    # 矩阵乘法相关的
    'mat_mul_serial': {},
    'mat_mul_parallel': {},
    'c_mat_mul_serial': {},
    'c_mat_mul_parallel': {},
}

# 正则表达式来提取执行时间
time_pattern = re.compile(r"bench:\s+([0-9,\.]+)\s+ns/iter")

# ======================================
# 运行求和基准测试
# ======================================
print("\nRunning sum benchmarks...")
for len_value in sum_len_values:
    env = os.environ.copy()
    # 设置环境变量 LEN（求和问题规模）
    env["LEN"] = str(len_value)
    # 固定 MLEN 为小值（矩阵大小），因为此时我们只关心求和测试
    env["MLEN"] = "1"
    
    print(f"Running sum benchmarks for LEN = {len_value} (MLEN fixed at 1)...")
    
    try:
        subprocess.run(["cargo", "build", "--release", "--quiet"],env=env, check=True)
        result = subprocess.run(
            ["cargo", "bench", "--quiet"],
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        
        # 解析输出结果，只记录求和相关的测试
        for line in result.stdout.splitlines():
            match = time_pattern.search(line)
            if match:
                time_ns = float(match.group(1).replace(',', ''))
                
                # 只记录求和基准测试
                if 'benchmark_parallel_sum' in line:
                    results['parallel_sum'][len_value] = time_ns
                elif 'benchmark_serial_sum' in line:
                    results['serial_sum'][len_value] = time_ns
                elif 'thread1_sum' in line:
                    results['thread1_sum'][len_value] = time_ns
                elif 'thread4_sum' in line:
                    results['thread4_sum'][len_value] = time_ns
                elif 'thread16_sum' in line:
                    results['thread16_sum'][len_value] = time_ns
                elif 'benchmark_c_parallel_sum' in line:
                    results['c_parallel_sum'][len_value] = time_ns
                elif 'benchmark_c_serial_sum' in line:
                    results['c_serial_sum'][len_value] = time_ns
        
        print(f"  Sum benchmarks completed for LEN={len_value}")
            
    except subprocess.CalledProcessError as e:
        print(f"  Error running sum benchmarks: {e}")
        print(f"  Output: {e.stdout}")
        print(f"  Error: {e.stderr}")

# ======================================
# 运行矩阵乘法基准测试
# ======================================
print("\nRunning matrix multiplication benchmarks...")
for mlen_value in mat_len_values:
    env = os.environ.copy()
    # 固定 LEN 为小值（求和问题规模），因为此时我们只关心矩阵测试
    env["LEN"] = "1"
    # 设置环境变量 MLEN（矩阵大小）
    env["MLEN"] = str(mlen_value)
    
    print(f"Running matrix benchmarks for MLEN = {mlen_value} (LEN fixed at 1)...")
    
    try:
        subprocess.run(["cargo", "build", "--release", "--quiet"],env=env, check=True)
        result = subprocess.run(
            ["cargo", "bench", "--quiet"],
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        
        # 解析输出结果，只记录矩阵乘法相关的测试
        for line in result.stdout.splitlines():
            match = time_pattern.search(line)
            if match:
                time_ns = float(match.group(1).replace(',', ''))
                
                # 只记录矩阵乘法基准测试
                if 'benchmark_mat_mul_serial' in line:
                    results['mat_mul_serial'][mlen_value] = time_ns
                elif 'benchmark_mat_mul_parallel' in line:
                    results['mat_mul_parallel'][mlen_value] = time_ns
                elif 'benchmarkc_c_mat_mul_serial' in line:
                    results['c_mat_mul_serial'][mlen_value] = time_ns
                elif 'benchmarkc_c_mat_mul_parallel' in line:
                    results['c_mat_mul_parallel'][mlen_value] = time_ns
        
        print(f"  Matrix benchmarks completed for MLEN={mlen_value}")
            
    except subprocess.CalledProcessError as e:
        print(f"  Error running matrix benchmarks: {e}")
        print(f"  Output: {e.stdout}")
        print(f"  Error: {e.stderr}")

# 输出结果
print("\nBenchmark Results:")
for test_type, times in results.items():
    print(f"\n{test_type}:")
    if "sum" in test_type:
        for len_value in sum_len_values:
            if len_value in times:
                print(f"  LEN: {len_value:>6}, Time: {times[len_value]:>12,.2f} ns")
    else:
        for mlen_value in mat_len_values:
            if mlen_value in times:
                print(f"  MLEN: {mlen_value:>6}, Time: {times[mlen_value]:>12,.2f} ns")

# 创建获取时间数据的辅助函数
def get_times(test_name, values):
    return [results[test_name].get(val, float('nan')) for val in values]

# ====================
# 创建第一个图表：求和基准测试
# ====================
plt.figure(figsize=(12, 10))

# 子图1：求和执行时间
plt.subplot(2, 1, 1)
plt.plot(sum_len_values, get_times('serial_sum', sum_len_values), 'k-', label='Serial (Rust)', marker='o', markersize=6)
plt.plot(sum_len_values, get_times('parallel_sum', sum_len_values), 'b-', label='Parallel (Rust Rayon)', marker='s', markersize=6)
plt.plot(sum_len_values, get_times('thread1_sum', sum_len_values), 'g--', label='Manual Threads (1)', marker='^', markersize=5)
plt.plot(sum_len_values, get_times('thread4_sum', sum_len_values), 'r--', label='Manual Threads (4)', marker='d', markersize=5)
plt.plot(sum_len_values, get_times('thread16_sum', sum_len_values), 'm--', label='Manual Threads (16)', marker='*', markersize=6)
plt.plot(sum_len_values, get_times('c_serial_sum', sum_len_values), 'c-', label='Serial (C)', marker='x', markersize=6)
plt.plot(sum_len_values, get_times('c_parallel_sum', sum_len_values), 'y-', label='Parallel (C OpenMP)', marker='+', markersize=7)

plt.xlabel('Problem Size (n)', fontsize=12)
plt.ylabel('Execution Time (ns)', fontsize=12)
plt.title('Sum Benchmark - Execution Time', fontsize=14)
plt.legend(loc='best')
plt.grid(True, linestyle='--', alpha=0.7)
plt.xscale('log')
plt.yscale('log')

# 子图2：求和加速比
plt.subplot(2, 1, 2)
serial_times = get_times('serial_sum', sum_len_values)
speedup_rayon = [serial / parallel if parallel > 0 else float('nan') for serial, parallel in zip(serial_times, get_times('parallel_sum', sum_len_values))]
speedup_thread1 = [serial / thread1 if thread1 > 0 else float('nan') for serial, thread1 in zip(serial_times, get_times('thread1_sum', sum_len_values))]
speedup_thread4 = [serial / thread4 if thread4 > 0 else float('nan') for serial, thread4 in zip(serial_times, get_times('thread4_sum', sum_len_values))]
speedup_thread16 = [serial / thread16 if thread16 > 0 else float('nan') for serial, thread16 in zip(serial_times, get_times('thread16_sum', sum_len_values))]
speedup_c_omp = [serial / c_parallel if c_parallel > 0 else float('nan') for serial, c_parallel in zip(serial_times, get_times('c_parallel_sum', sum_len_values))]

plt.plot(sum_len_values, speedup_rayon, 'b-', label='Rust Rayon', marker='s', markersize=6)
plt.plot(sum_len_values, speedup_thread1, 'g--', label='Manual (1 thread)', marker='^', markersize=5)
plt.plot(sum_len_values, speedup_thread4, 'r--', label='Manual (4 threads)', marker='d', markersize=5)
plt.plot(sum_len_values, speedup_thread16, 'm--', label='Manual (16 threads)', marker='*', markersize=6)
plt.plot(sum_len_values, speedup_c_omp, 'y-', label='C OpenMP', marker='+', markersize=7)
plt.axhline(y=1, color='k', linestyle='--', alpha=0.5)

plt.xlabel('Problem Size (n)', fontsize=12)
plt.ylabel('Speedup (vs Rust Serial)', fontsize=12)
plt.title('Sum Benchmark - Speedup Comparison', fontsize=14)
plt.legend(loc='best')
plt.grid(True, linestyle='--', alpha=0.7)
plt.xscale('log')

plt.tight_layout(pad=3.0)
plt.savefig('sum_benchmark_results.png', dpi=300)
print("\nSaved sum results as sum_benchmark_results.png")

# ====================
# 创建第二个图表：矩阵乘法基准测试
# ====================
plt.figure(figsize=(12, 10))

# 子图1：矩阵乘法执行时间
plt.subplot(2, 1, 1)
plt.plot(mat_len_values, get_times('mat_mul_serial', mat_len_values), 'k-', label='Serial (Rust)', marker='o', markersize=6)
plt.plot(mat_len_values, get_times('mat_mul_parallel', mat_len_values), 'b-', label='Parallel (Rust Rayon)', marker='s', markersize=6)
plt.plot(mat_len_values, get_times('c_mat_mul_serial', mat_len_values), 'c-', label='Serial (C)', marker='x', markersize=6)
plt.plot(mat_len_values, get_times('c_mat_mul_parallel', mat_len_values), 'y-', label='Parallel (C OpenMP)', marker='+', markersize=7)

plt.xlabel('Matrix Size (n x n)', fontsize=12)
plt.ylabel('Execution Time (ns)', fontsize=12)
plt.title('Matrix Multiplication Benchmark - Execution Time', fontsize=14)
plt.legend(loc='best')
plt.grid(True, linestyle='--', alpha=0.7)
plt.xscale('log')
plt.yscale('log')

# 子图2：矩阵乘法加速比
plt.subplot(2, 1, 2)
rust_serial_times = get_times('mat_mul_serial', mat_len_values)
rust_speedup = [rust_serial / rust_parallel if rust_parallel > 0 else float('nan') 
                for rust_serial, rust_parallel in zip(rust_serial_times, get_times('mat_mul_parallel', mat_len_values))]

c_serial_times = get_times('c_mat_mul_serial', mat_len_values)
c_speedup = [c_serial / c_parallel if c_parallel > 0 else float('nan') 
             for c_serial, c_parallel in zip(c_serial_times, get_times('c_mat_mul_parallel', mat_len_values))]

plt.plot(mat_len_values, rust_speedup, 'b-', label='Rust Rayon', marker='s', markersize=6)
plt.plot(mat_len_values, c_speedup, 'y-', label='C OpenMP', marker='+', markersize=7)
plt.axhline(y=1, color='k', linestyle='--', alpha=0.5)

plt.xlabel('Matrix Size (n x n)', fontsize=12)
plt.ylabel('Speedup (vs Respective Serial)', fontsize=12)
plt.title('Matrix Multiplication Benchmark - Speedup Comparison', fontsize=14)
plt.legend(loc='best')
plt.grid(True, linestyle='--', alpha=0.7)
plt.xscale('log')

plt.tight_layout(pad=3.0)
plt.savefig('matmul_benchmark_results.png', dpi=300)
print("Saved matrix multiplication results as matmul_benchmark_results.png")

plt.show()