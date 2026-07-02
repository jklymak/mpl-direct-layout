"""
Scaling benchmark: how DirectLayoutEngine and matplotlib's constrained_layout
compare as the number of axes grows (N x N grids), with and without a colorbar
on every axes.

This is the "does direct scale better than constrained" question -- constrained
runs a kiwisolver constraint solve whose cost grows faster than our O(n)
algebraic placement, so the direct engine is expected to pull ahead on large
grids.  Adding a per-axes colorbar stresses the colorbar code path at scale.

The engine cost is isolated with the ``layout-only`` metric (repeated
``layout_engine.execute`` on an already-drawn figure), which strips out the
rendering time that both engines share and that otherwise dominates -- and
hides the difference -- on big grids.

Outputs a comparison plot (absolute layout time + speedup vs grid size) and,
optionally, a CSV.  Only depends on numpy + matplotlib.

Usage::

    python benchmarks/benchmark_scaling.py                 # default sweep + plot
    python benchmarks/benchmark_scaling.py --quick          # small, fast sweep
    python benchmarks/benchmark_scaling.py --sizes 2 4 8 16 # custom grid sizes
    python benchmarks/benchmark_scaling.py --no-colorbar    # plain grids only
"""
from __future__ import annotations

import argparse
import platform
import time

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import mpl_direct_layout  # noqa: F401  registers 'direct'


def _build_grid(layout, n, with_colorbar):
    """N x N grid of small plots (optionally a colorbar on each axes)."""
    fig = plt.figure(figsize=(n * 1.1, n * 1.1), layout=layout)
    axs = np.atleast_2d(fig.subplots(n, n))
    for ax in axs.flat:
        if with_colorbar:
            im = ax.pcolormesh(np.arange(16).reshape(4, 4), rasterized=True)
            fig.colorbar(im, ax=ax)
        else:
            ax.plot([1, 2, 3], [1, 4, 2])
        ax.locator_params(nbins=3)
        ax.set_xlabel('x')
        ax.set_ylabel('y')
    return fig


def time_layout_only(n, layout, with_colorbar, n_warm, n_runs):
    """Time repeated ``layout_engine.execute(fig)`` on an already-drawn fig."""
    fig = _build_grid(layout, n, with_colorbar)
    fig.canvas.draw()                       # warm renderer + decoration caches
    engine = fig.get_layout_engine()
    for _ in range(n_warm):
        engine.execute(fig)
    times = np.empty(n_runs)
    for k in range(n_runs):
        t0 = time.perf_counter()
        engine.execute(fig)
        times[k] = time.perf_counter() - t0
    plt.close(fig)
    return times.mean(), times.std()


def _runs_for(n):
    """Fewer repeats as the grid (and so each run) gets more expensive."""
    if n <= 4:
        return 20
    if n <= 8:
        return 10
    if n <= 14:
        return 5
    return 3


def run_sweep(sizes, variants, quick):
    results = {}  # (variant, engine) -> list of (mean, std) aligned with sizes
    for variant in variants:
        for engine in ('direct', 'constrained'):
            results[(variant, engine)] = []

    print("=" * 74)
    print("Scaling benchmark: DirectLayoutEngine vs constrained_layout")
    print(f"  matplotlib {matplotlib.__version__} | python {platform.python_version()} "
          f"| {platform.system()} {platform.machine()}")
    print("=" * 74)

    for variant in variants:
        with_cb = variant == 'colorbar'
        print(f"\n{variant} grids (layout-only, ms):")
        print(f"  {'axes':>6} {'direct':>16} {'constrained':>16} {'speedup':>9}")
        for n in sizes:
            n_runs = 4 if quick else _runs_for(n)
            dm, ds = time_layout_only(n, 'direct', with_cb, 2, n_runs)
            cm, cs = time_layout_only(n, 'constrained', with_cb, 2, n_runs)
            results[(variant, 'direct')].append((dm, ds))
            results[(variant, 'constrained')].append((cm, cs))
            print(f"  {n*n:>6} {dm*1e3:>8.1f} +/-{ds*1e3:>4.1f} "
                  f"{cm*1e3:>8.1f} +/-{cs*1e3:>4.1f} {cm/dm:>8.2f}x")
    return results


def make_plot(sizes, variants, results, path):
    n_axes = [n * n for n in sizes]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5), layout='constrained')

    styles = {'plain': '-', 'colorbar': '--'}
    colors = {'direct': 'tab:green', 'constrained': 'tab:red'}
    for variant in variants:
        for engine in ('constrained', 'direct'):
            means = np.array([m for m, s in results[(variant, engine)]]) * 1e3
            ax1.plot(n_axes, means, styles[variant], color=colors[engine],
                     marker='o', label=f'{engine} ({variant})')
        d = np.array([m for m, s in results[(variant, 'direct')]])
        c = np.array([m for m, s in results[(variant, 'constrained')]])
        ax2.plot(n_axes, c / d, styles[variant], color='tab:blue', marker='o',
                 label=f'{variant}')

    ax1.set_xlabel('number of axes (N x N grid)')
    ax1.set_ylabel('layout time (ms)')
    ax1.set_title('Layout cost vs grid size')
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3)

    ax2.axhline(1.0, color='k', lw=0.8, ls=':')
    ax2.set_xlabel('number of axes (N x N grid)')
    ax2.set_ylabel('speedup (constrained / direct)')
    ax2.set_title('direct faster where > 1')
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)

    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"\nComparison plot written to {path}")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--sizes', type=int, nargs='+', default=None,
                    help='grid sizes N (each is an N x N grid)')
    ap.add_argument('--quick', action='store_true', help='small, fast sweep')
    ap.add_argument('--no-colorbar', action='store_true',
                    help='plain grids only (skip the colorbar variant)')
    ap.add_argument('--plot', type=str, default='benchmarks/scaling_comparison.png',
                    help='output PNG path (use "" to skip)')
    ap.add_argument('--csv', type=str, default=None, help='write raw results to CSV')
    args = ap.parse_args()

    if args.sizes is not None:
        sizes = args.sizes
    elif args.quick:
        sizes = [2, 3, 5, 8]
    else:
        sizes = [2, 3, 5, 8, 12, 16, 20]

    variants = ['plain'] if args.no_colorbar else ['plain', 'colorbar']

    results = run_sweep(sizes, variants, args.quick)

    if args.plot:
        make_plot(sizes, variants, results, args.plot)

    if args.csv:
        import csv
        with open(args.csv, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['variant', 'engine', 'n', 'n_axes',
                        'layout_mean_s', 'layout_std_s'])
            for variant in variants:
                for engine in ('direct', 'constrained'):
                    for n, (m, s) in zip(sizes, results[(variant, engine)]):
                        w.writerow([variant, engine, n, n * n, m, s])
        print(f"Raw results written to {args.csv}")


if __name__ == '__main__':
    main()
