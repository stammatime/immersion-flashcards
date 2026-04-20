"""Failing tests for SettingsManager.

Run before implementing src/settings/settings_manager.py — tests must fail first.
"""

import json
import sys
from pathlib import Path

from src.settings.models import Settings
from src.settings.settings_manager import SettingsManager


class TestSettingsManagerLoad:
    def test_returns_defaults_when_file_missing(self, tmp_path):
        mgr = SettingsManager(config_dir=tmp_path)
        settings = mgr.load()
        assert isinstance(settings, Settings)
        assert settings.save_directory is None or isinstance(settings.save_directory, str)

    def test_returns_defaults_on_malformed_json(self, tmp_path):
        config_file = tmp_path / "settings.json"
        config_file.write_text("not valid json {{{")
        mgr = SettingsManager(config_dir=tmp_path)
        settings = mgr.load()
        assert isinstance(settings, Settings)

    def test_loads_saved_directory(self, tmp_path):
        save_dir = tmp_path / "my_recordings"
        save_dir.mkdir()
        config_file = tmp_path / "settings.json"
        config_file.write_text(json.dumps({"save_directory": str(save_dir), "app_version": "0.1.0"}))
        mgr = SettingsManager(config_dir=tmp_path)
        settings = mgr.load()
        assert settings.save_directory == str(save_dir)

    def test_resets_invalid_save_directory(self, tmp_path):
        config_file = tmp_path / "settings.json"
        config_file.write_text(json.dumps({"save_directory": "/nonexistent/path/xyz", "app_version": "0.1.0"}))
        mgr = SettingsManager(config_dir=tmp_path)
        settings = mgr.load()
        assert settings.save_directory is None or settings.save_directory != "/nonexistent/path/xyz"


class TestSettingsManagerSave:
    def test_save_creates_file(self, tmp_path):
        mgr = SettingsManager(config_dir=tmp_path)
        mgr.save(Settings(save_directory="/tmp", app_version="0.1.0"))
        assert (tmp_path / "settings.json").exists()

    def test_save_and_load_round_trip(self, tmp_path):
        mgr = SettingsManager(config_dir=tmp_path)
        original = Settings(save_directory=str(tmp_path), selected_display_id="screen1", app_version="0.1.0")
        mgr.save(original)
        loaded = mgr.load()
        assert loaded.save_directory == str(tmp_path)
        assert loaded.selected_display_id == "screen1"

    def test_save_is_valid_json(self, tmp_path):
        mgr = SettingsManager(config_dir=tmp_path)
        mgr.save(Settings(app_version="0.1.0"))
        content = (tmp_path / "settings.json").read_text()
        parsed = json.loads(content)
        assert isinstance(parsed, dict)


class TestDefaultSaveDirectory:
    def test_returns_path(self, tmp_path):
        mgr = SettingsManager(config_dir=tmp_path)
        result = mgr.default_save_directory()
        assert isinstance(result, Path)

    def test_platform_appropriate(self, tmp_path):
        mgr = SettingsManager(config_dir=tmp_path)
        result = mgr.default_save_directory()
        if sys.platform == "win32":
            assert "Videos" in str(result) or "video" in str(result).lower()
        elif sys.platform == "darwin":
            assert "Movies" in str(result) or "movie" in str(result).lower()
