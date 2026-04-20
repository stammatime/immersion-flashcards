"""Transcript writer for chronological text extraction output."""

from __future__ import annotations

from pathlib import Path

from src.extractor.models import LearningLanguage, TextEntry

_LANGUAGE_LABELS = {
    LearningLanguage.JAPANESE: "Japanese",
    LearningLanguage.CHINESE_SIMPLIFIED: "Chinese (Simplified)",
    LearningLanguage.CHINESE_TRADITIONAL: "Chinese (Traditional)",
    LearningLanguage.ENGLISH: "English",
}


def _format_timestamp(seconds: float) -> str:
    """Format seconds as HH:MM:SS."""
    total = int(seconds)
    hours = total // 3600
    minutes = (total % 3600) // 60
    secs = total % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


class TranscriptWriter:
    """Writes the full chronological transcript to a file."""

    def write(self, entries: list[TextEntry], output_path: Path) -> Path:
        """Write all text entries to a transcript file.

        Format: [HH:MM:SS] [Language] text content
        """
        sorted_entries = sorted(entries, key=lambda e: e.timestamp_seconds)

        lines = []
        for entry in sorted_entries:
            timestamp = _format_timestamp(entry.timestamp_seconds)
            lang_label = _LANGUAGE_LABELS.get(entry.language, entry.language.value)
            lines.append(f"[{timestamp}] [{lang_label}] {entry.text}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines) + "\n" if lines else "", encoding="utf-8")
        return output_path
