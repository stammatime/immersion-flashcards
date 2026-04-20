"""Anki deck builder using genanki."""

from __future__ import annotations

import hashlib

import genanki

from src.anki.models import DeckMetadata, FlashcardEntry


def _stable_id(name: str) -> int:
    """Generate a deterministic integer ID from a string."""
    return int(hashlib.sha256(name.encode()).hexdigest()[:8], 16)


class DeckBuilder:
    """Builds an Anki deck from deduplicated text entries and their screenshots."""

    def __init__(self, deck_name: str, description: str = "") -> None:
        self._deck_name = deck_name
        self._description = description
        self._deck_id = _stable_id(f"deck:{deck_name}")
        self._model_id = _stable_id(f"model:{deck_name}")

        self._model = genanki.Model(
            self._model_id,
            "Immersion Flashcard",
            fields=[
                {"name": "Front"},
                {"name": "Back"},
                {"name": "Language"},
                {"name": "Timestamp"},
            ],
            templates=[
                {
                    "name": "Card 1",
                    "qfmt": "{{Front}}",
                    "afmt": '{{FrontSide}}<hr id="answer">{{Back}}',
                },
            ],
            css=".card { font-family: arial; font-size: 20px; text-align: center; }"
            " img { max-width: 100%; height: auto; }",
        )

        self._deck = genanki.Deck(self._deck_id, deck_name, description=description)
        self._cards: list[FlashcardEntry] = []

    def add_card(self, entry: FlashcardEntry) -> None:
        """Add a flashcard entry to the deck."""
        note = genanki.Note(
            model=self._model,
            fields=[
                entry.front_text,
                entry.back_html,
                entry.language.value,
                f"{entry.timestamp_seconds:.1f}",
            ],
            tags=entry.tags,
        )
        self._deck.add_note(note)
        self._cards.append(entry)

    def get_metadata(self) -> DeckMetadata:
        """Return current deck metadata."""
        return DeckMetadata(
            deck_name=self._deck_name,
            deck_id=self._deck_id,
            model_id=self._model_id,
            description=self._description,
            card_count=len(self._cards),
        )

    @property
    def deck(self) -> genanki.Deck:
        """Access the underlying genanki Deck."""
        return self._deck

    @property
    def cards(self) -> list[FlashcardEntry]:
        """Access the list of added FlashcardEntry objects."""
        return self._cards
