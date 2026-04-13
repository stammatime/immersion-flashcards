"""Failing tests for Settings dataclass.

Run before implementing src/settings/models.py — all tests must fail first.
"""

from src.settings.models import Settings


class TestSettings:
    def test_defaults_are_none(self):
        s = Settings()
        assert s.save_directory is None
        assert s.selected_display_id is None

    def test_app_version_is_string(self):
        s = Settings()
        assert isinstance(s.app_version, str)
        assert len(s.app_version) > 0

    def test_can_set_save_directory(self):
        s = Settings(save_directory="/Users/test/Videos")
        assert s.save_directory == "/Users/test/Videos"

    def test_can_set_display_id(self):
        s = Settings(selected_display_id="screen1")
        assert s.selected_display_id == "screen1"
