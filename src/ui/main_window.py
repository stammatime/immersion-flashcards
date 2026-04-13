"""Main application window for the Language Review Screen Recorder."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.recorder.display_enumerator import DisplayEnumerator
from src.recorder.models import Display, RecordingStatus
from src.recorder.screen_recorder import ScreenRecorder
from src.settings.models import Settings
from src.settings.settings_manager import SettingsManager

logger = logging.getLogger(__name__)

_STATUS_COLORS = {
    RecordingStatus.IDLE: "#888888",
    RecordingStatus.RECORDING: "#cc0000",
    RecordingStatus.STOPPING: "#cc6600",
    RecordingStatus.COMPLETE: "#888888",
    RecordingStatus.PARTIAL: "#888888",
    RecordingStatus.FAILED: "#888888",
}

_STATUS_LABELS = {
    RecordingStatus.IDLE: "Idle",
    RecordingStatus.RECORDING: "Recording",
    RecordingStatus.STOPPING: "Stopping…",
    RecordingStatus.COMPLETE: "Idle",
    RecordingStatus.PARTIAL: "Idle",
    RecordingStatus.FAILED: "Idle",
}


class MainWindow(QMainWindow):
    """Single-window UI for the screen recorder.

    Implements the UI state machine defined in contracts/ui-states.md.
    """

    def __init__(
        self,
        recorder: ScreenRecorder,
        settings_manager: SettingsManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._recorder = recorder
        self._settings_manager = settings_manager
        self._settings = settings_manager.settings
        self._enumerator = DisplayEnumerator()
        self._displays: list[Display] = []

        self.setWindowTitle("Language Review — Screen Recorder")
        self.setMinimumWidth(480)

        self._build_ui()
        self._connect_signals()
        self._refresh_displays()
        self._update_save_path_label()
        self._apply_idle_state()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # --- Status row ---
        status_row = QHBoxLayout()
        self._status_dot = QLabel("●")
        self._status_dot.setAccessibleName("Recording status indicator")
        self._status_label = QLabel("Idle")
        self._status_label.setAccessibleName("Recording status text")
        self._elapsed_label = QLabel("00:00")
        self._elapsed_label.setAccessibleName("Elapsed recording time")
        self._elapsed_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        status_row.addWidget(self._status_dot)
        status_row.addWidget(self._status_label)
        status_row.addStretch()
        status_row.addWidget(self._elapsed_label)
        layout.addLayout(status_row)

        # --- Display selector (hidden when only 1 display) ---
        self._display_label = QLabel("Capture display:")
        self._display_combo = QComboBox()
        self._display_combo.setAccessibleName("Display selector")
        layout.addWidget(self._display_label)
        layout.addWidget(self._display_combo)

        # --- Save location row ---
        save_row = QHBoxLayout()
        self._save_path_label = QLabel("")
        self._save_path_label.setAccessibleName("Save folder path")
        self._save_path_label.setWordWrap(False)
        self._choose_folder_btn = QPushButton("Choose Folder…")
        self._choose_folder_btn.setAccessibleName("Choose save folder")
        save_row.addWidget(self._save_path_label, stretch=1)
        save_row.addWidget(self._choose_folder_btn)
        layout.addLayout(save_row)

        self._folder_warning = QLabel("")
        self._folder_warning.setStyleSheet("color: #cc6600;")
        self._folder_warning.setAccessibleName("Save folder warning")
        self._folder_warning.setVisible(False)
        layout.addWidget(self._folder_warning)

        # --- Record button ---
        self._record_btn = QPushButton("Start Recording")
        self._record_btn.setAccessibleName("Start or stop recording")
        self._record_btn.setMinimumHeight(40)
        layout.addWidget(self._record_btn)

    # ------------------------------------------------------------------
    # Signal wiring
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        # Recorder signals
        self._recorder.status_changed.connect(self._on_status_changed)
        self._recorder.elapsed_updated.connect(self._on_elapsed_updated)
        self._recorder.recording_completed.connect(self._on_recording_completed)
        self._recorder.error_occurred.connect(self._on_error_occurred)

        # Button actions
        self._record_btn.clicked.connect(self._on_record_btn_clicked)
        self._choose_folder_btn.clicked.connect(self._on_choose_folder)

        # Display selector change
        self._display_combo.currentIndexChanged.connect(self._on_display_selected)

        # Qt screen change events
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.screenAdded.connect(self._on_screens_changed)
            app.screenRemoved.connect(self._on_screens_changed)

    # ------------------------------------------------------------------
    # Slot implementations
    # ------------------------------------------------------------------

    def _on_record_btn_clicked(self) -> None:
        if self._recorder.status == RecordingStatus.IDLE:
            self._start_recording()
        elif self._recorder.status == RecordingStatus.RECORDING:
            self._stop_recording()

    def _start_recording(self) -> None:
        """Validate prerequisites and start recording."""
        # Check save folder still exists
        save_dir = self._settings.save_directory
        if save_dir and not Path(save_dir).exists():
            QMessageBox.warning(
                self,
                "Save Folder Missing",
                f"The save folder no longer exists:\n{save_dir}\n\nPlease choose a new folder.",
            )
            self._on_choose_folder()
            return

        display = self._selected_display()
        try:
            self._recorder.start(display)
        except Exception as exc:
            QMessageBox.critical(self, "Could Not Start Recording", str(exc))

    def _stop_recording(self) -> None:
        try:
            self._recorder.stop()
        except Exception as exc:
            QMessageBox.critical(self, "Could Not Stop Recording", str(exc))

    def _on_status_changed(self, status: RecordingStatus) -> None:
        color = _STATUS_COLORS.get(status, "#888888")
        self._status_dot.setStyleSheet(f"color: {color}; font-size: 14px;")
        self._status_label.setText(_STATUS_LABELS.get(status, "Idle"))

        is_recording = status in (RecordingStatus.RECORDING, RecordingStatus.STOPPING)
        self._record_btn.setEnabled(status not in (RecordingStatus.STOPPING,))
        self._record_btn.setText(
            "Stop Recording" if status == RecordingStatus.RECORDING else "Start Recording"
        )
        self._choose_folder_btn.setEnabled(not is_recording)
        self._display_combo.setEnabled(not is_recording)

        if not is_recording:
            self._elapsed_label.setText("00:00")

    def _on_elapsed_updated(self, seconds: float) -> None:
        mins = int(seconds) // 60
        secs = int(seconds) % 60
        self._elapsed_label.setText(f"{mins:02d}:{secs:02d}")

    def _on_recording_completed(self, recording) -> None:
        logger.info(
            "Recording completed",
            extra={"event": "recording_completed", "recording_id": recording.id,
                   "save_path": str(recording.save_path),
                   "duration_seconds": recording.duration_seconds}
        )

    def _on_error_occurred(self, message: str) -> None:
        recording_id = (
            self._recorder.current_recording.id
            if self._recorder.current_recording else "unknown"
        )
        logger.error(
            "Recorder error",
            extra={"event": "recorder_error", "message": message,
                   "recording_id": recording_id}
        )
        QMessageBox.critical(self, "Recording Error", message)

    def _on_choose_folder(self) -> None:
        current = self._settings.save_directory or str(Path.home())
        chosen = QFileDialog.getExistingDirectory(
            self, "Choose Save Folder", current,
            QFileDialog.Option.ShowDirsOnly,
        )
        if not chosen:
            return  # User cancelled

        chosen_path = Path(chosen)
        if not os.access(chosen_path, os.W_OK):
            self._folder_warning.setText("This folder is not writable — choose another.")
            self._folder_warning.setVisible(True)
            return

        self._folder_warning.setVisible(False)
        updated = self._settings.__class__(
            save_directory=str(chosen_path),
            selected_display_id=self._settings.selected_display_id,
            app_version=self._settings.app_version,
        )
        self._settings_manager.save(updated)
        self._settings = updated
        self._update_save_path_label()

    def _on_display_selected(self, index: int) -> None:
        if index < 0 or index >= len(self._displays):
            return
        display = self._displays[index]
        updated = self._settings.__class__(
            save_directory=self._settings.save_directory,
            selected_display_id=display.id,
            app_version=self._settings.app_version,
        )
        self._settings_manager.save(updated)
        self._settings = updated

    def _on_screens_changed(self, _screen=None) -> None:
        self._refresh_displays()

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def _refresh_displays(self) -> None:
        self._displays = self._enumerator.list_displays()
        self._display_combo.blockSignals(True)
        self._display_combo.clear()
        for d in self._displays:
            self._display_combo.addItem(d.label)

        # Restore previously selected display
        saved_id = self._settings.selected_display_id
        if saved_id:
            for i, d in enumerate(self._displays):
                if d.id == saved_id:
                    self._display_combo.setCurrentIndex(i)
                    break

        self._display_combo.blockSignals(False)

        # Hide selector when only 1 display is connected
        show_selector = len(self._displays) > 1
        self._display_label.setVisible(show_selector)
        self._display_combo.setVisible(show_selector)

    def _update_save_path_label(self) -> None:
        path = self._settings.save_directory or str(
            self._settings_manager.default_save_directory()
        )
        # Truncate with ellipsis if too long
        max_chars = 50
        display = path if len(path) <= max_chars else "…" + path[-(max_chars - 1):]
        self._save_path_label.setText(display)
        self._save_path_label.setToolTip(path)

    def _apply_idle_state(self) -> None:
        self._on_status_changed(RecordingStatus.IDLE)

    def _selected_display(self) -> Display:
        idx = self._display_combo.currentIndex()
        if 0 <= idx < len(self._displays):
            return self._displays[idx]
        # Fallback: primary display
        for d in self._displays:
            if d.is_primary:
                return d
        return self._displays[0]
