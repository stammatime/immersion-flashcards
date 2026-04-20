"""Tests for Anki deck builder."""

from __future__ import annotations

from src.anki.deck_builder import DeckBuilder
from src.anki.models import FlashcardEntry
from src.extractor.models import LearningLanguage


def _make_card(text: str, timestamp: float = 0.0) -> FlashcardEntry:
    return FlashcardEntry(
        front_text=text,
        back_html=f'<img src="frame.png"><br><small>{text}</small>',
        screenshot_filename="frame.png",
        language=LearningLanguage.JAPANESE,
        timestamp_seconds=timestamp,
        confidence=0.95,
    )


class TestDeckBuilder:
    """T019: Tests for DeckBuilder."""

    def test_create_deck_builder(self):
        builder = DeckBuilder("Test Deck")
        assert builder is not None

    def test_add_card(self):
        builder = DeckBuilder("Test Deck")
        builder.add_card(_make_card("hello"))
        meta = builder.get_metadata()
        assert meta.card_count == 1

    def test_add_multiple_cards(self):
        builder = DeckBuilder("Test Deck")
        builder.add_card(_make_card("hello"))
        builder.add_card(_make_card("world", 5.0))
        meta = builder.get_metadata()
        assert meta.card_count == 2

    def test_metadata_has_deck_name(self):
        builder = DeckBuilder("My Language Deck")
        meta = builder.get_metadata()
        assert meta.deck_name == "My Language Deck"

    def test_metadata_has_deterministic_ids(self):
        builder1 = DeckBuilder("Same Name")
        builder2 = DeckBuilder("Same Name")
        assert builder1.get_metadata().deck_id == builder2.get_metadata().deck_id

    def test_metadata_with_description(self):
        builder = DeckBuilder("Test Deck", description="A test description")
        meta = builder.get_metadata()
        assert meta.description == "A test description"
