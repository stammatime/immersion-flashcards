"""Settings persistence — read/write user configuration to/from disk."""

from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

from src.settings.models import APP_VERSION, Settings

logger = logging.getLogger(__name__)

_APP_NAME = "LanguageReviewApp"


class SettingsManager(QObject):
    """Manages reading, writing, and validating application settings.

    Config file location:
    - Windows: %APPDATA%\\LanguageReviewApp\\settings.json
    - macOS:   ~/Library/Application Support/LanguageReviewApp/settings.json
    """

    settings_changed = pyqtSignal(object)  # payload: Settings

    def __init__(self, config_dir: Path | None = None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        if config_dir is not None:
            self._config_dir = Path(config_dir)
        else:
            self._config_dir = self._resolve_config_dir()
        self._config_dir.mkdir(parents=True, exist_ok=True)
        self._config_path = self._config_dir / "settings.json"
        self._settings: Settings = Settings()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def settings(self) -> Settings:
        """Current settings snapshot (read-only view)."""
        return self._settings

    @property
    def config_path(self) -> Path:
        """Full path to the settings JSON file."""
        return self._config_path

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self) -> Settings:
        """Read settings from disk.

        Returns defaults when the file is missing or malformed.
        Validates loaded values and resets invalid entries to safe defaults.
        """
        raw: dict = {}
        if self._config_path.exists():
            try:
                raw = json.loads(self._config_path.read_text(encoding="utf-8"))
                if not isinstance(raw, dict):
                    raise ValueError("Settings file root must be a JSON object")
            except Exception as exc:
                logger.warning("Could not parse settings file %s: %s — using defaults", self._config_path, exc)
                raw = {}

        save_dir = raw.get("save_directory")
        if save_dir is not None:
            p = Path(save_dir)
            if not p.exists() or not os.access(p, os.W_OK):
                logger.info("Saved directory %s is invalid or not writable — resetting to default", save_dir)
                save_dir = None

        settings = Settings(
            save_directory=save_dir,
            selected_display_id=raw.get("selected_display_id"),
            app_version=raw.get("app_version", APP_VERSION),
        )
        self._settings = settings
        return settings

    def save(self, settings: Settings) -> None:
        """Persist settings to disk atomically (write temp → rename).

        Raises:
            PermissionError: if the config directory is not writable.
        """
        payload = {
            "save_directory": settings.save_directory,
            "selected_display_id": settings.selected_display_id,
            "app_version": settings.app_version,
        }
        tmp_path = None
        try:
            fd, tmp_str = tempfile.mkstemp(dir=self._config_dir, suffix=".tmp")
            tmp_path = Path(tmp_str)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            tmp_path.replace(self._config_path)
            tmp_path = None
        finally:
            if tmp_path is not None and tmp_path.exists():
                tmp_path.unlink(missing_ok=True)

        self._settings = settings
        self.settings_changed.emit(settings)
        logger.debug("Settings saved to %s", self._config_path)

    def default_save_directory(self) -> Path:
        """Return the OS-appropriate default video save directory.

        - Windows: %USERPROFILE%\\Videos
        - macOS:   ~/Movies
        - Other:   ~/Videos (fallback)
        """
        if sys.platform == "win32":
            user_profile = os.environ.get("USERPROFILE", str(Path.home()))
            return Path(user_profile) / "Videos"
        elif sys.platform == "darwin":
            return Path.home() / "Movies"
        else:
            return Path.home() / "Videos"

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_config_dir() -> Path:
        if sys.platform == "win32":
            appdata = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
            return Path(appdata) / _APP_NAME
        elif sys.platform == "darwin":
            return Path.home() / "Library" / "Application Support" / _APP_NAME
        else:
            xdg = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
            return Path(xdg) / _APP_NAME
