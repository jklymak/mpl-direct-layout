"""
Benchmark speed comparison between direct layout and constrained_layout.
"""
import matplotlib.pyplot as plt
import numpy as np
import time
import mpl_direct_layout

def benchmark_layout(layout, n_axes=(3, 3), n_runs=50, figsize=None):
    """Time how long it takes to create and draw a figure."""
    times = []

    # Scale figure size with number of axes
    if figsize is None:
        max_dim = max(n_axes)
        figsize = (max_dim * 0.8, max_dim * 0.8)

    for _ in range(n_runs):
        fig = plt.figure(figsize=figsize, layout=layout)
        axs = fig.subplots(*n_axes)

        # Add minimal content to each axes
        for i, ax in enumerate(axs.flat):
            if i < 5:  # Only add content to first few to save time
                ax.plot([1, 2, 3], [1, 4, 2])
                ax.set_xlabel('X')
                ax.set_ylabel('Y')

        # Time the actual layout computation (triggered by draw)
        start = time.perf_counter()
        fig.canvas.draw()
        elapsed = time.perf_counter() - start
        times.append(elapsed)

        plt.close(fig)

    return np.array(times)


if __name__ == '__main__':
    print("Benchmarking layout engines...")
    print("=" * 60)

    # Test with 3x3 grid
    print("\n3×3 grid of axes:")
    direct_times = benchmark_layout('direct', (3, 3), n_runs=30)
    constrained_times = benchmark_layout('constrained', (3, 3), n_runs=30)

    print(f"  direct:       {direct_times.mean()*1000:.2f} ms ± {direct_times.std()*1000:.2f} ms")
    print(f"  constrained:  {constrained_times.mean()*1000:.2f} ms ± {constrained_times.std()*1000:.2f} ms")
    print(f"  Speedup:      {constrained_times.mean() / direct_times.mean():.2f}×")

    # Test with 6x6 grid
    print("\n6×6 grid of axes:")
    direct_times = benchmark_layout('direct', (6, 6), n_runs=20)
    constrained_times = benchmark_layout('constrained', (6, 6), n_runs=20)

    print(f"  direct:       {direct_times.mean()*1000:.2f} ms ± {direct_times.std()*1000:.2f} ms")
    print(f"  constrained:  {constrained_times.mean()*1000:.2f} ms ± {constrained_times.std()*1000:.2f} ms")
    print(f"  Speedup:      {constrained_times.mean() / direct_times.mean():.2f}×")

    # Test with 12x12 grid (stress test)
    print("\n12×12 grid of axes (stress test):")
    print("  (This may take a minute...)")
    direct_times = benchmark_layout('direct', (12, 12), n_runs=10)
    constrained_times = benchmark_layout('constrained', (12, 12), n_runs=10)

    print(f"  direct:       {direct_times.mean()*1000:.2f} ms ± {direct_times.std()*1000:.2f} ms")
    print(f"  constrained:  {constrained_times.mean()*1000:.2f} ms ± {constrained_times.std()*1000:.2f} ms")
    print(f"  Speedup:      {constrained_times.mean() / direct_times.mean():.2f}×")

    print("\n" + "=" * 60)
    print("""
Key speed advantages of DirectLayoutEngine:
1. Two-pass only (measure → position), no iteration
2. Pure algebraic positioning (no constraint solver)
3. No convergence checks or iterative refinement
4. O(n) complexity for n axes vs O(n²) or worse for constraint solving
""")
