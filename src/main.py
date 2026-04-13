"""Application entry point for the Language Review Screen Recorder."""

from __future__ import annotations

import logging
import sys

from PyQt6.QtWidgets import QApplication

from src.recorder.screen_recorder import ScreenRecorder
from src.settings.settings_manager import SettingsManager
from src.ui.main_window import MainWindow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("LanguageReviewApp")
    app.setOrganizationName("LanguageReview")

    settings_manager = SettingsManager()
    settings = settings_manager.load()

    # Ensure a valid save directory is set
    if not settings.save_directory:
        default_dir = settings_manager.default_save_directory()
        from src.settings.models import Settings
        settings = Settings(
            save_directory=str(default_dir),
            selected_display_id=settings.selected_display_id,
            app_version=settings.app_version,
        )
        settings_manager.save(settings)

    recorder = ScreenRecorder(settings)
    window = MainWindow(recorder, settings_manager)
    window.show()

    logger.info("Language Review Screen Recorder started")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
