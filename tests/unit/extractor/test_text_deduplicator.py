"""Tests for text deduplication."""

from __future__ import annotations

from src.extractor.models import LearningLanguage, TextEntry
from src.extractor.text_deduplicator import TextDeduplicator


def _make_entry(text: str, timestamp: float = 0.0) -> TextEntry:
    return TextEntry(
        text=text,
        language=LearningLanguage.JAPANESE,
        timestamp_seconds=timestamp,
        frame_index=0,
        confidence=0.9,
        bounding_box=(0, 0, 50, 20),
    )


class TestTextDeduplicator:
    """T017: Tests for TextDeduplicator."""

    def test_first_occurrence_returns_true(self):
        dedup = TextDeduplicator()
        entry = _make_entry("hello")
        assert dedup.process(entry) is True

    def test_second_occurrence_returns_false(self):
        dedup = TextDeduplicator()
        entry1 = _make_entry("hello")
        entry2 = _make_entry("hello", timestamp=5.0)
        dedup.process(entry1)
        assert dedup.process(entry2) is False

    def test_different_texts_both_return_true(self):
        dedup = TextDeduplicator()
        assert dedup.process(_make_entry("hello")) is True
        assert dedup.process(_make_entry("world")) is True

    def test_exact_match_only(self):
        dedup = TextDeduplicator()
        assert dedup.process(_make_entry("Hello")) is True
        assert dedup.process(_make_entry("hello")) is True  # Different case = different entry

    def test_reset_clears_seen(self):
        dedup = TextDeduplicator()
        dedup.process(_make_entry("hello"))
        dedup.reset()
        assert dedup.process(_make_entry("hello")) is True
