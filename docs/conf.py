# Configuration file for the Sphinx documentation builder.

import os
import sys
sys.path.insert(0, os.path.abspath('../src'))

project = 'mpl-direct-layout'
author = 'Jody Klymak'
release = '0.1.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'numpydoc',
    'matplotlib.sphinxext.plot_directive',
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'matplotlib': ('https://matplotlib.org/stable', None),
    'numpy': ('https://numpy.org/doc/stable', None),
}

numpydoc_show_class_members = False

# Plot directive configuration
plot_include_source = True
plot_html_show_source_link = False
plot_formats = ['png']
plot_html_show_formats = False

# Suppress duplicate object warnings from plot directive imports
suppress_warnings = ['app.add_node', 'app.add_directive', 'autosummary']
autodoc_member_order = 'bysource'

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
