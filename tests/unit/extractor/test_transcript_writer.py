"""Tests for transcript writing."""

from __future__ import annotations

from src.extractor.models import LearningLanguage, TextEntry
from src.extractor.transcript_writer import TranscriptWriter


def _make_entry(text: str, timestamp: float, language: LearningLanguage = LearningLanguage.JAPANESE) -> TextEntry:
    return TextEntry(
        text=text,
        language=language,
        timestamp_seconds=timestamp,
        frame_index=0,
        confidence=0.9,
        bounding_box=(0, 0, 50, 20),
    )


class TestTranscriptWriter:
    """T018: Tests for TranscriptWriter.write()."""

    def test_writes_transcript_file(self, tmp_path):
        entries = [
            _make_entry("hello", 5.0, LearningLanguage.ENGLISH),
            _make_entry("world", 10.0, LearningLanguage.ENGLISH),
        ]
        output_path = tmp_path / "transcript.txt"
        writer = TranscriptWriter()
        result = writer.write(entries, output_path)

        assert result == output_path
        assert output_path.exists()

    def test_format_hh_mm_ss_lang_text(self, tmp_path):
        entries = [
            _make_entry("hello", 65.0, LearningLanguage.ENGLISH),
        ]
        output_path = tmp_path / "transcript.txt"
        writer = TranscriptWriter()
        writer.write(entries, output_path)

        content = output_path.read_text(encoding="utf-8")
        assert "[00:01:05]" in content
        assert "[English]" in content
        assert "hello" in content

    def test_entries_in_chronological_order(self, tmp_path):
        entries = [
            _make_entry("first", 1.0),
            _make_entry("second", 5.0),
            _make_entry("third", 10.0),
        ]
        output_path = tmp_path / "transcript.txt"
        writer = TranscriptWriter()
        writer.write(entries, output_path)

        lines = output_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 3
        assert "first" in lines[0]
        assert "third" in lines[2]

    def test_empty_entries_produces_empty_file(self, tmp_path):
        output_path = tmp_path / "transcript.txt"
        writer = TranscriptWriter()
        writer.write([], output_path)

        content = output_path.read_text(encoding="utf-8")
        assert content.strip() == ""

    def test_japanese_language_tag(self, tmp_path):
        entries = [_make_entry("test", 0.0, LearningLanguage.JAPANESE)]
        output_path = tmp_path / "transcript.txt"
        writer = TranscriptWriter()
        writer.write(entries, output_path)

        content = output_path.read_text(encoding="utf-8")
        assert "[Japanese]" in content
