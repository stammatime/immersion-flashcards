"""Unit tests for DisplayEnumerator.

Tests use a real QApplication but mock QApplication.screens() to avoid
requiring physical displays to be connected.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.recorder.display_enumerator import DisplayEnumerator
from src.recorder.models import Display


def _make_mock_screen(name: str, x: int, y: int, w: int, h: int, dpr: float = 1.0):
    screen = MagicMock()
    screen.name.return_value = name
    geo = MagicMock()
    geo.x.return_value = x
    geo.y.return_value = y
    geo.width.return_value = w
    geo.height.return_value = h
    screen.geometry.return_value = geo
    screen.devicePixelRatio.return_value = dpr
    return screen


class TestDisplayEnumeratorSingleDisplay:
    def test_single_display_returns_one_element(self, qapp):
        mock_screen = _make_mock_screen("screen0", 0, 0, 1920, 1080)
        with patch.object(type(qapp), "screens", return_value=[mock_screen]), \
             patch.object(type(qapp), "primaryScreen", return_value=mock_screen):
            enumerator = DisplayEnumerator()
            displays = enumerator.list_displays()
        assert len(displays) == 1

    def test_single_display_is_primary(self, qapp):
        mock_screen = _make_mock_screen("screen0", 0, 0, 1920, 1080)
        with patch.object(type(qapp), "screens", return_value=[mock_screen]), \
             patch.object(type(qapp), "primaryScreen", return_value=mock_screen):
            enumerator = DisplayEnumerator()
            displays = enumerator.list_displays()
        assert displays[0].is_primary is True
        assert "Primary" in displays[0].label

    def test_single_display_geometry(self, qapp):
        mock_screen = _make_mock_screen("screen0", 0, 0, 2560, 1440, dpr=2.0)
        with patch.object(type(qapp), "screens", return_value=[mock_screen]), \
             patch.object(type(qapp), "primaryScreen", return_value=mock_screen):
            enumerator = DisplayEnumerator()
            d = enumerator.list_displays()[0]
        assert d.width == 2560
        assert d.height == 1440
        assert d.scale_factor == 2.0


class TestDisplayEnumeratorMultipleDisplays:
    def test_two_displays_returns_two_elements(self, qapp):
        s0 = _make_mock_screen("screen0", 0, 0, 1920, 1080)
        s1 = _make_mock_screen("screen1", 1920, 0, 2560, 1440)
        with patch.object(type(qapp), "screens", return_value=[s0, s1]), \
             patch.object(type(qapp), "primaryScreen", return_value=s0):
            enumerator = DisplayEnumerator()
            displays = enumerator.list_displays()
        assert len(displays) == 2

    def test_only_one_display_is_primary(self, qapp):
        s0 = _make_mock_screen("screen0", 0, 0, 1920, 1080)
        s1 = _make_mock_screen("screen1", 1920, 0, 2560, 1440)
        with patch.object(type(qapp), "screens", return_value=[s0, s1]), \
             patch.object(type(qapp), "primaryScreen", return_value=s0):
            enumerator = DisplayEnumerator()
            displays = enumerator.list_displays()
        primary_count = sum(1 for d in displays if d.is_primary)
        assert primary_count == 1

    def test_secondary_display_not_primary(self, qapp):
        s0 = _make_mock_screen("screen0", 0, 0, 1920, 1080)
        s1 = _make_mock_screen("screen1", 1920, 0, 2560, 1440)
        with patch.object(type(qapp), "screens", return_value=[s0, s1]), \
             patch.object(type(qapp), "primaryScreen", return_value=s0):
            enumerator = DisplayEnumerator()
            displays = enumerator.list_displays()
        secondary = next(d for d in displays if not d.is_primary)
        assert secondary.x == 1920
        assert "Primary" not in secondary.label

    def test_display_ids_are_unique(self, qapp):
        s0 = _make_mock_screen("screen0", 0, 0, 1920, 1080)
        s1 = _make_mock_screen("screen1", 1920, 0, 2560, 1440)
        with patch.object(type(qapp), "screens", return_value=[s0, s1]), \
             patch.object(type(qapp), "primaryScreen", return_value=s0):
            enumerator = DisplayEnumerator()
            displays = enumerator.list_displays()
        ids = [d.id for d in displays]
        assert len(ids) == len(set(ids))
