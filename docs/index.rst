mpl-direct-layout
=================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   usage
   api

A kiwisolver-free layout engine for `Matplotlib <https://matplotlib.org>`_.
Positions axes by direct algebraic solving instead of constraint optimisation,
making it lighter and requiring no optional solver dependency.

Quick start
-----------

.. code-block:: python

   import mpl_direct_layout          # registers the 'direct' key
   import matplotlib.pyplot as plt

   fig, axs = plt.subplots(2, 2, layout='direct')
   for ax in axs.flat:
       ax.plot([1, 2, 3])
       ax.set_xlabel('x')
       ax.set_ylabel('y')
       ax.set_title('Title')
   plt.show()

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
