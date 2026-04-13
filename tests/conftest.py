"""Shared pytest fixtures for all test modules."""

import sys
import pytest


@pytest.fixture(scope="session")
def qapp():
    """Session-scoped QApplication instance required by all PyQt widget tests."""
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
