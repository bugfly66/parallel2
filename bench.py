import subprocess
import os
import re
import matplotlib.pyplot as plt

len_values = [
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
    # # 极限规模 
    # 500000,1000000,100000000
]
# 结果字典初始化
results = {
    'parallel_sum': {},
    'serial_sum': {},
    'thread1_sum': {},
    'thread4_sum': {},
    'thread16_sum': {}
}

# 正则表达式来提取执行时间
time_pattern = re.compile(r"bench:\s+([0-9,\.]+)\s+ns/iter")

# 为每个 LEN 值运行基准测试
for len_value in len_values:
    # 设置环境变量 LEN
    os.environ["LEN"] = str(len_value)
    print(f"\nRunning benchmarks for LEN = {len_value}...")
    
    # 运行构建和基准测试
    try:
        # 使用 --no-run 避免重复编译
        subprocess.run(["cargo", "build", "--release", "--quiet"], check=True)
        
        # 运行基准测试
        result = subprocess.run(
            ["cargo", "bench", "--quiet"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # 解析输出结果
        found_any = False
        for line in result.stdout.splitlines():
            # 如果找到时间的行
            match = time_pattern.search(line)
            if match:
                # 提取测试名称和时间
                time_ns = float(match.group(1).replace(',', ''))  # 去掉逗号并转换为浮动类型
                
                if 'parallel_sum' in line:
                    results['parallel_sum'][len_value] = time_ns
                    found_any = True
                elif 'serial_sum' in line:
                    results['serial_sum'][len_value] = time_ns
                    found_any = True
                elif 'thread1_sum' in line:
                    results['thread1_sum'][len_value] = time_ns
                    found_any = True
                elif 'thread4_sum' in line:
                    results['thread4_sum'][len_value] = time_ns
                    found_any = True
                elif 'thread16_sum' in line:
                    results['thread16_sum'][len_value] = time_ns
                    found_any = True
        
        if not found_any:
            print(f"  Warning: No benchmark results found for LEN={len_value}")
        else:
            print(f"  Benchmarks completed for LEN={len_value}")
            
    except subprocess.CalledProcessError as e:
        print(f"  Error running benchmarks for LEN={len_value}: {e}")
        print(f"  Output: {e.stdout}")
        print(f"  Error: {e.stderr}")

# 输出结果
print("\nBenchmark Results:")
for test_type, times in results.items():
    print(f"\n{test_type}:")
    for len_value in len_values:
        if len_value in times:
            print(f"  LEN: {len_value:>6}, Time: {times[len_value]:>12,.2f} ns")

# 创建绘图数据（处理缺失值）
def get_times(test_name):
    return [results[test_name].get(len_value, float('nan')) for len_value in len_values]

# 获取各测试的时间数据
parallel_times = get_times('parallel_sum')
serial_times = get_times('serial_sum')
thread1_times = get_times('thread1_sum')
thread4_times = get_times('thread4_sum')
thread16_times = get_times('thread16_sum')

# 创建图表
plt.figure(figsize=(12, 8))

# 主图：执行时间 vs LEN
plt.subplot(2, 1, 1)
plt.plot(len_values, serial_times, 'k-', label='Serial', marker='o', markersize=6)
plt.plot(len_values, parallel_times, 'b-', label='Parallel (Rayon)', marker='s', markersize=6)
plt.plot(len_values, thread1_times, 'g--', label='Manual Threads (1)', marker='^', markersize=5)
plt.plot(len_values, thread4_times, 'r--', label='Manual Threads (4)', marker='d', markersize=5)
plt.plot(len_values, thread16_times, 'm--', label='Manual Threads (16)', marker='*', markersize=6)

plt.xlabel('Problem Size (n)', fontsize=12)
plt.ylabel('Execution Time (ns)', fontsize=12)
plt.title('Parallel vs Serial Performance Comparison', fontsize=14)
plt.legend(loc='best')
plt.grid(True, linestyle='--', alpha=0.7)
plt.yscale('log')  # 对数尺度更适合大范围数据

# 子图：加速比
plt.subplot(2, 1, 2)
# 计算加速比（相对于串行版本）
speedup_parallel = [serial / parallel if parallel > 0 else float('nan') for serial, parallel in zip(serial_times, parallel_times)]
speedup_thread1 = [serial / thread1 if thread1 > 0 else float('nan') for serial, thread1 in zip(serial_times, thread1_times)]
speedup_thread4 = [serial / thread4 if thread4 > 0 else float('nan') for serial, thread4 in zip(serial_times, thread4_times)]
speedup_thread16 = [serial / thread16 if thread16 > 0 else float('nan') for serial, thread16 in zip(serial_times, thread16_times)]

plt.plot(len_values, speedup_parallel, 'b-', label='Parallel (Rayon)', marker='s', markersize=6)
plt.plot(len_values, speedup_thread1, 'g--', label='Manual Threads (1)', marker='^', markersize=5)
plt.plot(len_values, speedup_thread4, 'r--', label='Manual Threads (4)', marker='d', markersize=5)
plt.plot(len_values, speedup_thread16, 'm--', label='Manual Threads (16)', marker='*', markersize=6)
plt.axhline(y=1, color='k', linestyle='--', alpha=0.5)  # 参考线

plt.xlabel('Problem Size (n)', fontsize=12)
plt.ylabel('Speedup (vs Serial)', fontsize=12)
plt.title('Parallel Speedup Comparison', fontsize=14)
plt.legend(loc='best')
plt.grid(True, linestyle='--', alpha=0.7)

plt.tight_layout(pad=3.0)

# 保存和显示图表
plt.savefig('parallel_benchmark_results.png', dpi=300)
print("\nSaved results as parallel_benchmark_results.png")
plt.show()
