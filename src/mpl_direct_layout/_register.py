"""Register the 'direct' layout key with Matplotlib's Figure.set_layout_engine."""

import matplotlib.figure
from ._engine import DirectLayoutEngine

_original_set_layout_engine = matplotlib.figure.Figure.set_layout_engine
_registered = False


def _patched_set_layout_engine(self, layout=None, **kwargs):
    if layout == 'direct':
        self._layout_engine = DirectLayoutEngine(**kwargs)
        return
    return _original_set_layout_engine(self, layout, **kwargs)


def register():
    """Patch ``Figure.set_layout_engine`` to accept ``layout='direct'``.

    Calling this more than once is safe; subsequent calls are no-ops.
    """
    global _registered
    if _registered:
        return
    matplotlib.figure.Figure.set_layout_engine = _patched_set_layout_engine
    _registered = True


def unregister():
    """Restore the original ``Figure.set_layout_engine`` (mainly for testing)."""
    global _registered
    matplotlib.figure.Figure.set_layout_engine = _original_set_layout_engine
    _registered = False
