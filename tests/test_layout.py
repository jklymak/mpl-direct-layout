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


# ---------------------------------------------------------------------------
# Colorbar overlap tests
# ---------------------------------------------------------------------------

@pytest.mark.mpl_image_compare(style='mpl20', tolerance=5)
def test_colorbars_no_overlapV():
    """Vertical colorbars on multiple axes should not overlap."""
    fig = plt.figure(figsize=(2, 4), layout='direct')
    axs = fig.subplots(2, 1, sharex=True, sharey=True)
    for ax in axs:
        ax.yaxis.set_major_formatter(ticker.NullFormatter())
        ax.tick_params(axis='both', direction='in')
        pcm = ax.pcolormesh([[1, 2], [3, 4]])
        fig.colorbar(pcm, ax=ax, orientation='vertical')
    fig.suptitle('Vertical colorbars')
    return fig


@pytest.mark.mpl_image_compare(style='mpl20', tolerance=5)
def test_colorbars_no_overlapH():
    """Horizontal colorbars on multiple axes should not overlap."""
    fig = plt.figure(figsize=(4, 2), layout='direct')
    fig.suptitle('Horizontal colorbars')
    axs = fig.subplots(1, 2, sharex=True, sharey=True)
    for ax in axs:
        ax.yaxis.set_major_formatter(ticker.NullFormatter())
        ax.tick_params(axis='both', direction='in')
        pcm = ax.pcolormesh([[1, 2], [3, 4]])
        fig.colorbar(pcm, ax=ax, orientation='horizontal')
    return fig


def test_submerged_subfig():
    """
    Test that the layout logic does not get called multiple times
    on same axes if it is already in a subfigure.
    """
    fig = plt.figure(figsize=(4, 5), layout='direct')
    figures = fig.subfigures(3, 1)
    axs = []
    for f in figures.flatten():
        gs = f.add_gridspec(2, 2)
        for i in range(2):
            axs += [f.add_subplot(gs[i, 0])]
            axs[-1].plot([1, 2])
        f.add_subplot(gs[:, 1]).plot([1, 2])
    fig.canvas.draw()
    # All left axes should have the same height
    for ax in axs[1:]:
        assert np.allclose(ax.get_position().bounds[-1],
                           axs[0].get_position().bounds[-1], atol=1e-6)


# ---------------------------------------------------------------------------
# Compressed layout tests
# ---------------------------------------------------------------------------

@pytest.mark.mpl_image_compare(style='mpl20', tolerance=5)
def test_compressed_2x2_imshow():
    """Canonical compressed layout: 2x2 grid of square images on a wide figure.

    With compress=True the axes should be pulled together with minimal lateral
    whitespace; the slack from the fixed-aspect shrinkage goes into the outer
    margins, centring the grid.
    """
    rng = np.random.default_rng(0)
    fig, axs = plt.subplots(2, 2, layout='direct-compressed', figsize=(10, 4))
    for ax in axs.flat:
        ax.imshow(rng.standard_normal((10, 10)))
    return fig


@pytest.mark.mpl_image_compare(style='mpl20', tolerance=5)
def test_compressed_no_aspect_noop():
    """compress=True on axes without a fixed aspect must be a no-op visually.

    The result should be indistinguishable from compress=False.
    """
    fig, axs = plt.subplots(2, 2, layout='direct-compressed', figsize=(8, 6))
    for ax in axs.flat:
        example_plot(ax, fontsize=12)
    return fig


@pytest.mark.mpl_image_compare(style='mpl20', tolerance=5)
def test_compressed_with_colorbar():
    """Compressed layout with a shared colorbar.

    The colorbar should reposition correctly after the compression pass.
    """
    rng = np.random.default_rng(1)
    fig, axs = plt.subplots(2, 2, layout='direct-compressed', figsize=(10, 5))
    for ax in axs.flat:
        im = ax.imshow(rng.standard_normal((10, 10)), vmin=-2, vmax=2)
    fig.colorbar(im, ax=axs, shrink=0.6)
    return fig


def test_compressed_idempotency():
    """Drawing a compressed figure twice must not move the axes.

    After the first draw the slack should be essentially zero, so the
    second draw should produce positions that are identical (within floating-
    point tolerance) to the first.
    """
    rng = np.random.default_rng(2)
    fig, axs = plt.subplots(2, 2, layout='direct-compressed', figsize=(10, 4))
    for ax in axs.flat:
        ax.imshow(rng.standard_normal((10, 10)))

    # First draw
    fig.canvas.draw()
    positions_first = [ax.get_position().bounds for ax in axs.flat]

    # Second draw
    fig.canvas.draw()
    positions_second = [ax.get_position().bounds for ax in axs.flat]

    for p1, p2 in zip(positions_first, positions_second):
        assert np.allclose(p1, p2, atol=1e-4), (
            f"Positions changed between draws: {p1} vs {p2}")


def test_compressed_layout_reduces_whitespace():
    """Compressed layout must produce less lateral whitespace than uncompressed.

    On a wide figure with square images the total width occupied by the axes
    group should be smaller (i.e. the left edge is further right) when
    compress=False, because compression moves the slack into the outer margins.
    """
    rng = np.random.default_rng(3)

    fig_nc, axs_nc = plt.subplots(2, 2, layout='direct', figsize=(10, 4))
    for ax in axs_nc.flat:
        ax.imshow(rng.standard_normal((10, 10)))
    fig_nc.canvas.draw()
    x0_nc = min(ax.get_position().x0 for ax in axs_nc.flat)
    x1_nc = max(ax.get_position().x1 for ax in axs_nc.flat)
    plt.close(fig_nc)

    fig_c, axs_c = plt.subplots(2, 2, layout='direct-compressed', figsize=(10, 4))
    for ax in axs_c.flat:
        ax.imshow(rng.standard_normal((10, 10)))
    fig_c.canvas.draw()
    x0_c = min(ax.get_position().x0 for ax in axs_c.flat)
    x1_c = max(ax.get_position().x1 for ax in axs_c.flat)
    plt.close(fig_c)

    # The compressed grid should be narrower (less total span) than uncompressed
    span_nc = x1_nc - x0_nc
    span_c  = x1_c  - x0_c
    assert span_c < span_nc, (
        f"Compressed span ({span_c:.4f}) should be less than "
        f"uncompressed span ({span_nc:.4f})"
    )


# ---------------------------------------------------------------------------
# Mixed-aspect compressed layout tests
#
# Each test has a 2×2 grid on a wide figure (10×4 in) with compress=True.
# Axes labelled by (row, col): 00 01 / 10 11.
# 'equal' axes use imshow (square image → fixed aspect).
# 'auto'  axes use a simple line plot.
# ---------------------------------------------------------------------------

def _make_mixed_aspect_fig(aspects):
    """Return a compressed 2×2 figure with per-axis aspects.

    Parameters
    ----------
    aspects : sequence of 4 str, row-major order (00, 01, 10, 11)
        Each element is ``'equal'`` or ``'auto'``.
    """
    rng = np.random.default_rng(42)
    fig, axs = plt.subplots(2, 2, layout='direct-compressed', figsize=(10, 4))
    for ax, asp in zip(axs.flat, aspects):
        if asp == 'equal':
            ax.imshow(rng.standard_normal((10, 10)))
        else:
            example_plot(ax, fontsize=10, nodec=True)
    return fig


@pytest.mark.mpl_image_compare(style='mpl20', tolerance=5)
def test_compressed_mixed_all_equal():
    """All four axes have equal aspect — full compression on both axes."""
    return _make_mixed_aspect_fig(['equal', 'equal', 'equal', 'equal'])


@pytest.mark.mpl_image_compare(style='mpl20', tolerance=5)
def test_compressed_mixed_all_auto():
    """All four axes are auto — compression is a no-op."""
    return _make_mixed_aspect_fig(['auto', 'auto', 'auto', 'auto'])


@pytest.mark.mpl_image_compare(style='mpl20', tolerance=5)
def test_compressed_mixed_top_equal():
    """Top row equal, bottom row auto."""
    return _make_mixed_aspect_fig(['equal', 'equal', 'auto', 'auto'])


@pytest.mark.mpl_image_compare(style='mpl20', tolerance=5)
def test_compressed_mixed_left_equal():
    """Left column equal, right column auto."""
    return _make_mixed_aspect_fig(['equal', 'auto', 'equal', 'auto'])


@pytest.mark.mpl_image_compare(style='mpl20', tolerance=5)
def test_compressed_mixed_diagonal_equal():
    """Diagonal axes equal (top-left, bottom-right), off-diagonal auto."""
    return _make_mixed_aspect_fig(['equal', 'auto', 'auto', 'equal'])


@pytest.mark.mpl_image_compare(style='mpl20', tolerance=5)
def test_compressed_mixed_one_equal():
    """Only top-left axis has equal aspect, the other three are auto."""
    return _make_mixed_aspect_fig(['equal', 'auto', 'auto', 'auto'])


# Numeric checks for the mixed-aspect cases ---------------------------------

@pytest.mark.parametrize('figsize,aspects,expect_w_compress,expect_h_compress', [
    # Wide figure (10×4): cells are wider than tall, so square images lose
    # width but not height — only horizontal compression.
    ((10, 4), ['equal', 'equal', 'equal', 'equal'], True,  False),
    ((10, 4), ['auto',  'auto',  'auto',  'auto'],  False, False),
    ((10, 4), ['equal', 'equal', 'auto',  'auto'],  True,  False),
    ((10, 4), ['equal', 'auto',  'equal', 'auto'],  True,  False),
    ((10, 4), ['equal', 'auto',  'auto',  'auto'],  True,  False),
    # Tall figure (4×10): cells are taller than wide, so square images lose
    # height but not width — only vertical compression.
    ((4, 10), ['equal', 'equal', 'equal', 'equal'], False, True),
    ((4, 10), ['auto',  'auto',  'auto',  'auto'],  False, False),
    ((4, 10), ['auto',  'auto',  'equal', 'equal'], False, True),
    ((4, 10), ['equal', 'auto',  'equal', 'auto'],  False, True),
    ((4, 10), ['auto',  'auto',  'auto',  'equal'],  False, True),
])
def test_compressed_mixed_aspect_directions(figsize, aspects,
                                            expect_w_compress, expect_h_compress):
    """Check which directions are compressed for each aspect/figsize combination.

    On a wide figure (cells wider than tall) square images shed width only.
    On a tall figure (cells taller than wide) they shed height only.
    Compression should shift x0 (horizontal) or y0 (vertical) relative to the
    uncompressed baseline accordingly.
    """
    def _make(layout):
        rng = np.random.default_rng(42)
        fig, axs = plt.subplots(2, 2, layout=layout, figsize=figsize)
        for ax, asp in zip(axs.flat, aspects):
            if asp == 'equal':
                ax.imshow(rng.standard_normal((10, 10)))
            else:
                ax.plot([1, 2])
        fig.canvas.draw()
        return fig, axs

    fig_nc, axs_nc = _make('direct')
    x0_nc = min(ax.get_position().x0 for ax in axs_nc.flat)
    y0_nc = min(ax.get_position().y0 for ax in axs_nc.flat)
    plt.close(fig_nc)

    fig_c, axs_c = _make('direct-compressed')
    x0_c = min(ax.get_position().x0 for ax in axs_c.flat)
    y0_c = min(ax.get_position().y0 for ax in axs_c.flat)
    plt.close(fig_c)

    if expect_w_compress:
        assert x0_c > x0_nc + 1e-4, (
            f"Expected horizontal compression for figsize={figsize} aspects={aspects}: "
            f"x0_compressed={x0_c:.4f} should be > x0_uncompressed={x0_nc:.4f}")
    else:
        assert abs(x0_c - x0_nc) < 1e-4, (
            f"Expected no horizontal compression for figsize={figsize} aspects={aspects}: "
            f"x0_compressed={x0_c:.4f} vs x0_uncompressed={x0_nc:.4f}")

    if expect_h_compress:
        assert y0_c > y0_nc + 1e-4, (
            f"Expected vertical compression for figsize={figsize} aspects={aspects}: "
            f"y0_compressed={y0_c:.4f} should be > y0_uncompressed={y0_nc:.4f}")
    else:
        assert abs(y0_c - y0_nc) < 1e-4, (
            f"Expected no vertical compression for figsize={figsize} aspects={aspects}: "
            f"y0_compressed={y0_c:.4f} vs y0_uncompressed={y0_nc:.4f}")
