"""Extraction panel widget for video text extraction workflow.

Implements the UI state machine defined in contracts/ui-extraction.md:
IDLE → CONFIGURED → PROCESSING → COMPLETE / ERROR
"""

from __future__ import annotations

import enum
import logging
import os
import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.extractor.models import ExtractionConfig, LearningLanguage
from src.extractor.pipeline import ExtractionPipeline

logger = logging.getLogger(__name__)

_VIDEO_FILTER = "Video Files (*.mp4 *.mkv *.avi *.webm);;All Files (*)"

_LANGUAGE_ITEMS = [
    ("— Select language —", None),
    ("Japanese", LearningLanguage.JAPANESE),
    ("Chinese (Simplified)", LearningLanguage.CHINESE_SIMPLIFIED),
    ("Chinese (Traditional)", LearningLanguage.CHINESE_TRADITIONAL),
    ("English", LearningLanguage.ENGLISH),
]


class PanelState(enum.Enum):
    IDLE = "idle"
    CONFIGURED = "configured"
    PROCESSING = "processing"
    COMPLETE = "complete"
    ERROR = "error"


# ------------------------------------------------------------------
# Background worker
# ------------------------------------------------------------------


class _ExtractionWorker(QObject):
    """Runs the extraction pipeline in a background thread."""

    finished = pyqtSignal(int, str, str, int)  # card_count, transcript, apkg, low_conf
    error = pyqtSignal(str)
    progress = pyqtSignal(str, int, int)  # phase, current, total

    def __init__(self, config: ExtractionConfig) -> None:
        super().__init__()
        self._config = config
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        try:
            pipeline = ExtractionPipeline(
                self._config,
                progress_callback=self._on_progress,
            )
            session = pipeline.run()

            transcript_path = ""
            apkg_path = ""
            video_name = self._config.video_path.stem
            transcript_file = self._config.output_directory / f"{video_name}_transcript.txt"
            if transcript_file.exists():
                transcript_path = str(transcript_file)
            apkg_file = self._config.output_directory / f"{video_name}.apkg"
            if apkg_file.exists():
                apkg_path = str(apkg_file)

            low_conf = sum(1 for e in session.unique_entries if e.is_low_confidence)
            self.finished.emit(
                len(session.unique_entries),
                transcript_path,
                apkg_path,
                low_conf,
            )
        except Exception as exc:
            self.error.emit(str(exc))

    def _on_progress(self, phase: str, current: int, total: int) -> None:
        if not self._cancelled:
            self.progress.emit(phase, current, total)


# ------------------------------------------------------------------
# ExtractionPanel
# ------------------------------------------------------------------


class ExtractionPanel(QWidget):
    """Panel for configuring and running video text extraction."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._video_path: Path | None = None
        self._state = PanelState.IDLE
        self._worker: _ExtractionWorker | None = None
        self._thread: QThread | None = None

        self._build_ui()
        self._connect_signals()
        self._apply_state(PanelState.IDLE)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def state(self) -> PanelState:
        return self._state

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # --- Status ---
        self._status_label = QLabel("Ready")
        self._status_label.setAccessibleName("Extraction status")
        layout.addWidget(self._status_label)

        # --- Input panel ---
        input_group = QGroupBox("Input")
        input_layout = QVBoxLayout(input_group)

        # Video file picker
        self._video_label = QLabel("Video file:")
        video_row = QHBoxLayout()
        self._video_path_label = QLabel("No file selected")
        self._video_path_label.setAccessibleName("Selected video file path")
        self._browse_btn = QPushButton("Browse…")
        self._browse_btn.setAccessibleName("Browse for video file")
        video_row.addWidget(self._video_path_label, stretch=1)
        video_row.addWidget(self._browse_btn)
        input_layout.addWidget(self._video_label)
        input_layout.addLayout(video_row)

        # Learning language dropdown
        self._language_label = QLabel("Learning language:")
        self._language_combo = QComboBox()
        self._language_combo.setAccessibleName("Learning language selector")
        for label, _lang in _LANGUAGE_ITEMS:
            self._language_combo.addItem(label)
        input_layout.addWidget(self._language_label)
        input_layout.addWidget(self._language_combo)

        # Additional languages checkboxes
        self._additional_label = QLabel("Additional languages (transcript only):")
        input_layout.addWidget(self._additional_label)
        self._additional_checks: dict[LearningLanguage, QCheckBox] = {}
        for label, lang in _LANGUAGE_ITEMS[1:]:
            cb = QCheckBox(label)
            cb.setAccessibleName(f"Include {label} in transcript")
            self._additional_checks[lang] = cb
            input_layout.addWidget(cb)

        layout.addWidget(input_group)

        # --- Extract button ---
        self._extract_btn = QPushButton("Extract")
        self._extract_btn.setAccessibleName("Start extraction")
        self._extract_btn.setMinimumHeight(40)
        self._extract_btn.setEnabled(False)
        layout.addWidget(self._extract_btn)

        # --- Progress panel ---
        self._progress_panel = QWidget()
        progress_layout = QVBoxLayout(self._progress_panel)
        progress_layout.setContentsMargins(0, 0, 0, 0)

        self._progress_bar = QProgressBar()
        self._progress_bar.setAccessibleName("Extraction progress")
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        progress_layout.addWidget(self._progress_bar)

        self._progress_label = QLabel("")
        self._progress_label.setAccessibleName("Current extraction phase")
        progress_layout.addWidget(self._progress_label)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setAccessibleName("Cancel extraction")
        progress_layout.addWidget(self._cancel_btn)

        self._progress_panel.setVisible(False)
        layout.addWidget(self._progress_panel)

        # --- Results panel ---
        self._results_panel = QWidget()
        results_layout = QVBoxLayout(self._results_panel)
        results_layout.setContentsMargins(0, 0, 0, 0)

        self._card_count_label = QLabel("")
        self._card_count_label.setAccessibleName("Flashcard count")
        results_layout.addWidget(self._card_count_label)

        self._transcript_link = QLabel("")
        self._transcript_link.setAccessibleName("Transcript file path")
        self._transcript_link.setOpenExternalLinks(False)
        results_layout.addWidget(self._transcript_link)

        self._apkg_link = QLabel("")
        self._apkg_link.setAccessibleName("Anki deck file path")
        self._apkg_link.setOpenExternalLinks(False)
        results_layout.addWidget(self._apkg_link)

        self._low_confidence_label = QLabel("")
        self._low_confidence_label.setAccessibleName("Low confidence entry count")
        results_layout.addWidget(self._low_confidence_label)

        results_btn_row = QHBoxLayout()
        self._open_anki_btn = QPushButton("Open in Anki")
        self._open_anki_btn.setAccessibleName("Open deck in Anki")
        self._new_extraction_btn = QPushButton("New Extraction")
        self._new_extraction_btn.setAccessibleName("Start new extraction")
        results_btn_row.addWidget(self._open_anki_btn)
        results_btn_row.addWidget(self._new_extraction_btn)
        results_layout.addLayout(results_btn_row)

        self._results_panel.setVisible(False)
        layout.addWidget(self._results_panel)

        # --- Error panel ---
        self._error_panel = QWidget()
        error_layout = QVBoxLayout(self._error_panel)
        error_layout.setContentsMargins(0, 0, 0, 0)

        self._error_label = QLabel("")
        self._error_label.setAccessibleName("Error message")
        self._error_label.setStyleSheet("color: #cc0000;")
        self._error_label.setWordWrap(True)
        error_layout.addWidget(self._error_label)

        self._retry_btn = QPushButton("Retry")
        self._retry_btn.setAccessibleName("Retry extraction")
        error_layout.addWidget(self._retry_btn)

        self._error_panel.setVisible(False)
        layout.addWidget(self._error_panel)

        layout.addStretch()

    # ------------------------------------------------------------------
    # Signal wiring
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        self._browse_btn.clicked.connect(self._on_browse_clicked)
        self._language_combo.currentIndexChanged.connect(self._on_config_changed)
        self._extract_btn.clicked.connect(self._on_extract_clicked)
        self._cancel_btn.clicked.connect(self._on_cancel_clicked)
        self._new_extraction_btn.clicked.connect(self._on_new_extraction_clicked)
        self._retry_btn.clicked.connect(self._on_retry_clicked)
        self._open_anki_btn.clicked.connect(self._on_open_anki_clicked)
        self._transcript_link.linkActivated.connect(self._on_link_clicked)
        self._apkg_link.linkActivated.connect(self._on_link_clicked)

    # ------------------------------------------------------------------
    # State machine
    # ------------------------------------------------------------------

    def _apply_state(self, new_state: PanelState) -> None:
        self._state = new_state

        is_idle = new_state == PanelState.IDLE
        is_configured = new_state == PanelState.CONFIGURED
        is_processing = new_state == PanelState.PROCESSING
        is_complete = new_state == PanelState.COMPLETE
        is_error = new_state == PanelState.ERROR

        # Input controls
        input_enabled = is_idle or is_configured
        self._browse_btn.setEnabled(input_enabled)
        self._language_combo.setEnabled(input_enabled)
        for cb in self._additional_checks.values():
            cb.setEnabled(input_enabled)

        # Extract button
        self._extract_btn.setEnabled(is_configured)
        self._extract_btn.setVisible(not is_processing)

        # Progress panel
        self._progress_panel.setVisible(is_processing)

        # Results panel
        self._results_panel.setVisible(is_complete)

        # Error panel
        self._error_panel.setVisible(is_error)

        # Status label
        status_map = {
            PanelState.IDLE: "Ready",
            PanelState.CONFIGURED: "Ready to extract",
            PanelState.PROCESSING: "Extracting…",
            PanelState.COMPLETE: "Extraction complete",
            PanelState.ERROR: "Extraction failed",
        }
        self._status_label.setText(status_map.get(new_state, ""))

    def _check_configured(self) -> None:
        """Transition to CONFIGURED if both video and language are set, else IDLE."""
        if self._state in (PanelState.PROCESSING, PanelState.COMPLETE, PanelState.ERROR):
            return
        has_video = self._video_path is not None
        has_language = self._language_combo.currentIndex() > 0
        if has_video and has_language:
            self._apply_state(PanelState.CONFIGURED)
        else:
            self._apply_state(PanelState.IDLE)

    # ------------------------------------------------------------------
    # Slot implementations
    # ------------------------------------------------------------------

    def _set_video_path(self, path: Path | None) -> None:
        self._video_path = path
        if path:
            display = path.name
            if len(str(path)) > 60:
                display = "…" + str(path)[-(59):]
            self._video_path_label.setText(display)
            self._video_path_label.setToolTip(str(path))
        else:
            self._video_path_label.setText("No file selected")
            self._video_path_label.setToolTip("")
        self._check_configured()

    def _on_browse_clicked(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "", _VIDEO_FILTER
        )
        if path:
            self._set_video_path(Path(path))

    def _on_config_changed(self) -> None:
        self._check_configured()
        # Update additional language checkboxes to hide the selected learning language
        selected_idx = self._language_combo.currentIndex()
        if selected_idx > 0:
            selected_lang = _LANGUAGE_ITEMS[selected_idx][1]
            for lang, cb in self._additional_checks.items():
                cb.setVisible(lang != selected_lang)
                if lang == selected_lang:
                    cb.setChecked(False)

    def _on_extract_clicked(self) -> None:
        self._apply_state(PanelState.PROCESSING)
        self._progress_bar.setValue(0)
        self._progress_label.setText("Starting…")
        self._start_extraction()

    def _start_extraction(self) -> None:
        """Launch the extraction pipeline in a background thread."""
        selected_idx = self._language_combo.currentIndex()
        learning_lang = _LANGUAGE_ITEMS[selected_idx][1]

        additional = []
        for lang, cb in self._additional_checks.items():
            if cb.isChecked() and lang != learning_lang:
                additional.append(lang)

        output_dir = self._video_path.parent / f"{self._video_path.stem}_extraction"
        output_dir.mkdir(parents=True, exist_ok=True)

        config = ExtractionConfig(
            video_path=self._video_path,
            learning_language=learning_lang,
            output_directory=output_dir,
            additional_languages=additional,
        )

        self._thread = QThread()
        self._worker = _ExtractionWorker(config)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.error.connect(self._on_worker_error)
        self._worker.progress.connect(self._on_worker_progress)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)

        self._thread.start()

    def _on_worker_progress(self, phase: str, current: int, total: int) -> None:
        self._progress_label.setText(phase)
        if total > 0:
            pct = int((current / total) * 100)
            self._progress_bar.setValue(pct)

    def _on_worker_finished(
        self, card_count: int, transcript_path: str, apkg_path: str, low_confidence_count: int
    ) -> None:
        self._on_extraction_complete(
            card_count=card_count,
            transcript_path=Path(transcript_path) if transcript_path else None,
            apkg_path=Path(apkg_path) if apkg_path else None,
            low_confidence_count=low_confidence_count,
        )

    def _on_worker_error(self, message: str) -> None:
        self._on_extraction_error(message)

    def _on_extraction_complete(
        self,
        card_count: int,
        transcript_path: Path | None,
        apkg_path: Path | None,
        low_confidence_count: int,
    ) -> None:
        self._apply_state(PanelState.COMPLETE)
        self._card_count_label.setText(f"Flashcards generated: {card_count}")

        if transcript_path:
            self._transcript_path = transcript_path
            self._transcript_link.setText(
                f'Transcript: <a href="{transcript_path}">{transcript_path.name}</a>'
            )
        else:
            self._transcript_link.setText("Transcript: (none)")

        if apkg_path:
            self._apkg_path = apkg_path
            self._apkg_link.setText(
                f'Anki deck: <a href="{apkg_path}">{apkg_path.name}</a>'
            )
        else:
            self._apkg_path = None
            self._apkg_link.setText("Anki deck: (none)")

        if low_confidence_count > 0:
            self._low_confidence_label.setText(
                f"Low-confidence entries: {low_confidence_count}"
            )
        else:
            self._low_confidence_label.setText("")

    def _on_extraction_error(self, message: str) -> None:
        self._apply_state(PanelState.ERROR)
        self._error_label.setText(f"Error: {message}")

    def _on_cancel_clicked(self) -> None:
        if self._worker:
            self._worker.cancel()
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(5000)
        self._apply_state(PanelState.IDLE)

    def _on_new_extraction_clicked(self) -> None:
        self._set_video_path(None)
        self._language_combo.setCurrentIndex(0)
        self._apply_state(PanelState.IDLE)

    def _on_retry_clicked(self) -> None:
        self._apply_state(PanelState.CONFIGURED)

    def _on_open_anki_clicked(self) -> None:
        if hasattr(self, "_apkg_path") and self._apkg_path and self._apkg_path.exists():
            if sys.platform == "win32":
                os.startfile(str(self._apkg_path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(self._apkg_path)])
            else:
                subprocess.Popen(["xdg-open", str(self._apkg_path)])

    def _on_link_clicked(self, link: str) -> None:
        path = Path(link)
        if path.exists():
            if sys.platform == "win32":
                os.startfile(str(path.parent))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path.parent)])
            else:
                subprocess.Popen(["xdg-open", str(path.parent)])
