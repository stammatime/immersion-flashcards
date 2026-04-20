"""Tests for Anki .apkg exporter."""

from __future__ import annotations

import pytest

from src.anki.deck_builder import DeckBuilder
from src.anki.exporter import AnkiExporter
from src.anki.models import FlashcardEntry
from src.extractor.models import LearningLanguage


def _make_card(text: str, screenshot: str = "frame.png") -> FlashcardEntry:
    return FlashcardEntry(
        front_text=text,
        back_html=f'<img src="{screenshot}">',
        screenshot_filename=screenshot,
        language=LearningLanguage.JAPANESE,
        timestamp_seconds=0.0,
        confidence=0.95,
    )


class TestAnkiExporter:
    """T020: Tests for AnkiExporter.export()."""

    def test_export_creates_apkg_file(self, tmp_path):
        builder = DeckBuilder("Test Deck")
        builder.add_card(_make_card("hello", "frame_001.png"))

        media_dir = tmp_path / "media"
        media_dir.mkdir()
        (media_dir / "frame_001.png").touch()

        output_path = tmp_path / "output.apkg"
        exporter = AnkiExporter()
        result = exporter.export(builder, media_dir, output_path)

        assert result == output_path
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_export_raises_on_empty_deck(self, tmp_path):
        builder = DeckBuilder("Empty Deck")
        media_dir = tmp_path / "media"
        media_dir.mkdir()
        output_path = tmp_path / "output.apkg"

        exporter = AnkiExporter()
        with pytest.raises(ValueError, match="zero cards"):
            exporter.export(builder, media_dir, output_path)

    def test_exported_file_is_valid_zip(self, tmp_path):
        import zipfile

        builder = DeckBuilder("Test Deck")
        builder.add_card(_make_card("hello", "frame_001.png"))

        media_dir = tmp_path / "media"
        media_dir.mkdir()
        (media_dir / "frame_001.png").touch()

        output_path = tmp_path / "output.apkg"
        exporter = AnkiExporter()
        exporter.export(builder, media_dir, output_path)

        assert zipfile.is_zipfile(output_path)
