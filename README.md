# mpl-direct-layout

[![Tests](https://github.com/jklymak/mpl-direct-layout/actions/workflows/tests.yml/badge.svg)](https://github.com/jklymak/mpl-direct-layout/actions/workflows/tests.yml)
[![Documentation](https://github.com/jklymak/mpl-direct-layout/actions/workflows/deploy-docs.yml/badge.svg)](https://jklymak.github.io/mpl-direct-layout/)

A kiwisolver-free layout engine for [Matplotlib](https://matplotlib.org) that
positions axes using direct algebraic solving rather than constraint
optimisation.

![Example: Mosaic layout with shared colorbar](tests/baseline_images/test_mosaic_shared_colorbar.png)

## Documentation

Full documentation is available at **[jklymak.github.io/mpl-direct-layout](https://jklymak.github.io/mpl-direct-layout/)**

## Why?

Matplotlib's `constrained_layout` requires `kiwisolver`.  `mpl-direct-layout`
achieves the same goal — tight, non-overlapping axes with proper label spacing
— using only NumPy arithmetic, making it lighter and faster for simple grids.

## Performance

Both engines spend most of their time in the same place: measuring each axes'
decorations (ticks, labels, titles) via Matplotlib's `get_tightbbox`.  The
difference is in placement — `constrained_layout` runs a `kiwisolver`
constraint solve whose cost grows super-linearly with the number of axes, while
`DirectLayoutEngine` places axes with `O(n)` algebra.  As a result the direct
engine pulls further ahead as grids get larger.

![Layout time and speedup vs grid size](benchmarks/scaling_comparison.png)

Layout-only timings (Matplotlib 3.11, Apple Silicon), sweeping `N×N` grids:

| axes | plain: direct | plain: constrained | speedup | colorbar: direct | colorbar: constrained | speedup |
|-----:|--------------:|-------------------:|--------:|-----------------:|----------------------:|--------:|
|    4 |      12.6 ms  |            13.1 ms | 1.04×   |         31.0 ms  |              26.5 ms  | 0.85×   |
|   64 |     201.2 ms  |           228.6 ms | 1.14×   |        517.2 ms  |             460.8 ms  | 0.89×   |
|  144 |     454.6 ms  |           591.5 ms | 1.30×   |       1164.2 ms  |            1109.2 ms  | 0.95×   |
|  400 |    1312.5 ms  |          2399.3 ms | 1.83×   |       3370.6 ms  |            3918.6 ms  | 1.16×   |

For plain grids the direct engine is faster everywhere and the margin widens
with size (1.8× at 400 axes).  With a colorbar on every axes there is a small
constant per-colorbar overhead (measuring each colorbar's neighbour at its final
size), so the direct engine trails on small grids; because that overhead is a
constant factor while the constraint solve is super-linear, the direct engine
crosses ahead at roughly 200 axes and leads at scale.  The regime where it
trails — small colorbar grids — is already sub-30 ms, where the difference is
imperceptible.

Reproduce with:

```bash
python benchmarks/benchmark_scaling.py     # scaling sweep + comparison plot
python benchmarks/benchmark_layout.py      # complex single-figure scenarios
```

## Features

- Drop-in replacement: use `layout='direct'` wherever you would use
  `layout='constrained'`
- Colorbars (right / left / top / bottom, single or shared across axes)
- Mosaic layouts (`fig.subplot_mosaic`)
- Spanning axes
- `width_ratios` / `height_ratios`
- `suptitle`, `supxlabel`, `supylabel`
- Subfigures (including nested)
- Configurable outer margins and padding

## Installation

```bash
pip install mpl-direct-layout
```

### Development install

```bash
git clone https://github.com/jklymak/mpl-direct-layout
cd mpl-direct-layout
pip install -e ".[test,docs]"
```

## Quick start

```python
import mpl_direct_layout          # registers the engine
import matplotlib.pyplot as plt

fig, axs = plt.subplots(2, 2, layout='direct')
for ax in axs.flat:
    ax.plot([1, 2, 3])
    ax.set_xlabel('x-label')
    ax.set_ylabel('y-label')
    ax.set_title('Title')
fig.suptitle('Direct layout')
plt.show()
```

## Customisation

```python
fig = plt.figure(layout='direct')
eng = fig.get_layout_engine()
eng.set(
    h_pad=6/72,        # 6 pt vertical padding between axes
    w_pad=6/72,        # 6 pt horizontal padding
    left=0.1,          # 0.1" left outer margin
    right=0.1,
    top=0.1,
    bottom=0.1,
    suptitle_pad=0.15, # 0.15" gap below suptitle
)
```

## Running the tests

```bash
# Generate baseline images (first time only)
pytest tests/ --mpl-generate-path=tests/baseline_images

# Run image comparison tests
pytest tests/ --mpl
```

## Project layout

```
src/mpl_direct_layout/
    __init__.py     re-exports DirectLayoutEngine; registers 'direct' layout key
    _engine.py      the layout engine implementation
tests/
    conftest.py
    test_layout.py  pytest-mpl image-comparison tests
docs/
    conf.py, index.rst, usage.rst, api.rst
```
