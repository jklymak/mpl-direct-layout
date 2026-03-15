"""
mpl_direct_layout
=================

A kiwisolver-free layout engine for Matplotlib.

Import this package to register the ``'direct'`` layout key::

    import mpl_direct_layout
    import matplotlib.pyplot as plt

    fig, axs = plt.subplots(2, 2, layout='direct')

"""

from ._engine import DirectLayoutEngine
from ._register import register

register()

__all__ = ['DirectLayoutEngine']
__version__ = '0.1.0'
