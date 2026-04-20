"""Tests for Anki data models."""

from __future__ import annotations

import pytest

from src.anki.models import DeckMetadata, FlashcardEntry
from src.extractor.models import LearningLanguage

# --- T012: FlashcardEntry ---


class TestFlashcardEntry:
    def test_create_flashcard_entry(self):
        entry = FlashcardEntry(
            front_text="hello",
            back_html='<img src="frame_001.png">',
            screenshot_filename="frame_001.png",
            language=LearningLanguage.ENGLISH,
            timestamp_seconds=10.5,
            confidence=0.95,
        )
        assert entry.front_text == "hello"
        assert entry.back_html == '<img src="frame_001.png">'
        assert entry.screenshot_filename == "frame_001.png"
        assert entry.language == LearningLanguage.ENGLISH
        assert entry.timestamp_seconds == 10.5
        assert entry.confidence == 0.95

    def test_default_tags_empty(self):
        entry = FlashcardEntry(
            front_text="test",
            back_html="<p>test</p>",
            screenshot_filename="frame.png",
            language=LearningLanguage.JAPANESE,
            timestamp_seconds=0.0,
            confidence=0.9,
        )
        assert entry.tags == []

    def test_custom_tags(self):
        entry = FlashcardEntry(
            front_text="test",
            back_html="<p>test</p>",
            screenshot_filename="frame.png",
            language=LearningLanguage.JAPANESE,
            timestamp_seconds=0.0,
            confidence=0.3,
            tags=["low-confidence"],
        )
        assert "low-confidence" in entry.tags

    def test_screenshot_filename_no_path_separators(self):
        with pytest.raises(ValueError, match="screenshot_filename"):
            FlashcardEntry(
                front_text="test",
                back_html="<p>test</p>",
                screenshot_filename="some/path/frame.png",
                language=LearningLanguage.JAPANESE,
                timestamp_seconds=0.0,
                confidence=0.9,
            )


# --- T012: DeckMetadata ---


class TestDeckMetadata:
    def test_create_deck_metadata(self):
        meta = DeckMetadata(
            deck_name="Test Deck",
            deck_id=12345,
            model_id=67890,
            description="A test deck",
            card_count=10,
        )
        assert meta.deck_name == "Test Deck"
        assert meta.deck_id == 12345
        assert meta.model_id == 67890
        assert meta.description == "A test deck"
        assert meta.card_count == 10

    def test_deck_name_must_be_nonempty(self):
        with pytest.raises(ValueError, match="deck_name"):
            DeckMetadata(
                deck_name="",
                deck_id=12345,
                model_id=67890,
                description="A test deck",
                card_count=0,
            )
