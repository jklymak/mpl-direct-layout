"""
Image-comparison tests for mpl_direct_layout.

Run to generate baselines (first time)::

    pytest tests/ --mpl-generate-path=tests/baseline_images

Run with comparison::

    pytest tests/ --mpl

The test helpers ``example_plot`` and ``example_pcolor`` are intentionally
similar to those in matplotlib's own ``test_constrainedlayout.py`` so that
the two layout engines can be compared visually.
"""

import numpy as np
import pytest

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.ticker as ticker

import mpl_direct_layout  # registers 'direct' layout key  # noqa: F401


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def example_plot(ax, fontsize=12, nodec=False):
    ax.plot([1, 2])
    ax.locator_params(nbins=3)
    if not nodec:
        ax.set_xlabel('x-label', fontsize=fontsize)
        ax.set_ylabel('y-label', fontsize=fontsize)
        ax.set_title('Title', fontsize=fontsize)
    else:
        ax.set_xticklabels([])
        ax.set_yticklabels([])


def example_pcolor(ax, fontsize=12):
    dx, dy = 0.6, 0.6
    y, x = np.mgrid[slice(-3, 3 + dy, dy), slice(-3, 3 + dx, dx)]
    z = (1 - x / 2. + x**5 + y**3) * np.exp(-x**2 - y**2)
    pcm = ax.pcolormesh(x, y, z[:-1, :-1], cmap='RdBu_r', vmin=-1., vmax=1.,
                        rasterized=True)
    ax.set_xlabel('x-label', fontsize=fontsize)
    ax.set_ylabel('y-label', fontsize=fontsize)
    ax.set_title('Title', fontsize=fontsize)
    return pcm


# ---------------------------------------------------------------------------
# Basic grid tests
# ---------------------------------------------------------------------------

@pytest.mark.mpl_image_compare(style='mpl20', tolerance=5)
def test_single_axes():
    """Single axes with labels and title."""
    fig = plt.figure(layout='direct')
    ax = fig.add_subplot()
    example_plot(ax, fontsize=24)
    return fig


@pytest.mark.mpl_image_compare(style='mpl20', tolerance=5)
def test_2x2_grid():
    """2×2 subplot grid with axis labels."""
    fig, axs = plt.subplots(2, 2, layout='direct')
    for ax in axs.flat:
        example_plot(ax, fontsize=24)
    return fig


@pytest.mark.mpl_image_compare(style='mpl20', tolerance=5)
def test_3x3_grid():
    """3×3 subplot grid."""
    fig, axs = plt.subplots(3, 3, layout='direct')
    for ax in axs.flat:
        example_plot(ax, fontsize=12)
    return fig


@pytest.mark.mpl_image_compare(style='mpl20', tolerance=5)
def test_suptitle():
    """suptitle, supxlabel, supylabel with 2×2 grid."""
    fig, axs = plt.subplots(2, 2, layout='direct')
    for ax in axs.flat:
        example_plot(ax, fontsize=12)
    fig.suptitle('Suptitle', fontsize=18)
    fig.supxlabel('Figure x-label')
    fig.supylabel('Figure y-label')
    return fig


# ---------------------------------------------------------------------------
# Colorbar tests
# ---------------------------------------------------------------------------

@pytest.mark.mpl_image_compare(style='mpl20', tolerance=5)
def test_colorbar_right():
    """Colorbars on the right of each axes in a 2×2 grid."""
    fig, axs = plt.subplots(2, 2, layout='direct')
    for ax in axs.flat:
        pcm = example_pcolor(ax, fontsize=24)
        fig.colorbar(pcm, ax=ax)
    return fig


@pytest.mark.mpl_image_compare(style='mpl20', tolerance=5)
def test_colorbar_locations():
    """Colorbars in all four locations."""
    fig, axs = plt.subplots(2, 2, layout='direct')
    locations = ['right', 'left', 'top', 'bottom']
    for ax, loc in zip(axs.flat, locations):
        pcm = example_pcolor(ax, fontsize=12)
        fig.colorbar(pcm, ax=ax, location=loc)
    return fig


@pytest.mark.mpl_image_compare(style='mpl20', tolerance=5)
def test_shared_colorbar_2x2():
    """Single shared colorbar for all four axes in a 2×2 grid."""
    fig, axs = plt.subplots(2, 2, layout='direct')
    for ax in axs.flat:
        pcm = example_pcolor(ax, fontsize=24)
    fig.colorbar(pcm, ax=axs, shrink=0.6)
    return fig


@pytest.mark.mpl_image_compare(style='mpl20', tolerance=5)
def test_shared_colorbar_bottom():
    """Single shared colorbar at the bottom."""
    fig, axs = plt.subplots(2, 2, layout='direct')
    for ax in axs.flat:
        pcm = example_pcolor(ax, fontsize=24)
    fig.colorbar(pcm, ax=axs, shrink=0.6, location='bottom')
    return fig


@pytest.mark.mpl_image_compare(style='mpl20', tolerance=5)
def test_colorbar_top_row():
    """Colorbar for top row only in a 2×2 grid."""
    fig, axs = plt.subplots(2, 2, layout='direct')
    for ax in axs.flat:
        pcm = example_pcolor(ax, fontsize=24)
    # Colorbar only for top row
    fig.colorbar(pcm, ax=axs[0, :], location='bottom')
    return fig


@pytest.mark.mpl_image_compare(style='mpl20', tolerance=5)
def test_suptitle_with_colorbar():
    """suptitle combined with a shared colorbar."""
    fig, axs = plt.subplots(2, 2, layout='direct')
    for ax in axs.flat:
        pcm = example_pcolor(ax, fontsize=24)
        ax.set_xlabel('')
        ax.set_ylabel('')
    fig.colorbar(pcm, ax=axs, shrink=0.6)
    fig.suptitle('Test Suptitle', fontsize=28)
    return fig


# ---------------------------------------------------------------------------
# Mosaic / spanning axes
# ---------------------------------------------------------------------------

@pytest.mark.mpl_image_compare(style='mpl20', tolerance=5)
def test_mosaic_basic():
    """Simple mosaic with a vertically spanning axis."""
    fig = plt.figure(layout='direct')
    axd = fig.subplot_mosaic([['a', 'b'],
                               ['c', 'b']])
    for label, ax in axd.items():
        example_plot(ax, fontsize=14)
    return fig


@pytest.mark.mpl_image_compare(style='mpl20', tolerance=5)
def test_mosaic_colorbar_spanning():
    """Colorbar on a vertically spanning mosaic axis."""
    fig = plt.figure(layout='direct')
    axd = fig.subplot_mosaic([['a', 'b'],
                               ['c', 'b']])
    for label, ax in axd.items():
        pcm = example_pcolor(ax, fontsize=12)
    fig.colorbar(pcm, ax=axd['b'], location='right')
    return fig


@pytest.mark.mpl_image_compare(style='mpl20', tolerance=5)
def test_mosaic_shared_colorbar():
    """Shared colorbar across a group of mosaic axes adjacent to another."""
    fig = plt.figure(figsize=(10, 6), layout='direct')
    axd = fig.subplot_mosaic([['a', 'a', 'b'],
                               ['c', 'd', 'b']])
    vmin, vmax = -2, 2
    for label, ax in axd.items():
        pcm = ax.pcolormesh(np.random.default_rng(0).standard_normal((20, 20)),
                            vmin=vmin, vmax=vmax)
        ax.set_title(f'Axes {label.upper()}')
        ax.set_xlabel(f'{label} x-axis')
        ax.set_ylabel(f'{label} y-axis')
    fig.colorbar(pcm, ax=[axd['a'], axd['c'], axd['d']], location='right')
    return fig


@pytest.mark.mpl_image_compare(style='mpl20', tolerance=5)
def test_uneven_gridspec():
    """Spanning axes in an uneven GridSpec."""
    fig = plt.figure(layout='direct')
    gs = gridspec.GridSpec(3, 3, figure=fig)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1:])
    ax3 = fig.add_subplot(gs[1:, 0:2])
    ax4 = fig.add_subplot(gs[1:, -1])
    for ax in (ax1, ax2, ax3, ax4):
        example_plot(ax)
    return fig


# ---------------------------------------------------------------------------
# Width / height ratios
# ---------------------------------------------------------------------------

@pytest.mark.mpl_image_compare(style='mpl20', tolerance=5)
def test_width_height_ratios():
    """GridSpec with non-uniform width and height ratios."""
    fig = plt.figure(layout='direct')
    gs = gridspec.GridSpec(2, 3, figure=fig,
                           width_ratios=[3, 1, 2],
                           height_ratios=[2, 1])
    for i in range(2):
        for j in range(3):
            ax = fig.add_subplot(gs[i, j])
            example_plot(ax, fontsize=9)
    return fig


# ---------------------------------------------------------------------------
# Subfigures
# ---------------------------------------------------------------------------

@pytest.mark.mpl_image_compare(style='mpl20', tolerance=5)
def test_subfigures():
    """Two subfigures side by side, each with its own 2×1 grid."""
    fig = plt.figure(layout='direct', figsize=(8, 4))
    sfigs = fig.subfigures(1, 2)
    for sfig in sfigs:
        axs = sfig.subplots(2, 1)
        for ax in axs:
            example_plot(ax, fontsize=10)
        sfig.suptitle('Subfigure', fontsize=12)
    fig.suptitle('Root suptitle')
    return fig


@pytest.mark.mpl_image_compare(style='mpl20', tolerance=5)
def test_subfigures_colorbars():
    """Subfigures each containing a pcolor plot with colorbar."""
    fig = plt.figure(layout='direct', figsize=(10, 4))
    sfigs = fig.subfigures(1, 2)
    for sfig in sfigs:
        ax = sfig.subplots()
        pcm = example_pcolor(ax, fontsize=10)
        sfig.colorbar(pcm, ax=ax)
        sfig.suptitle('Subfig')
    return fig


# ---------------------------------------------------------------------------
# Padding / margins
# ---------------------------------------------------------------------------

@pytest.mark.mpl_image_compare(style='mpl20', tolerance=5)
def test_custom_padding():
    """Larger h_pad and w_pad than the default."""
    fig, axs = plt.subplots(2, 2, layout='direct')
    for ax in axs.flat:
        pcm = example_pcolor(ax, fontsize=12)
        fig.colorbar(pcm, ax=ax, shrink=0.6)
    fig.get_layout_engine().set(w_pad=24. / 72., h_pad=24. / 72.)
    return fig


@pytest.mark.mpl_image_compare(style='mpl20', tolerance=5)
def test_outer_margins():
    """Non-default outer margins leave visible whitespace at figure edges."""
    fig, axs = plt.subplots(2, 2, layout='direct')
    for ax in axs.flat:
        example_plot(ax, fontsize=12)
    fig.get_layout_engine().set(left=0.3, right=0.3, top=0.3, bottom=0.3)
    return fig
