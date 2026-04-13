"""Application entry point for the Language Review Screen Recorder."""

from __future__ import annotations

import logging
import sys
import tempfile
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMessageBox

from src.recorder.screen_recorder import ScreenRecorder
from src.settings.settings_manager import SettingsManager
from src.ui.main_window import MainWindow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

_MUTEX_NAME = "LanguageReviewApp_SingleInstance"
_LOCK_FILE = Path(tempfile.gettempdir()) / "language_review_app.lock"


class SingleInstanceLock:
    """Cross-platform single-instance enforcement.

    On Windows uses a named mutex; on macOS/Linux uses an exclusive flock.
    Call acquire() to attempt the lock; call release() on shutdown.
    """

    def __init__(self, mutex_name: str = _MUTEX_NAME, lock_file: Path = _LOCK_FILE) -> None:
        self._mutex_name = mutex_name
        self._lock_file = lock_file
        self._handle: object = None  # Windows mutex handle
        self._file: object = None    # POSIX lock file handle

    def acquire(self) -> bool:
        """Return True if lock was acquired (first instance), False otherwise."""
        if sys.platform == "win32":
            return self._acquire_windows()
        return self._acquire_posix()

    def release(self) -> None:
        """Release the lock."""
        if sys.platform == "win32":
            if self._handle is not None:
                import ctypes
                ctypes.windll.kernel32.CloseHandle(self._handle)
                self._handle = None
        else:
            if self._file is not None:
                self._file.close()
                self._file = None

    def _acquire_windows(self) -> bool:
        import ctypes
        handle = ctypes.windll.kernel32.CreateMutexW(None, True, self._mutex_name)
        if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            ctypes.windll.kernel32.CloseHandle(handle)
            return False
        self._handle = handle
        return True

    def _acquire_posix(self) -> bool:
        import fcntl
        f = self._lock_file.open("w")
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            f.close()
            return False
        self._file = f
        return True


def main() -> int:
    lock = SingleInstanceLock()
    if not lock.acquire():
        app = QApplication(sys.argv)
        QMessageBox.warning(
            None,
            "Already Running",
            "Language Review Screen Recorder is already running.",
        )
        return 1

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
    result = app.exec()
    lock.release()
    return result


if __name__ == "__main__":
    sys.exit(main())
