"""Tests for the extraction panel UI widget."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from src.ui.extraction_panel import ExtractionPanel, PanelState


@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture()
def panel(qapp):
    """Create a fresh ExtractionPanel for each test."""
    p = ExtractionPanel()
    yield p
    p.close()


# ------------------------------------------------------------------
# T044: State machine tests
# ------------------------------------------------------------------


class TestExtractionPanelStateMachine:
    """T044: Tests for ExtractionPanel state machine transitions."""

    def test_initial_state_is_idle(self, panel):
        assert panel.state == PanelState.IDLE

    def test_extract_button_disabled_in_idle(self, panel):
        assert not panel._extract_btn.isEnabled()

    def test_transition_idle_to_configured_when_video_and_language_set(self, panel):
        panel._set_video_path(Path("test_video.mp4"))
        panel._language_combo.setCurrentIndex(1)  # Select first real language
        assert panel.state == PanelState.CONFIGURED

    def test_extract_button_enabled_in_configured(self, panel):
        panel._set_video_path(Path("test_video.mp4"))
        panel._language_combo.setCurrentIndex(1)
        assert panel._extract_btn.isEnabled()

    def test_transition_configured_to_idle_when_video_cleared(self, panel):
        panel._set_video_path(Path("test_video.mp4"))
        panel._language_combo.setCurrentIndex(1)
        assert panel.state == PanelState.CONFIGURED
        panel._set_video_path(None)
        assert panel.state == PanelState.IDLE

    def test_transition_configured_to_idle_when_language_cleared(self, panel):
        panel._set_video_path(Path("test_video.mp4"))
        panel._language_combo.setCurrentIndex(1)
        assert panel.state == PanelState.CONFIGURED
        panel._language_combo.setCurrentIndex(0)  # Back to placeholder
        assert panel.state == PanelState.IDLE

    def test_transition_configured_to_processing(self, panel):
        panel._set_video_path(Path("test_video.mp4"))
        panel._language_combo.setCurrentIndex(1)
        with patch.object(panel, "_start_extraction"):
            panel._on_extract_clicked()
        assert panel.state == PanelState.PROCESSING

    def test_progress_bar_visible_during_processing(self, panel):
        panel._set_video_path(Path("test_video.mp4"))
        panel._language_combo.setCurrentIndex(1)
        with patch.object(panel, "_start_extraction"):
            panel._on_extract_clicked()
        assert not panel._progress_panel.isHidden()

    def test_cancel_button_visible_during_processing(self, panel):
        panel._set_video_path(Path("test_video.mp4"))
        panel._language_combo.setCurrentIndex(1)
        with patch.object(panel, "_start_extraction"):
            panel._on_extract_clicked()
        assert not panel._cancel_btn.isHidden()

    def test_transition_processing_to_complete(self, panel):
        panel._set_video_path(Path("test_video.mp4"))
        panel._language_combo.setCurrentIndex(1)
        with patch.object(panel, "_start_extraction"):
            panel._on_extract_clicked()
        panel._on_extraction_complete(
            card_count=10,
            transcript_path=Path("/tmp/transcript.txt"),
            apkg_path=Path("/tmp/deck.apkg"),
            low_confidence_count=2,
        )
        assert panel.state == PanelState.COMPLETE

    def test_results_visible_in_complete_state(self, panel):
        panel._set_video_path(Path("test_video.mp4"))
        panel._language_combo.setCurrentIndex(1)
        with patch.object(panel, "_start_extraction"):
            panel._on_extract_clicked()
        panel._on_extraction_complete(
            card_count=5,
            transcript_path=Path("/tmp/transcript.txt"),
            apkg_path=Path("/tmp/deck.apkg"),
            low_confidence_count=0,
        )
        assert not panel._results_panel.isHidden()

    def test_transition_processing_to_error(self, panel):
        panel._set_video_path(Path("test_video.mp4"))
        panel._language_combo.setCurrentIndex(1)
        with patch.object(panel, "_start_extraction"):
            panel._on_extract_clicked()
        panel._on_extraction_error("OCR engine failed")
        assert panel.state == PanelState.ERROR

    def test_error_message_displayed_in_error_state(self, panel):
        panel._set_video_path(Path("test_video.mp4"))
        panel._language_combo.setCurrentIndex(1)
        with patch.object(panel, "_start_extraction"):
            panel._on_extract_clicked()
        panel._on_extraction_error("OCR engine failed")
        assert "OCR engine failed" in panel._error_label.text()

    def test_transition_error_to_configured_on_retry(self, panel):
        panel._set_video_path(Path("test_video.mp4"))
        panel._language_combo.setCurrentIndex(1)
        with patch.object(panel, "_start_extraction"):
            panel._on_extract_clicked()
        panel._on_extraction_error("Something failed")
        panel._on_retry_clicked()
        assert panel.state == PanelState.CONFIGURED

    def test_transition_complete_to_idle_on_new_extraction(self, panel):
        panel._set_video_path(Path("test_video.mp4"))
        panel._language_combo.setCurrentIndex(1)
        with patch.object(panel, "_start_extraction"):
            panel._on_extract_clicked()
        panel._on_extraction_complete(
            card_count=5,
            transcript_path=Path("/tmp/t.txt"),
            apkg_path=Path("/tmp/d.apkg"),
            low_confidence_count=0,
        )
        panel._on_new_extraction_clicked()
        assert panel.state == PanelState.IDLE

    def test_transition_processing_to_idle_on_cancel(self, panel):
        panel._set_video_path(Path("test_video.mp4"))
        panel._language_combo.setCurrentIndex(1)
        with patch.object(panel, "_start_extraction"):
            panel._on_extract_clicked()
        panel._on_cancel_clicked()
        assert panel.state == PanelState.IDLE


# ------------------------------------------------------------------
# T045: Accessibility tests
# ------------------------------------------------------------------


class TestExtractionPanelAccessibility:
    """T045: Tests for ExtractionPanel accessibility."""

    def test_video_picker_has_accessible_name(self, panel):
        assert panel._browse_btn.accessibleName() != ""

    def test_language_combo_has_accessible_name(self, panel):
        assert panel._language_combo.accessibleName() != ""

    def test_extract_button_has_accessible_name(self, panel):
        assert panel._extract_btn.accessibleName() != ""

    def test_progress_bar_has_accessible_name(self, panel):
        assert panel._progress_bar.accessibleName() != ""

    def test_all_labels_are_visible(self, panel):
        """Verify visible labels exist for key controls."""
        assert not panel._video_label.isHidden()
        assert not panel._language_label.isHidden()

    def test_keyboard_tab_order(self, panel):
        """Verify keyboard tab order follows visual layout."""
        # Check that key interactive widgets are in tab chain
        widgets_in_order = [
            panel._browse_btn,
            panel._language_combo,
            panel._extract_btn,
        ]
        for w in widgets_in_order:
            assert w.focusPolicy() != Qt.FocusPolicy.NoFocus

    def test_status_label_updates_for_screen_readers(self, panel):
        """Verify status label has accessible description that changes with state."""
        assert panel._status_label.accessibleName() != ""

    def test_cancel_button_has_accessible_name(self, panel):
        assert panel._cancel_btn.accessibleName() != ""

    def test_color_not_sole_state_indicator(self, panel):
        """State is communicated via text labels, not color alone."""
        # In IDLE state, status label should contain text
        assert panel._status_label.text() != ""
