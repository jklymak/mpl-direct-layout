"""
Simple speed comparison between direct layout and constrained_layout.
"""
import matplotlib.pyplot as plt
import numpy as np
import time
import mpl_direct_layout
from memory_profiler import memory_usage
import platform
import datetime

def time_single_layout(layout, nrows, ncols):
    """Time a single figure creation and draw, and measure peak memory."""
    fig = plt.figure(figsize=(nrows*1.2, ncols*1.2), layout=layout)
    axs = fig.subplots(nrows, ncols)

    def draw_fig():
        fig.canvas.draw()

    start = time.perf_counter()
    mem_usage = memory_usage((draw_fig,))
    elapsed = time.perf_counter() - start

    plt.close(fig)
    return elapsed, max(mem_usage)

if __name__ == '__main__':
    print("Speed comparison: DirectLayoutEngine vs constrained_layout")
    print("=" * 70)

    grid_sizes = [3, 6, 12, 18, 24, 30]
    direct_means = []
    direct_mems = []
    constrained_means = []
    constrained_mems = []

    for n in grid_sizes:
        print(f"\n{n}×{n} grid:")
        # Warm up
        print("  Warming up direct...", end='', flush=True)
        time_single_layout('direct', n, n)
        print(" done")
        print("  Warming up constrained...", end='', flush=True)
        time_single_layout('constrained', n, n)
        print(" done")

        # Time direct layout (5 runs)
        print("  Timing direct (5 runs)...", end='', flush=True)
        direct_results = [time_single_layout('direct', n, n) for _ in range(5)]
        direct_times = [r[0] for r in direct_results]
        direct_mem = max(r[1] for r in direct_results)
        direct_means.append(np.mean(direct_times))
        direct_mems.append(direct_mem)
        print(" done")

        # Time constrained layout (5 runs)
        print("  Timing constrained (5 runs)...", end='', flush=True)
        constrained_results = [time_single_layout('constrained', n, n) for _ in range(5)]
        constrained_times = [r[0] for r in constrained_results]
        constrained_mem = max(r[1] for r in constrained_results)
        constrained_means.append(np.mean(constrained_times))
        constrained_mems.append(constrained_mem)
        print(" done")

        print(f"  direct:       {direct_means[-1]*1000:.1f} ms, {direct_mems[-1]:.1f} MiB peak")
        print(f"  constrained:  {constrained_means[-1]*1000:.1f} ms, {constrained_mems[-1]:.1f} MiB peak")
        print(f"  Speedup:      {constrained_means[-1] / direct_means[-1]:.2f}×")

    print("\n" + "=" * 70)

    # Plot timing and memory trends
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 8))
    ax1.plot(grid_sizes, np.array(direct_means)*1000, 'o-', label='DirectLayoutEngine')
    ax1.plot(grid_sizes, np.array(constrained_means)*1000, 's-', label='constrained_layout')
    ax1.set_ylabel('Mean draw time (ms)')
    ax1.set_xlabel('Grid size N (for N×N)')
    ax1.set_title('Timing vs Grid Size')
    ax1.legend()
    ax1.grid(True)

    ax2.plot(grid_sizes, direct_mems, 'o-', label='DirectLayoutEngine')
    ax2.plot(grid_sizes, constrained_mems, 's-', label='constrained_layout')
    ax2.set_ylabel('Peak memory (MiB)')
    ax2.set_xlabel('Grid size N (for N×N)')
    ax2.set_title('Memory Usage vs Grid Size')
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()
    plt.savefig('benchmark_timing_memory.png', dpi=150)

    # Save a caption with system info
    sysinfo = f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" \
              f"System: {platform.system()} {platform.release()} ({platform.machine()})\n" \
              f"Processor: {platform.processor()}\n" \
              f"Python: {platform.python_version()}\n" \
              f"Matplotlib: {plt.matplotlib.__version__}"
    with open('benchmark_timing_memory.txt', 'w') as f:
        f.write(sysinfo)
    print("\nBenchmark plot saved as benchmark_timing_memory.png")
    print("System info saved as benchmark_timing_memory.txt:")
    print(sysinfo)
    plt.show()
