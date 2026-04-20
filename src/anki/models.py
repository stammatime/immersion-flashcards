"""Data models for Anki flashcard generation."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from src.extractor.models import LearningLanguage


@dataclass
class FlashcardEntry:
    """A single Anki card derived from a first-occurrence TextEntry."""

    front_text: str
    back_html: str
    screenshot_filename: str
    language: LearningLanguage
    timestamp_seconds: float
    confidence: float
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if os.sep in self.screenshot_filename or "/" in self.screenshot_filename:
            msg = "screenshot_filename must be a basename only, no path separators"
            raise ValueError(msg)


@dataclass
class DeckMetadata:
    """Metadata for the generated Anki deck."""

    deck_name: str
    deck_id: int
    model_id: int
    description: str
    card_count: int

    def __post_init__(self) -> None:
        if not self.deck_name:
            msg = "deck_name must be non-empty"
            raise ValueError(msg)
