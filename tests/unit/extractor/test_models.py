"""Tests for extractor data models."""

from __future__ import annotations

import uuid

import pytest

from src.extractor.models import (
    ExtractionConfig,
    ExtractionSession,
    ExtractionStatus,
    LearningLanguage,
    TextEntry,
)

# --- T006: LearningLanguage enum ---


class TestLearningLanguage:
    def test_has_japanese(self):
        assert LearningLanguage.JAPANESE.value == "japanese"

    def test_has_chinese_simplified(self):
        assert LearningLanguage.CHINESE_SIMPLIFIED.value == "chinese_simplified"

    def test_has_chinese_traditional(self):
        assert LearningLanguage.CHINESE_TRADITIONAL.value == "chinese_traditional"

    def test_has_english(self):
        assert LearningLanguage.ENGLISH.value == "english"

    def test_all_members(self):
        assert len(LearningLanguage) == 4


# --- T006: ExtractionConfig ---


class TestExtractionConfig:
    def test_create_with_required_fields(self, tmp_path):
        video = tmp_path / "test.mp4"
        video.touch()
        config = ExtractionConfig(
            video_path=video,
            learning_language=LearningLanguage.JAPANESE,
            output_directory=tmp_path,
        )
        assert config.video_path == video
        assert config.learning_language == LearningLanguage.JAPANESE
        assert config.output_directory == tmp_path

    def test_defaults(self, tmp_path):
        video = tmp_path / "test.mp4"
        video.touch()
        config = ExtractionConfig(
            video_path=video,
            learning_language=LearningLanguage.ENGLISH,
            output_directory=tmp_path,
        )
        assert config.additional_languages == []
        assert config.scene_threshold == 0.3
        assert config.confidence_threshold == 0.5

    def test_custom_thresholds(self, tmp_path):
        video = tmp_path / "test.mp4"
        video.touch()
        config = ExtractionConfig(
            video_path=video,
            learning_language=LearningLanguage.JAPANESE,
            output_directory=tmp_path,
            scene_threshold=0.5,
            confidence_threshold=0.8,
        )
        assert config.scene_threshold == 0.5
        assert config.confidence_threshold == 0.8

    def test_additional_languages(self, tmp_path):
        video = tmp_path / "test.mp4"
        video.touch()
        config = ExtractionConfig(
            video_path=video,
            learning_language=LearningLanguage.JAPANESE,
            output_directory=tmp_path,
            additional_languages=[LearningLanguage.ENGLISH],
        )
        assert config.additional_languages == [LearningLanguage.ENGLISH]

    def test_validate_scene_threshold_range(self, tmp_path):
        video = tmp_path / "test.mp4"
        video.touch()
        with pytest.raises(ValueError, match="scene_threshold"):
            ExtractionConfig(
                video_path=video,
                learning_language=LearningLanguage.JAPANESE,
                output_directory=tmp_path,
                scene_threshold=1.5,
            )

    def test_validate_confidence_threshold_range(self, tmp_path):
        video = tmp_path / "test.mp4"
        video.touch()
        with pytest.raises(ValueError, match="confidence_threshold"):
            ExtractionConfig(
                video_path=video,
                learning_language=LearningLanguage.JAPANESE,
                output_directory=tmp_path,
                confidence_threshold=-0.1,
            )


# --- T008: TextEntry ---


class TestTextEntry:
    def test_create_text_entry(self):
        entry = TextEntry(
            text="hello",
            language=LearningLanguage.ENGLISH,
            timestamp_seconds=10.5,
            frame_index=3,
            confidence=0.95,
            bounding_box=(10, 20, 100, 30),
        )
        assert entry.text == "hello"
        assert entry.language == LearningLanguage.ENGLISH
        assert entry.timestamp_seconds == 10.5
        assert entry.frame_index == 3
        assert entry.confidence == 0.95
        assert entry.bounding_box == (10, 20, 100, 30)

    def test_auto_generates_uuid(self):
        entry = TextEntry(
            text="test",
            language=LearningLanguage.JAPANESE,
            timestamp_seconds=0.0,
            frame_index=0,
            confidence=0.9,
            bounding_box=(0, 0, 50, 20),
        )
        uuid.UUID(entry.id)  # Should not raise

    def test_is_low_confidence_default_false(self):
        entry = TextEntry(
            text="test",
            language=LearningLanguage.JAPANESE,
            timestamp_seconds=0.0,
            frame_index=0,
            confidence=0.9,
            bounding_box=(0, 0, 50, 20),
        )
        assert entry.is_low_confidence is False

    def test_screenshot_path_default_none(self):
        entry = TextEntry(
            text="test",
            language=LearningLanguage.JAPANESE,
            timestamp_seconds=0.0,
            frame_index=0,
            confidence=0.9,
            bounding_box=(0, 0, 50, 20),
        )
        assert entry.screenshot_path is None

    def test_confidence_must_be_valid(self):
        with pytest.raises(ValueError, match="confidence"):
            TextEntry(
                text="test",
                language=LearningLanguage.JAPANESE,
                timestamp_seconds=0.0,
                frame_index=0,
                confidence=1.5,
                bounding_box=(0, 0, 50, 20),
            )


# --- T010: ExtractionStatus + ExtractionSession ---


class TestExtractionStatus:
    def test_all_statuses(self):
        assert ExtractionStatus.PENDING.value == "pending"
        assert ExtractionStatus.SAMPLING.value == "sampling"
        assert ExtractionStatus.EXTRACTING.value == "extracting"
        assert ExtractionStatus.BUILDING.value == "building"
        assert ExtractionStatus.COMPLETE.value == "complete"
        assert ExtractionStatus.FAILED.value == "failed"

    def test_has_six_members(self):
        assert len(ExtractionStatus) == 6


class TestExtractionSession:
    def test_create_session(self, tmp_path):
        video = tmp_path / "test.mp4"
        video.touch()
        config = ExtractionConfig(
            video_path=video,
            learning_language=LearningLanguage.JAPANESE,
            output_directory=tmp_path,
        )
        session = ExtractionSession(config=config)
        assert session.config == config
        assert session.status == ExtractionStatus.PENDING
        uuid.UUID(session.id)  # Should not raise

    def test_session_defaults(self, tmp_path):
        video = tmp_path / "test.mp4"
        video.touch()
        config = ExtractionConfig(
            video_path=video,
            learning_language=LearningLanguage.JAPANESE,
            output_directory=tmp_path,
        )
        session = ExtractionSession(config=config)
        assert session.end_time is None
        assert session.total_frames_sampled == 0
        assert session.total_frames_processed == 0
        assert session.all_entries == []
        assert session.unique_entries == []
        assert session.seen_texts == set()
        assert session.error_message is None
