"""Text deduplication for first-occurrence flashcard generation."""

from __future__ import annotations

from src.extractor.models import TextEntry


class TextDeduplicator:
    """Tracks seen text and emits only first occurrences."""

    def __init__(self) -> None:
        self._seen: set[str] = set()

    def process(self, entry: TextEntry) -> bool:
        """Check if this text entry is a first occurrence.

        Returns True if the entry's text has not been seen before (first
        occurrence), False if it is a duplicate. Adds new text to the
        seen set.
        """
        if entry.text in self._seen:
            return False
        self._seen.add(entry.text)
        return True

    def reset(self) -> None:
        """Clear all seen entries."""
        self._seen.clear()
