"""
Direct Layout Engine - A kiwisolver-free alternative to constrained_layout.

This module provides a LayoutEngine that uses direct equation solving instead
of constraint solving to position axes on a grid.
"""

import numpy as np
from matplotlib.layout_engine import LayoutEngine
from matplotlib.transforms import Bbox
from matplotlib import artist as martist
import matplotlib as mpl


def _fig_size_inches(fig):
    """Return (width_inches, height_inches) for a Figure or SubFigure."""
    root = fig.get_figure(root=True)
    root_w = root.get_figwidth()
    root_h = root.get_figheight()
    try:
        # SubFigure has bbox_relative
        bb = fig.bbox_relative
        return root_w * bb.width, root_h * bb.height
    except AttributeError:
        return root_w, root_h


class DirectLayoutEngine(LayoutEngine):
    """
    A layout engine that uses direct equation solving instead of kiwisolver.

    Positions axes on a grid by measuring decoration sizes (tick labels,
    axis labels, titles, colorbars) and solving for positions algebraically.

    Usage::

        import mpl_direct_layout
        import matplotlib.pyplot as plt

        fig, axs = plt.subplots(2, 2, layout='direct')

    Or explicitly::

        fig = plt.figure()
        fig.set_layout_engine('direct')
        axs = fig.subplots(2, 2)

    Parameters
    ----------
    h_pad, w_pad : float
        Padding between axes in inches.
        Defaults to 3 points (3/72 ≈ 0.042 in).
    rect : tuple of 4 floats
        Rectangle ``(left, bottom, width, height)`` in figure coordinates
        (each 0–1) within which to perform layout.
    left, right, top, bottom : float, optional
        Fixed outer margins in inches from the figure edges.
        Defaults: 6 points (6/72 ≈ 0.083 in) on all sides.
    suptitle_pad : float, optional
        Gap in inches between suptitle / supxlabel / supylabel and the axes
        content.  Default: 0.1 in.
    """

    _adjust_compatible = False
    _colorbar_gridspec = False

    def __init__(self, *, h_pad=None, w_pad=None, rect=(0, 0, 1, 1),
                 left=None, right=None, top=None, bottom=None,
                 suptitle_pad=None, **kwargs):
        super().__init__(**kwargs)
        default_pad = 0.1  # inches between axes
        default_margin = 0.1  # inches at figure edges
        self.set(h_pad=h_pad if h_pad is not None else default_pad,
                 w_pad=w_pad if w_pad is not None else default_pad,
                 rect=rect,
                 left=left if left is not None else default_margin,
                 right=right if right is not None else default_margin,
                 top=top if top is not None else default_margin,
                 bottom=bottom if bottom is not None else default_margin,
                 suptitle_pad=suptitle_pad if suptitle_pad is not None else 0.1)

    def set(self, *, h_pad=None, w_pad=None, rect=None,
            left=None, right=None, top=None, bottom=None,
            suptitle_pad=None):
        """
        Set layout parameters.

        Parameters
        ----------
        h_pad, w_pad : float
            Padding between axes in inches.
        rect : tuple of 4 floats
            ``(left, bottom, width, height)`` layout rectangle in figure coords.
        left, right, top, bottom : float
            Outer margins in inches from figure edges.
        suptitle_pad : float
            Gap in inches between suptitle/supxlabel/supylabel and axes.
        """
        if h_pad is not None:
            self._params['h_pad'] = h_pad
        if w_pad is not None:
            self._params['w_pad'] = w_pad
        if rect is not None:
            self._params['rect'] = rect
        if left is not None:
            self._params['left'] = left
        if right is not None:
            self._params['right'] = right
        if top is not None:
            self._params['top'] = top
        if bottom is not None:
            self._params['bottom'] = bottom
        if suptitle_pad is not None:
            self._params['suptitle_pad'] = suptitle_pad

    def execute(self, fig):
        """
        Perform layout on *fig*.  Called automatically during the draw cycle.
        """
        from matplotlib.figure import SubFigure

        subfigs = fig.subfigs if hasattr(fig, 'subfigs') and fig.subfigs else []

        if subfigs:
            for subfig in subfigs:
                subfig._redo_transform_rel_fig()
            self._adjust_subfig_bboxes_for_suptitles(fig, subfigs)
            for subfig in subfigs:
                self._execute_for_subfigure(subfig)

        direct_axes = [ax for ax in fig.axes
                       if ax.get_subplotspec() is not None
                       and not hasattr(ax, '_colorbar_info')
                       and ax.get_figure(root=False) is fig]

        if not direct_axes:
            return

        self._execute_for_fig_with_axes(fig, direct_axes, rect=None)

    # ------------------------------------------------------------------
    # Subfigure helpers
    # ------------------------------------------------------------------

    def _adjust_subfig_bboxes_for_suptitles(self, fig, subfigs):
        """Shrink subfigure bboxes to make room for fig-level super labels."""
        renderer = fig._get_renderer()
        inv = fig.transSubfigure.inverted().transform_bbox
        fig_width_inches, fig_height_inches = _fig_size_inches(fig)
        gap_inches = self._params['suptitle_pad']

        top_shrink = bottom_shrink = left_shrink = 0.0

        if fig._suptitle is not None and fig._suptitle.get_in_layout():
            bbox = inv(fig._suptitle.get_window_extent(renderer))
            top_shrink = bbox.height + gap_inches / fig_height_inches

        if fig._supxlabel is not None and fig._supxlabel.get_in_layout():
            bbox = inv(fig._supxlabel.get_window_extent(renderer))
            bottom_shrink = bbox.height + gap_inches / fig_height_inches

        if fig._supylabel is not None and fig._supylabel.get_in_layout():
            bbox = inv(fig._supylabel.get_window_extent(renderer))
            left_shrink = bbox.width + gap_inches / fig_width_inches

        if top_shrink == bottom_shrink == left_shrink == 0.0:
            return

        for subfig in subfigs:
            bb = subfig.bbox_relative
            x0, y0, x1, y1 = bb.x0, bb.y0, bb.x1, bb.y1
            avail_height = 1.0 - top_shrink - bottom_shrink
            avail_width = 1.0 - left_shrink
            subfig.bbox_relative.p0 = (left_shrink + x0 * avail_width,
                                       bottom_shrink + y0 * avail_height)
            subfig.bbox_relative.p1 = (left_shrink + x1 * avail_width,
                                       bottom_shrink + y1 * avail_height)

    def _execute_for_subfigure(self, subfig):
        """Run layout for a subfigure in subfigure-local coordinates (0–1)."""
        nested = subfig.subfigs if hasattr(subfig, 'subfigs') and subfig.subfigs else []

        if nested:
            for n in nested:
                n._redo_transform_rel_fig()
            self._adjust_subfig_bboxes_for_suptitles(subfig, nested)
            for n in nested:
                self._execute_for_subfigure(n)

        axes_list = [ax for ax in subfig.axes
                     if ax.get_subplotspec() is not None
                     and not hasattr(ax, '_colorbar_info')]
        if not axes_list:
            return

        root_fig = subfig.get_figure(root=True)
        bbox = subfig.bbox_relative
        sw = root_fig.get_figwidth() * bbox.width
        sh = root_fig.get_figheight() * bbox.height
        self._execute_for_fig_with_axes(subfig, axes_list, rect=[0, 0, 1, 1],
                                        fig_width_inches=sw,
                                        fig_height_inches=sh)

    # ------------------------------------------------------------------
    # Core layout
    # ------------------------------------------------------------------

    def _execute_for_fig_with_axes(self, fig, axes_list, rect,
                                    fig_width_inches=None, fig_height_inches=None):
        """Group axes by gridspec and apply layout to each group."""
        from matplotlib.figure import SubFigure
        is_subfigure = isinstance(fig, SubFigure)

        gridspec_to_axes = {}
        for ax in axes_list:
            gs = ax.get_subplotspec().get_gridspec()
            gridspec_to_axes.setdefault(gs, []).append(ax)

        for gs, axes in gridspec_to_axes.items():
            nrows, ncols = gs.nrows, gs.ncols

            width_ratios = gs.get_width_ratios()
            height_ratios = gs.get_height_ratios()
            width_ratios = np.ones(ncols) if width_ratios is None else np.array(width_ratios)
            height_ratios = np.ones(nrows) if height_ratios is None else np.array(height_ratios)

            axes_grid = np.empty((nrows, ncols), dtype=object)
            spanning_axes = []

            for ax in axes:
                ss = ax.get_subplotspec()
                if ss.rowspan.start != ss.rowspan.stop - 1 or \
                   ss.colspan.start != ss.colspan.stop - 1:
                    spanning_axes.append(ax)
                    continue
                axes_grid[ss.rowspan.start, ss.colspan.start] = ax

            kw = dict(fig_width_inches=fig_width_inches,
                      fig_height_inches=fig_height_inches)
            # Two passes – second pass converges after positions are known
            for _ in range(2):
                self._apply_layout_to_grid(
                    fig, axes_grid, nrows, ncols, spanning_axes,
                    width_ratios, height_ratios, is_subfigure, rect, **kw)

    def _apply_layout_to_grid(self, fig, axes_grid, nrows, ncols,
                               spanning_axes=None, width_ratios=None,
                               height_ratios=None, is_subfigure=False,
                               subfig_rect=None, fig_width_inches=None,
                               fig_height_inches=None):
        """Core algebraic positioning for one gridspec."""
        if spanning_axes is None:
            spanning_axes = []

        renderer = fig._get_renderer()
        if fig_width_inches is None or fig_height_inches is None:
            fig_width_inches, fig_height_inches = _fig_size_inches(fig)

        h_pad = self._params['h_pad'] / fig_height_inches
        w_pad = self._params['w_pad'] / fig_width_inches

        rect = list(subfig_rect if subfig_rect is not None
                    else self._params['rect'])

        # Outer margins
        lm = self._params['left']  / fig_width_inches
        rm = self._params['right'] / fig_width_inches
        tm = self._params['top']   / fig_height_inches
        bm = self._params['bottom']/ fig_height_inches
        rect[0] += lm
        rect[1] += bm
        rect[2] -= lm + rm
        rect[3] -= tm + bm

        rect = self._adjust_rect_for_suptitles(fig, renderer, rect)

        # --- Margin array [row, col, side]: L=0 R=1 B=2 T=3 ---
        margins = np.zeros((nrows, ncols, 4))

        for i in range(nrows):
            for j in range(ncols):
                ax = axes_grid[i, j]
                if ax is None or not ax.get_visible():
                    continue
                m = self._measure_axes_decorations(ax, renderer, fig)
                margins[i, j] = [m['left'], m['right'], m['bottom'], m['top']]
                cb = self._measure_colorbar_space(ax, renderer, fig,
                                                  axes_grid, nrows, ncols)
                if cb:
                    margins[i, j, 0] += cb.get('left', 0)
                    margins[i, j, 1] += cb.get('right', 0)
                    margins[i, j, 2] += cb.get('bottom', 0)
                    margins[i, j, 3] += cb.get('top', 0)

        for ax in spanning_axes:
            if not ax.get_visible():
                continue
            m = self._measure_axes_decorations(ax, renderer, fig)
            ss = ax.get_subplotspec()
            cs, ce = ss.colspan.start, ss.colspan.stop - 1
            rs, re = ss.rowspan.start, ss.rowspan.stop - 1
            for i in range(ss.rowspan.start, ss.rowspan.stop):
                margins[i, cs, 0] = max(margins[i, cs, 0], m['left'])
                margins[i, ce, 1] = max(margins[i, ce, 1], m['right'])
            for j in range(ss.colspan.start, ss.colspan.stop):
                margins[re, j, 2] = max(margins[re, j, 2], m['bottom'])
                margins[rs, j, 3] = max(margins[rs, j, 3], m['top'])

            cb = self._measure_colorbar_space_for_spanning_axis(
                ax, renderer, fig, ss, nrows, ncols)
            if cb:
                loc = cb['location']
                if loc == 'right':
                    for i in range(ss.rowspan.start, ss.rowspan.stop):
                        margins[i, ce, 1] += cb.get('right', 0)
                elif loc == 'left':
                    for i in range(ss.rowspan.start, ss.rowspan.stop):
                        margins[i, cs, 0] += cb.get('left', 0)
                elif loc == 'top':
                    for j in range(ss.colspan.start, ss.colspan.stop):
                        margins[rs, j, 3] += cb.get('top', 0)
                elif loc == 'bottom':
                    for j in range(ss.colspan.start, ss.colspan.stop):
                        margins[re, j, 2] += cb.get('bottom', 0)

        # --- Aggregate per-column and per-row ---
        left_margins  = np.array([margins[:, j, 0].max()
                                   if np.any(margins[:, j, :]) else 0
                                   for j in range(ncols)])
        right_margins = np.array([margins[:, j, 1].max()
                                   if np.any(margins[:, j, :]) else 0
                                   for j in range(ncols)])
        bottom_margins = np.array([margins[i, :, 2].max()
                                    if np.any(margins[i, :, :]) else 0
                                    for i in range(nrows)])
        top_margins    = np.array([margins[i, :, 3].max()
                                    if np.any(margins[i, :, :]) else 0
                                    for i in range(nrows)])

        fig_left, fig_bottom, fig_width, fig_height = rect
        fig_right = fig_left + fig_width
        fig_top   = fig_bottom + fig_height

        available_width  = fig_width  - left_margins.sum() - right_margins.sum()  - w_pad * (ncols - 1)
        available_height = fig_height - bottom_margins.sum() - top_margins.sum() - h_pad * (nrows - 1)

        if available_width <= 0 or available_height <= 0:
            return

        width_ratios  = np.array(width_ratios)  if width_ratios  is not None else np.ones(ncols)
        height_ratios = np.array(height_ratios) if height_ratios is not None else np.ones(nrows)
        col_widths  = (width_ratios  / width_ratios.sum())  * available_width
        row_heights = (height_ratios / height_ratios.sum()) * available_height

        # --- Compute and apply positions ---
        positions = np.zeros((nrows, ncols, 4))

        for j in range(ncols):
            col_left = (fig_left + left_margins[0] if j == 0
                        else positions[0, j-1, 2] + right_margins[j-1] + w_pad + left_margins[j])
            col_right = col_left + col_widths[j]

            for i in range(nrows):
                row_top = (fig_top - top_margins[0] if i == 0
                           else positions[i-1, j, 1] - bottom_margins[i-1] - h_pad - top_margins[i])
                row_bottom = row_top - row_heights[i]
                positions[i, j] = [col_left, row_bottom, col_right, row_top]
                ax = axes_grid[i, j]
                if ax is not None and ax.get_visible():
                    ax.set_position([col_left, row_bottom,
                                     col_right - col_left, row_top - row_bottom])

        for ax in spanning_axes:
            if not ax.get_visible():
                continue
            ss = ax.get_subplotspec()
            rs, re = ss.rowspan.start, ss.rowspan.stop
            cs, ce = ss.colspan.start, ss.colspan.stop
            ax.set_position([
                positions[rs, cs, 0],
                positions[re - 1, cs, 1],
                positions[rs, ce - 1, 2] - positions[rs, cs, 0],
                positions[rs, cs, 3]     - positions[re - 1, cs, 1],
            ])

        self._position_colorbars(fig, axes_grid, positions, nrows, ncols, spanning_axes)

    # ------------------------------------------------------------------
    # Decoration measurement helpers
    # ------------------------------------------------------------------

    def _measure_axes_decorations(self, ax, renderer, fig):
        """Return margins (left/right/bottom/top) needed by *ax*'s decorations."""
        pos = ax.get_position(original=True)
        tightbbox = martist._get_tightbbox_for_layout_only(ax, renderer)
        if tightbbox is None:
            return {'left': 0, 'right': 0, 'bottom': 0, 'top': 0}
        bbox = fig.transSubfigure.inverted().transform_bbox(tightbbox)
        return {
            'left':   max(0, pos.x0 - bbox.x0),
            'right':  max(0, bbox.x1 - pos.x1),
            'bottom': max(0, pos.y0 - bbox.y0),
            'top':    max(0, bbox.y1 - pos.y1),
        }

    def _measure_positioned_colorbar(self, cax, parent_ax, location, renderer, fig):
        """Measure space needed for a colorbar by checking its actual tight_bbox.

        Returns space in figure-relative coordinates, or None if not yet positioned.
        """
        cax_pos = cax.get_position()
        parent_pos = parent_ax.get_position()

        # If colorbar doesn't have a reasonable position yet, return None
        # (will use default estimate in first pass)
        if cax_pos.width <= 0 or cax_pos.height <= 0:
            return None

        fig_w, fig_h = _fig_size_inches(fig)

        # Get colorbar's tight bbox (includes tick labels)
        cax_tight = martist._get_tightbbox_for_layout_only(cax, renderer)
        if cax_tight is None:
            # Fallback: use conservative estimates
            if location in ('right', 'left'):
                return 0.7 / fig_w  # bar + pad + labels + buffer
            else:
                return 0.7 / fig_h

        cax_bbox = fig.transSubfigure.inverted().transform_bbox(cax_tight)
        parent_tight = martist._get_tightbbox_for_layout_only(parent_ax, renderer)
        if parent_tight is None:
            parent_tight_bbox = parent_pos
        else:
            parent_tight_bbox = fig.transSubfigure.inverted().transform_bbox(parent_tight)

        # Calculate space: distance from parent's tight edge to colorbar's tight edge
        # plus a buffer for neighboring axes
        # Use larger buffer for vertical colorbars to prevent tick label overlap
        if location in ('right', 'left'):
            # For vertical colorbars, the tick labels extend horizontally
            buffer = 0.05 / fig_w
        else:
            # For horizontal colorbars, the tick labels extend vertically
            # Use a larger buffer to account for potential overlap between stacked colorbars
            buffer = 0.15 / fig_h  # Increased from 0.05 to prevent overlap

        if location == 'right':
            space = cax_bbox.x1 - parent_tight_bbox.x1 + buffer
        elif location == 'left':
            space = parent_tight_bbox.x0 - cax_bbox.x0 + buffer
        elif location == 'top':
            space = cax_bbox.y1 - parent_tight_bbox.y1 + buffer
        elif location == 'bottom':
            space = parent_tight_bbox.y0 - cax_bbox.y0 + buffer
        else:
            return None

        return max(0, space)

    def _measure_colorbar_space(self, ax, renderer, fig, axes_grid, nrows, ncols):
        """Margin reserved for colorbars attached to a regular-grid *ax*."""
        ax_row = ax_col = None
        for i in range(nrows):
            for j in range(ncols):
                if axes_grid[i, j] is ax:
                    ax_row, ax_col = i, j
                    break
            if ax_row is not None:
                break
        if ax_row is None:
            return None

        colorbars = [(cax, cax._colorbar_info.get('parents', []))
                     for cax in fig.axes
                     if hasattr(cax, '_colorbar_info')
                     and ax in cax._colorbar_info.get('parents', [])]
        if not colorbars:
            return None

        cb_margins = {'left': 0, 'right': 0, 'bottom': 0, 'top': 0}
        fig_w, fig_h = _fig_size_inches(fig)

        for cax, parents in colorbars:
            location = cax._colorbar_info.get('location', 'right')

            if len(parents) > 1:
                prows, pcols = [], []
                for p in parents:
                    for i in range(nrows):
                        for j in range(ncols):
                            if axes_grid[i, j] is p:
                                prows.append(i); pcols.append(j)
                if location == 'right'  and ax_col != max(pcols): continue
                if location == 'left'   and ax_col != min(pcols): continue
                if location == 'top'    and ax_row != min(prows): continue
                if location == 'bottom' and ax_row != max(prows): continue

            # Measure actual colorbar space if it's already positioned
            space = self._measure_positioned_colorbar(cax, ax, location, renderer, fig)
            if space is None:
                # Fallback for first pass: conservative estimate
                fig_w, fig_h = _fig_size_inches(fig)
                space = 0.7 / fig_w if location in ('right', 'left') else 0.7 / fig_h
            cb_margins[location] += space

        return cb_margins

    def _measure_colorbar_space_for_spanning_axis(self, ax, renderer, fig,
                                                   subplotspec, nrows, ncols):
        """Margin reserved for a colorbar attached to a spanning *ax*."""
        colorbars = [cax for cax in fig.axes
                     if hasattr(cax, '_colorbar_info')
                     and ax in cax._colorbar_info.get('parents', [])]
        if not colorbars or len(colorbars) > 1:
            return None

        cax = colorbars[0]
        location = cax._colorbar_info.get('location', 'right')

        # Measure actual colorbar space if it's already positioned
        space = self._measure_positioned_colorbar(cax, ax, location, renderer, fig)
        if space is None:
            # Fallback for first pass: conservative estimate
            fig_w, fig_h = _fig_size_inches(fig)
            space = 0.7 / fig_w if location in ('right', 'left') else 0.7 / fig_h
        return {'location': location, location: space}

    # ------------------------------------------------------------------
    # Colorbar positioning
    # ------------------------------------------------------------------

    def _position_colorbars(self, fig, axes_grid, positions, nrows, ncols,
                             spanning_axes=None):
        """Place all colorbar axes after the parent axes have been positioned."""
        if spanning_axes is None:
            spanning_axes = []

        renderer = fig._get_renderer()
        fig_w, fig_h = _fig_size_inches(fig)
        bar_in = 0.2; pad_in = 0.1
        positioned = set()
        colorbar_positions = {}  # Track positioned colorbars by location

        for cax in fig.axes:
            if not hasattr(cax, '_colorbar_info') or id(cax) in positioned:
                continue
            positioned.add(id(cax))

            parents  = cax._colorbar_info.get('parents', [])
            location = cax._colorbar_info.get('location', 'right')
            if not parents:
                continue

            # Collect parent positions
            pp = []
            for pax in parents:
                found = False
                for i in range(nrows):
                    for j in range(ncols):
                        if axes_grid[i, j] is pax:
                            pp.append(positions[i, j])
                            found = True
                            break
                    if found:
                        break
                if not found and pax in spanning_axes:
                    pos = pax.get_position()
                    pp.append([pos.x0, pos.y0, pos.x1, pos.y1])
            if not pp:
                continue

            pp = np.array(pp)
            sx0, sy0, sx1, sy1 = pp[:, 0].min(), pp[:, 1].min(), pp[:, 2].max(), pp[:, 3].max()

            # Get shrink, anchor, and aspect parameters
            shrink = cax._colorbar_info.get('shrink', 1.0)
            anchor = cax._colorbar_info.get('anchor', (0.0, 0.5))
            aspect = cax._colorbar_info.get('aspect', 20)  # aspect = long_dimension / short_dimension

            pad_fig_w = pad_in / fig_w
            pad_fig_h = pad_in / fig_h

            if location == 'right':
                # For vertical colorbar: height is long dimension, width = height / aspect
                # Start after the tight bbox right edge of all parents
                tight_right = sx1
                for pax in parents:
                    tb = martist._get_tightbbox_for_layout_only(pax, renderer)
                    if tb is not None:
                        t = fig.transSubfigure.inverted().transform_bbox(tb)
                        tight_right = max(tight_right, t.x1)
                # Apply shrink to height (long dimension) based on parent spine extent
                full_height = sy1 - sy0
                cb_height = full_height * shrink
                cy0 = sy0 + anchor[1] * (full_height - cb_height)
                cy1 = cy0 + cb_height
                # Compute width from aspect ratio: width = height / aspect
                # Convert to inches: cb_height is in fig coords, convert to inches, divide by aspect, convert back
                cb_height_inches = cb_height * fig_h
                cb_width_inches = cb_height_inches / aspect
                cb_w = cb_width_inches / fig_w
                cx0 = tight_right + pad_fig_w
                cx1 = cx0 + cb_w
            elif location == 'left':
                # For vertical colorbar: height is long dimension, width = height / aspect
                # Start before the tight bbox left edge of all parents
                tight_left = sx0
                for pax in parents:
                    tb = martist._get_tightbbox_for_layout_only(pax, renderer)
                    if tb is not None:
                        t = fig.transSubfigure.inverted().transform_bbox(tb)
                        tight_left = min(tight_left, t.x0)
                # Apply shrink to height (long dimension) based on parent spine extent
                full_height = sy1 - sy0
                cb_height = full_height * shrink
                cy0 = sy0 + anchor[1] * (full_height - cb_height)
                cy1 = cy0 + cb_height
                # Compute width from aspect ratio
                cb_height_inches = cb_height * fig_h
                cb_width_inches = cb_height_inches / aspect
                cb_w = cb_width_inches / fig_w
                cx1 = tight_left - pad_fig_w
                cx0 = cx1 - cb_w
            elif location == 'top':
                # For horizontal colorbar: width is long dimension, height = width / aspect
                # Start above the tight bbox top edge of all parents
                tight_top = sy1
                for pax in parents:
                    tb = martist._get_tightbbox_for_layout_only(pax, renderer)
                    if tb is not None:
                        t = fig.transSubfigure.inverted().transform_bbox(tb)
                        tight_top = max(tight_top, t.y1)
                # Apply shrink to width (long dimension) based on parent spine extent
                full_width = sx1 - sx0
                cb_width = full_width * shrink
                cx0 = sx0 + anchor[0] * (full_width - cb_width)
                cx1 = cx0 + cb_width
                # Compute height from aspect ratio
                cb_width_inches = cb_width * fig_w
                cb_height_inches = cb_width_inches / aspect
                cb_h = cb_height_inches / fig_h
                cy0 = tight_top + pad_fig_h
                cy1 = cy0 + cb_h
            elif location == 'bottom':
                # For horizontal colorbar: width is long dimension, height = width / aspect
                # Start below the tight bbox bottom edge of all parents
                tight_bottom = sy0
                for pax in parents:
                    tb = martist._get_tightbbox_for_layout_only(pax, renderer)
                    if tb is not None:
                        t = fig.transSubfigure.inverted().transform_bbox(tb)
                        tight_bottom = min(tight_bottom, t.y0)
                # Apply shrink to width (long dimension) based on parent spine extent
                full_width = sx1 - sx0
                cb_width = full_width * shrink
                cx0 = sx0 + anchor[0] * (full_width - cb_width)
                cx1 = cx0 + cb_width
                # Compute height from aspect ratio
                cb_width_inches = cb_width * fig_w
                cb_height_inches = cb_width_inches / aspect
                cb_h = cb_height_inches / fig_h
                cy1 = tight_bottom - pad_fig_h
                cy0 = cy1 - cb_h
            else:
                continue

            # Remove box-aspect so our explicit size is not overridden by
            # apply_aspect() later in the draw cycle.
            cax.set_box_aspect(None)
            cax.set_position([cx0, cy0, cx1 - cx0, cy1 - cy0])

    # ------------------------------------------------------------------
    # Super-label rectangle adjustment
    # ------------------------------------------------------------------

    def _adjust_rect_for_suptitles(self, fig, renderer, rect):
        """Shrink *rect* to leave room for suptitle / supxlabel / supylabel."""
        rect = list(rect)
        inv = fig.transSubfigure.inverted().transform_bbox
        fig_w, fig_h = _fig_size_inches(fig)
        gap = self._params['suptitle_pad']

        if fig._suptitle is not None and fig._suptitle.get_in_layout():
            h = inv(fig._suptitle.get_window_extent(renderer)).height
            rect[3] -= h + gap / fig_h

        if fig._supxlabel is not None and fig._supxlabel.get_in_layout():
            h = inv(fig._supxlabel.get_window_extent(renderer)).height
            need = h + gap / fig_h
            rect[1] += need
            rect[3] -= need

        if fig._supylabel is not None and fig._supylabel.get_in_layout():
            w = inv(fig._supylabel.get_window_extent(renderer)).width
            need = w + gap / fig_w
            rect[0] += need
            rect[2] -= need

        return rect
