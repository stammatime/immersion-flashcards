"""Extraction pipeline orchestrator.

Chains: FrameSampler -> OCREngine -> TextDeduplicator ->
        TranscriptWriter -> DeckBuilder -> AnkiExporter
"""

from __future__ import annotations

import logging
import shutil
from datetime import datetime

from src.anki.deck_builder import DeckBuilder
from src.anki.exporter import AnkiExporter
from src.anki.models import FlashcardEntry
from src.extractor.frame_sampler import FrameSampler
from src.extractor.models import (
    ExtractionConfig,
    ExtractionSession,
    ExtractionStatus,
    LearningLanguage,
    TextEntry,
)
from src.extractor.ocr_engine import OCREngine
from src.extractor.text_deduplicator import TextDeduplicator
from src.extractor.transcript_writer import TranscriptWriter

logger = logging.getLogger(__name__)

_LANGUAGE_LABELS = {
    LearningLanguage.JAPANESE: "Japanese",
    LearningLanguage.CHINESE_SIMPLIFIED: "Chinese (Simplified)",
    LearningLanguage.CHINESE_TRADITIONAL: "Chinese (Traditional)",
    LearningLanguage.ENGLISH: "English",
}


def _format_timestamp(seconds: float) -> str:
    total = int(seconds)
    hours = total // 3600
    minutes = (total % 3600) // 60
    secs = total % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


class ExtractionPipeline:
    """Orchestrates the full video text extraction workflow."""

    def __init__(self, config: ExtractionConfig, progress_callback=None) -> None:
        self.config = config
        self.session = ExtractionSession(config=config)
        self._progress_callback = progress_callback

    def run(self) -> ExtractionSession:
        """Execute the full extraction pipeline.

        Returns the completed ExtractionSession with results.
        """
        logger.info(
            "Starting extraction",
            extra={
                "event": "extraction_start",
                "session_id": self.session.id,
                "video": str(self.config.video_path),
                "learning_language": self.config.learning_language.value,
            },
        )
        try:
            self._validate_inputs()
            self._sample_frames()
            self._extract_text()
            self._build_output()
            self.session.status = ExtractionStatus.COMPLETE
            self.session.end_time = datetime.now()
            logger.info(
                "Extraction complete",
                extra={
                    "event": "extraction_complete",
                    "session_id": self.session.id,
                    "total_entries": len(self.session.all_entries),
                    "unique_entries": len(self.session.unique_entries),
                    "frames_sampled": self.session.total_frames_sampled,
                },
            )
        except Exception as e:
            self.session.status = ExtractionStatus.FAILED
            self.session.error_message = str(e)
            self.session.end_time = datetime.now()
            logger.error(
                "Extraction failed: %s",
                e,
                extra={
                    "event": "extraction_failed",
                    "session_id": self.session.id,
                    "error": str(e),
                },
            )
            raise
        return self.session

    def _validate_inputs(self) -> None:
        if not self.config.video_path.exists():
            msg = f"Video file not found: {self.config.video_path}"
            raise FileNotFoundError(msg)
        if not self.config.video_path.is_file():
            msg = f"Video path is not a file: {self.config.video_path}"
            raise FileNotFoundError(msg)

    def _emit_progress(self, phase: str, current: int = 0, total: int = 0) -> None:
        if self._progress_callback:
            self._progress_callback(phase, current, total)

    def _sample_frames(self) -> None:
        self.session.status = ExtractionStatus.SAMPLING
        self._emit_progress("Sampling frames...")

        frames_dir = self.config.output_directory / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)

        sampler = FrameSampler()
        self._sampled_frames = sampler.sample_frames(
            self.config.video_path,
            frames_dir,
            self.config.scene_threshold,
        )

        # Remove duplicate frames
        unique_frames = []
        for frame in self._sampled_frames:
            is_dup = False
            for existing in unique_frames:
                if sampler.is_duplicate_frame(frame.path, existing.path):
                    is_dup = True
                    break
            if not is_dup:
                unique_frames.append(frame)

        self._sampled_frames = unique_frames
        self.session.total_frames_sampled = len(self._sampled_frames)
        logger.info(
            "Sampled %d unique frames (removed %d duplicates)",
            len(unique_frames),
            len(self._sampled_frames) - len(unique_frames) if hasattr(self, '_sampled_frames') else 0,
            extra={
                "event": "sampling_complete",
                "session_id": self.session.id,
                "unique_frames": len(unique_frames),
            },
        )

    def _extract_text(self) -> None:
        self.session.status = ExtractionStatus.EXTRACTING

        # Determine which languages to process
        all_languages = [self.config.learning_language] + self.config.additional_languages
        engines = {}
        for lang in all_languages:
            engines[lang] = OCREngine(lang)

        dedup = TextDeduplicator()
        total = len(self._sampled_frames)

        self._emit_progress("Extracting text...", 0, total)
        for i, frame in enumerate(self._sampled_frames):
            self._emit_progress("Extracting text...", i + 1, total)
            logger.debug(
                "Processing frame %d/%d (%.1fs)",
                i + 1, total, frame.timestamp_seconds,
                extra={
                    "event": "frame_processing",
                    "session_id": self.session.id,
                    "frame": i + 1,
                    "total": total,
                    "timestamp": frame.timestamp_seconds,
                },
            )

            for lang, engine in engines.items():
                results = engine.extract_text(frame.path)
                for ocr_result in results:
                    is_low = ocr_result.confidence < self.config.confidence_threshold
                    entry = TextEntry(
                        text=ocr_result.text,
                        language=lang,
                        timestamp_seconds=frame.timestamp_seconds,
                        frame_index=frame.index,
                        confidence=ocr_result.confidence,
                        bounding_box=ocr_result.bounding_box,
                        is_low_confidence=is_low,
                        screenshot_path=frame.path,
                    )
                    self.session.all_entries.append(entry)

                    # Only deduplicate for the learning language (flashcard candidates)
                    if lang == self.config.learning_language and dedup.process(entry):
                        self.session.unique_entries.append(entry)

            self.session.total_frames_processed = i + 1

        low_conf_count = sum(1 for e in self.session.unique_entries if e.is_low_confidence)
        logger.info(
            "Extracted %d total entries, %d unique for flashcards (%d low-confidence)",
            len(self.session.all_entries),
            len(self.session.unique_entries),
            low_conf_count,
            extra={
                "event": "extraction_text_complete",
                "session_id": self.session.id,
                "total_entries": len(self.session.all_entries),
                "unique_entries": len(self.session.unique_entries),
                "low_confidence_count": low_conf_count,
                "frames_processed": self.session.total_frames_processed,
            },
        )

    def _build_output(self) -> None:
        self.session.status = ExtractionStatus.BUILDING
        self._emit_progress("Building output...")

        # Write transcript
        transcript_writer = TranscriptWriter()
        video_name = self.config.video_path.stem
        transcript_path = self.config.output_directory / f"{video_name}_transcript.txt"
        transcript_writer.write(self.session.all_entries, transcript_path)
        logger.info("Transcript written to %s", transcript_path)

        # Build Anki deck from unique entries
        if not self.session.unique_entries:
            logger.warning(
                "No text detected in learning language — no flashcards generated. "
                "Transcript (if any) was still written.",
                extra={
                    "event": "no_flashcards",
                    "session_id": self.session.id,
                    "total_entries": len(self.session.all_entries),
                },
            )
            return

        media_dir = self.config.output_directory / "media"
        media_dir.mkdir(parents=True, exist_ok=True)

        lang_label = _LANGUAGE_LABELS.get(
            self.config.learning_language, self.config.learning_language.value
        )
        deck_name = f"{video_name} - {lang_label}"
        builder = DeckBuilder(
            deck_name,
            description=f"Extracted from {video_name} on {datetime.now():%Y-%m-%d}",
        )

        for entry in self.session.unique_entries:
            # Copy screenshot to media dir
            screenshot_filename = f"frame_{entry.frame_index:04d}_{entry.id[:8]}.png"
            if entry.screenshot_path and entry.screenshot_path.exists():
                shutil.copy2(entry.screenshot_path, media_dir / screenshot_filename)

            timestamp_str = _format_timestamp(entry.timestamp_seconds)
            back_html = (
                f'<img src="{screenshot_filename}">'
                f"<br><small>{lang_label} · {timestamp_str} · "
                f"Confidence: {entry.confidence:.0%}</small>"
            )

            tags = [self.config.learning_language.value]
            if entry.is_low_confidence:
                tags.append("low-confidence")

            card = FlashcardEntry(
                front_text=entry.text,
                back_html=back_html,
                screenshot_filename=screenshot_filename,
                language=entry.language,
                timestamp_seconds=entry.timestamp_seconds,
                confidence=entry.confidence,
                tags=tags,
            )
            builder.add_card(card)

        # Export .apkg
        apkg_path = self.config.output_directory / f"{video_name}.apkg"
        exporter = AnkiExporter()
        exporter.export(builder, media_dir, apkg_path)
        logger.info("Anki deck exported to %s with %d cards", apkg_path, builder.get_metadata().card_count)
