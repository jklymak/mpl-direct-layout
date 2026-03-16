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

def time_single_layout_nolayout(nrows, ncols):
    """Time a single figure creation and draw, and measure peak memory, with no layout manager."""
    fig = plt.figure(figsize=(nrows*1.2, ncols*1.2))
    axs = fig.subplots(nrows, ncols)

    def draw_fig():
        fig.canvas.draw()

    start = time.perf_counter()
    mem_usage = memory_usage((draw_fig,))
    elapsed = time.perf_counter() - start

    plt.close(fig)
    return elapsed, max(mem_usage)


import argparse


def analyze_and_plot(csv_path='benchmark_timing_data.csv'):
    import pandas as pd
    # Load timing data
    timing_df = pd.read_csv(csv_path)
    grid_sizes = sorted(timing_df['N'].unique())
    n_repeats = (timing_df['N'] == grid_sizes[0]).sum()
    # Reshape to lists of lists for plotting
    direct_all_times = [timing_df.loc[timing_df['N'] == n, 'direct'].values for n in grid_sizes]
    constrained_all_times = [timing_df.loc[timing_df['N'] == n, 'constrained'].values for n in grid_sizes]
    nolayout_all_times = [timing_df.loc[timing_df['N'] == n, 'nolayout'].values for n in grid_sizes]

    # Plot timing trends (no fits)
    fig, ax1 = plt.subplots(figsize=(7, 5), layout='direct')
    for i, n in enumerate(grid_sizes):
        ax1.plot([n]*n_repeats, np.array(direct_all_times[i])*1000, 'o', color='gray', alpha=0.4)
        ax1.plot([n]*n_repeats, np.array(constrained_all_times[i])*1000, 's', color='red', alpha=0.4)
        ax1.plot([n]*n_repeats, np.array(nolayout_all_times[i])*1000, 'x', color='blue', alpha=0.3)
    ax1.plot(grid_sizes, [np.mean(times)*1000 for times in nolayout_all_times], 'x--', label='No layout', color='blue')
    ax1.plot(grid_sizes, [np.mean(times)*1000 for times in direct_all_times], 'o-', label='DirectLayoutEngine', color='black')
    ax1.plot(grid_sizes, [np.mean(times)*1000 for times in constrained_all_times], 's-', label='constrained_layout', color='red')
    ax1.set_ylabel('Draw time (ms)')
    ax1.set_xlabel('Grid size N (for N×N)')
    ax1.set_title('Timing vs Grid Size')
    ax1.legend()
    ax1.grid(True)
    plt.savefig('benchmark_timing_memory.png', dpi=150)
    print("\nBenchmark plot saved as benchmark_timing_memory.png")

    # Save a caption with system info
    sysinfo = f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" \
              f"System: {platform.system()} {platform.release()} ({platform.machine()})\n" \
              f"Processor: {platform.processor()}\n" \
              f"Python: {platform.python_version()}\n" \
              f"Matplotlib: {plt.matplotlib.__version__}"
    with open('benchmark_timing_memory.txt', 'w') as f:
        f.write(sysinfo)
    print("System info saved as benchmark_timing_memory.txt:")
    print(sysinfo)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Benchmark direct vs constrained_layout')
    parser.add_argument('--analyze-only', action='store_true', help='Only analyze/plot from CSV, do not rerun benchmarks')
    parser.add_argument('--csv', type=str, default='benchmark_timing_data.csv', help='CSV file to analyze')
    args = parser.parse_args()

    if args.analyze_only:
        analyze_and_plot(args.csv)
    else:
        print("Speed comparison: DirectLayoutEngine vs constrained_layout")
        print("=" * 70)

        grid_sizes = [3, 6, 12, 18, 24, 30, 40]
        n_repeats = 5
        direct_means = []
        direct_mems = []
        direct_all_times = []
        constrained_means = []
        constrained_mems = []
        constrained_all_times = []
        nolayout_means = []
        nolayout_mems = []
        nolayout_all_times = []

        for n in grid_sizes:
            print(f"\n{n}×{n} grid:")
            # Warm up
            print("  Warming up no layout...", end='', flush=True)
            time_single_layout_nolayout(n, n)
            print(" done")
            print("  Warming up direct...", end='', flush=True)
            time_single_layout('direct', n, n)
            print(" done")
            print("  Warming up constrained...", end='', flush=True)
            time_single_layout('constrained', n, n)
            print(" done")

            # Time no layout (n_repeats runs)
            print(f"  Timing no layout ({n_repeats} runs)...", end='', flush=True)
            nolayout_results = [time_single_layout_nolayout(n, n) for _ in range(n_repeats)]
            nolayout_times = [r[0] for r in nolayout_results]
            nolayout_mem = max(r[1] for r in nolayout_results)
            nolayout_means.append(np.mean(nolayout_times))
            nolayout_mems.append(nolayout_mem)
            nolayout_all_times.append(nolayout_times)
            print(" done")

            # Time direct layout (n_repeats runs)
            print(f"  Timing direct ({n_repeats} runs)...", end='', flush=True)
            direct_results = [time_single_layout('direct', n, n) for _ in range(n_repeats)]
            direct_times = [r[0] for r in direct_results]
            direct_mem = max(r[1] for r in direct_results)
            direct_means.append(np.mean(direct_times))
            direct_mems.append(direct_mem)
            direct_all_times.append(direct_times)
            print(" done")

            # Time constrained layout (n_repeats runs)
            print(f"  Timing constrained ({n_repeats} runs)...", end='', flush=True)
            constrained_results = [time_single_layout('constrained', n, n) for _ in range(n_repeats)]
            constrained_times = [r[0] for r in constrained_results]
            constrained_mem = max(r[1] for r in constrained_results)
            constrained_means.append(np.mean(constrained_times))
            constrained_mems.append(constrained_mem)
            constrained_all_times.append(constrained_times)
            print(" done")

            print(f"  direct:       {direct_means[-1]*1000:.1f} ms, {direct_mems[-1]:.1f} MiB peak")
            print(f"  constrained:  {constrained_means[-1]*1000:.1f} ms, {constrained_mems[-1]:.1f} MiB peak")
            print(f"  Speedup:      {constrained_means[-1] / direct_means[-1]:.2f}×")

        # Save all timing data for fitting
        import pandas as pd
        timing_df = pd.DataFrame({
            'N': np.repeat(grid_sizes, n_repeats),
            'nolayout': np.concatenate(nolayout_all_times),
            'direct': np.concatenate(direct_all_times),
            'constrained': np.concatenate(constrained_all_times),
        })
        timing_df.to_csv('benchmark_timing_data.csv', index=False)
        # Also run analysis/plotting after collecting new data
        analyze_and_plot('benchmark_timing_data.csv')

