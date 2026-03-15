"""conftest.py – shared fixtures for mpl_direct_layout tests."""

import pytest
import matplotlib as mpl


@pytest.fixture(autouse=True)
def text_placeholders(monkeypatch):
    """Replace text rendering with placeholder boxes for reproducible images.

    This is the same fixture used by the matplotlib test suite.
    """
    try:
        from matplotlib.testing.conftest import mpl_test_settings  # noqa: F401
    except ImportError:
        pass

    # Use the 'mpl20' style for all tests so baselines are reproducible
    with mpl.rc_context({'text.usetex': False}):
        yield
