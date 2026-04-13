"""Data models for application settings."""

from __future__ import annotations

from dataclasses import dataclass, field


APP_VERSION = "0.1.0"


@dataclass
class Settings:
    """User-configurable application state persisted across sessions.

    Stored as JSON in the OS user config directory:
    - Windows: %APPDATA%\\LanguageReviewApp\\settings.json
    - macOS:   ~/Library/Application Support/LanguageReviewApp/settings.json
    """

    save_directory: str | None = field(default=None)
    """Absolute path to the folder where recordings are saved.

    None means the default (OS Videos/Movies folder) has not yet been overridden.
    """

    selected_display_id: str | None = field(default=None)
    """ID of the last-selected display for capture.

    None means use the primary display.
    """

    app_version: str = field(default=APP_VERSION)
    """Application version at the time settings were last saved.

    Used for future settings schema migration.
    """
