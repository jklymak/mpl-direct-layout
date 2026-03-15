# mpl-direct-layout — Copilot Project Context

## What this project is

`mpl-direct-layout` is a pip-installable Python package that provides `DirectLayoutEngine`,
a two-pass algebraic layout engine for Matplotlib. It is an alternative to
`constrained_layout` / `tight_layout` that lets users specify margins in physical units
(inches) rather than relative fractions.

It was developed in `/Users/jklymak/matplotlib/direct_layout_engine.py` and then
packaged here.

## Package structure

```
mpl-direct-layout/
├── pyproject.toml          # hatchling build, pytest-mpl config
├── README.md
├── LICENSE                 # MIT
├── src/
│   └── mpl_direct_layout/
│       ├── __init__.py     # imports + calls register()
│       ├── _engine.py      # DirectLayoutEngine (full implementation)
│       └── _register.py    # register() / unregister() monkey-patch
├── tests/
│   ├── conftest.py         # autouse rc_context fixture (style='mpl20')
│   ├── test_layout.py      # 18 pytest-mpl image comparison tests
│   └── baseline_images/    # 18 PNG baselines (generated, not hand-made)
└── docs/
    ├── conf.py             # Sphinx config
    ├── index.rst
    ├── usage.rst
    └── api.rst
```

## Python environment

The project is tested with the pixi environment from
`/Users/jklymak/matplotlib/pixi.toml` (Python 3.11.14, Matplotlib 3.11.0.dev).

The package is installed **editable** into that environment:
```bash
pixi run --manifest-path /Users/jklymak/matplotlib/pixi.toml pip install -e ".[test]"
```

## Running tests

```bash
# run all 18 image-comparison tests
cd ~/Dropbox/mpl-direct-layout
pixi run --manifest-path /Users/jklymak/matplotlib/pixi.toml \
  python -m pytest tests/ --mpl -p no:warnings

# regenerate baselines (after intentional engine changes)
pixi run --manifest-path /Users/jklymak/matplotlib/pixi.toml \
  python -m pytest tests/ --mpl-generate-path=tests/baseline_images -p no:warnings
```

pytest-mpl config lives in `pyproject.toml`:
```toml
[tool.pytest.ini_options]
addopts = "--mpl-default-tolerance=2 --mpl-baseline-path=tests/baseline_images"
testpaths = ["tests"]
```

## How the engine works

`DirectLayoutEngine` is a two-pass layout engine:

1. **Pass 1 — measure:** Walk all axes, collect tick/label/title decoration sizes
   (via `tight_bbox`), compute the margin budget needed on each side of the figure.
2. **Pass 2 — position:** Compute axes positions algebraically from the margin budget,
   width/height ratios, and any colorbar space reservations; call `ax.set_position()`.

Registration is via monkey-patching `matplotlib.figure.Figure.set_layout_engine` to
recognise `layout='direct'`. Calling `import mpl_direct_layout` is all that is needed.

### Key API for users

```python
import mpl_direct_layout  # activates the engine
fig, ax = plt.subplots(layout='direct')

# Optional keyword arguments to set_layout_engine / Figure constructor:
#   left_margin_inches, right_margin_inches, top_margin_inches, bottom_margin_inches
#   (all default to 'auto' — engine measures and allocates automatically)
#   width_ratios, height_ratios  (list of floats, like GridSpec)
#   hspace_inches, wspace_inches (fixed spacing between axes, in inches)
```

### Colorbar support

Colorbars created with `fig.colorbar(..., ax=<one or more axes>)` are detected
automatically. The engine:
- Removes the colorbar axes from the main grid
- Reserves space for it adjacent to the parent axes
- Positions it to align with the tight bounding box of the parent(s)

Key fix history (all applied in `_engine.py`):
- Spanning colorbar margins use `+=` (not `max()`) to accumulate decoration + colorbar space
- Right colorbar uses `max(tight_bbox.x1)` across all parents, not the axes box edge
- `neighbor_pad_inches = 0.1` buffer added to all four direction branches
- `cax.set_box_aspect(None)` called before `cax.set_position()` to remove aspect=20 cap

## Status

All 18 pytest-mpl image tests pass (as of 2026-03-14).
