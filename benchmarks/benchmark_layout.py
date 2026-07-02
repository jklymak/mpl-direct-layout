"""
Benchmark DirectLayoutEngine against matplotlib's constrained_layout on a set
of *complicated* figures (colorbars, shared/spanning colorbars, mosaics,
compressed fixed-aspect grids) -- not just plain N x N grids.

Two things are measured for every scenario:

* **layout-only**  -- the figure is built and drawn once to warm all caches,
  then ``layout_engine.execute(fig)`` is timed in a tight loop.  This isolates
  the layout algorithm from rendering and is the number to watch when
  optimising the engine (e.g. the tight-bbox caching work).
* **full draw**    -- the figure is rebuilt and ``fig.canvas.draw()`` timed
  end to end, for context on how much layout costs relative to a real draw.

Each scenario is run for ``layout='direct'`` and for the matplotlib built-in it
is meant to replace (``constrained`` / ``compressed``), and the speedup is
reported.

Usage::

    python benchmarks/benchmark_layout.py            # full run
    python benchmarks/benchmark_layout.py --quick    # fewer repeats
    python benchmarks/benchmark_layout.py --csv out.csv

Only depends on numpy + matplotlib (no pandas / memory_profiler).
"""
from __future__ import annotations

import argparse
import platform
import time

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import mpl_direct_layout  # noqa: F401  registers 'direct' / 'direct-compressed'


# ---------------------------------------------------------------------------
# Content helpers
# ---------------------------------------------------------------------------

def _decorate(ax):
    ax.plot([1, 2, 3], [1, 4, 2])
    ax.locator_params(nbins=3)
    ax.set_xlabel('x-label')
    ax.set_ylabel('y-label')
    ax.set_title('Title')


def _image(ax):
    y, x = np.mgrid[-3:3:0.2, -3:3:0.2]
    z = (1 - x / 2 + x ** 5 + y ** 3) * np.exp(-x ** 2 - y ** 2)
    im = ax.pcolormesh(x, y, z, cmap='RdBu_r', vmin=-1, vmax=1, rasterized=True)
    ax.set_xlabel('x-label')
    ax.set_ylabel('y-label')
    ax.set_title('Title')
    return im


# ---------------------------------------------------------------------------
# Scenario builders.  Each takes the *layout* string and returns a Figure.
# ---------------------------------------------------------------------------

def build_dense_grid(layout):
    fig = plt.figure(figsize=(9, 9), layout=layout)
    axs = fig.subplots(5, 5)
    for ax in axs.flat:
        _decorate(ax)
    return fig


def build_per_axes_colorbars(layout):
    fig = plt.figure(figsize=(9, 8), layout=layout)
    axs = fig.subplots(3, 3)
    for ax in axs.flat:
        im = _image(ax)
        fig.colorbar(im, ax=ax)
    return fig


def build_shared_colorbars(layout):
    fig = plt.figure(figsize=(10, 6), layout=layout)
    axs = fig.subplots(2, 3)
    for ax in axs.flat:
        im = _image(ax)
    # one shared colorbar spanning each row -> exercises spanning-colorbar path
    fig.colorbar(im, ax=axs[0, :].tolist())
    fig.colorbar(im, ax=axs[1, :].tolist())
    return fig


def build_mosaic(layout):
    fig = plt.figure(figsize=(9, 7), layout=layout)
    axd = fig.subplot_mosaic(
        """
        AAB
        CDB
        """,
        empty_sentinel='.',
    )
    for k, ax in axd.items():
        if k in ('A', 'B'):
            im = _image(ax)
        else:
            _decorate(ax)
    fig.colorbar(im, ax=list(axd.values()))
    return fig


def build_compressed_grid(layout):
    fig = plt.figure(figsize=(8, 8), layout=layout)
    axs = fig.subplots(3, 3)
    data = np.arange(100).reshape(10, 10)
    for ax in axs.flat:
        ax.imshow(data)  # fixed aspect -> leaves compressible whitespace
        ax.set_xlabel('x')
        ax.set_ylabel('y')
    return fig


# name, builder, direct-layout key, matplotlib-equivalent key
SCENARIOS = [
    ('dense_grid_5x5',       build_dense_grid,         'direct',            'constrained'),
    ('per_axes_colorbars',   build_per_axes_colorbars, 'direct',            'constrained'),
    ('shared_colorbars',     build_shared_colorbars,   'direct',            'constrained'),
    ('mosaic_spanning_cbar', build_mosaic,             'direct',            'constrained'),
    ('compressed_imshow',    build_compressed_grid,    'direct-compressed', 'compressed'),
]


# ---------------------------------------------------------------------------
# Timing
# ---------------------------------------------------------------------------

def time_layout_only(builder, layout, n_warm, n_runs):
    """Time repeated ``layout_engine.execute(fig)`` on an already-drawn fig."""
    fig = builder(layout)
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
    return times


def time_full_draw(builder, layout, n_warm, n_runs):
    """Time end-to-end build + draw, rebuilding the figure each run."""
    for _ in range(n_warm):
        fig = builder(layout)
        fig.canvas.draw()
        plt.close(fig)
    times = np.empty(n_runs)
    for k in range(n_runs):
        fig = builder(layout)
        t0 = time.perf_counter()
        fig.canvas.draw()
        times[k] = time.perf_counter() - t0
        plt.close(fig)
    return times


def _fmt(t):
    return f"{t.mean() * 1e3:7.2f} ms +/- {t.std() * 1e3:5.2f}"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--quick', action='store_true', help='fewer repeats')
    ap.add_argument('--runs', type=int, default=None, help='explicit number of timed runs')
    ap.add_argument('--csv', type=str, default=None, help='write raw results to CSV')
    args = ap.parse_args()

    n_warm = 2
    n_runs = args.runs if args.runs is not None else (8 if args.quick else 30)

    print("=" * 78)
    print("Layout benchmark: DirectLayoutEngine vs matplotlib built-in")
    print(f"  matplotlib {matplotlib.__version__} | python {platform.python_version()} "
          f"| {platform.system()} {platform.machine()}")
    print(f"  {n_runs} timed runs after {n_warm} warmups")
    print("=" * 78)

    rows = []
    for name, builder, dkey, mkey in SCENARIOS:
        print(f"\n{name}")
        for metric, timer in (('layout-only', time_layout_only),
                              ('full-draw', time_full_draw)):
            d = timer(builder, dkey, n_warm, n_runs)
            m = timer(builder, mkey, n_warm, n_runs)
            speedup = m.mean() / d.mean()
            print(f"  {metric:11s}  direct {_fmt(d)}   {mkey:11s} {_fmt(m)}"
                  f"   speedup {speedup:5.2f}x")
            rows.append((name, metric, dkey, d.mean(), d.std(),
                         mkey, m.mean(), m.std(), speedup))

    # headline: layout-only geometric-mean speedup
    lo = [r[8] for r in rows if r[1] == 'layout-only']
    print("\n" + "=" * 78)
    print(f"Layout-only speedup (geo-mean over scenarios): "
          f"{np.exp(np.mean(np.log(lo))):.2f}x")
    print("=" * 78)

    if args.csv:
        import csv
        with open(args.csv, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['scenario', 'metric', 'direct_key', 'direct_mean_s',
                        'direct_std_s', 'mpl_key', 'mpl_mean_s', 'mpl_std_s',
                        'speedup'])
            w.writerows(rows)
        print(f"\nRaw results written to {args.csv}")


if __name__ == '__main__':
    main()
