"""Integration test for the extraction pipeline end-to-end flow.

Uses mocked FFmpeg and OCR backends to validate the full chain:
FrameSampler -> OCREngine -> TextDeduplicator -> TranscriptWriter -> DeckBuilder -> AnkiExporter
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from PIL import Image

from src.extractor.models import ExtractionConfig, ExtractionStatus, LearningLanguage, OCRResult
from src.extractor.pipeline import ExtractionPipeline


@pytest.fixture()
def sample_video(tmp_path):
    """Create a fake video file."""
    video = tmp_path / "test_game.mp4"
    video.write_bytes(b"\x00" * 100)
    return video


@pytest.fixture()
def sample_frames(tmp_path):
    """Create visually distinct sample frame images that FFmpeg would produce."""
    from PIL import ImageDraw

    frames_dir = tmp_path / "output" / "frames"
    frames_dir.mkdir(parents=True)
    paths = []

    # Frame 0: white background with black left half
    img0 = Image.new("RGB", (200, 200), (255, 255, 255))
    draw0 = ImageDraw.Draw(img0)
    draw0.rectangle([0, 0, 100, 200], fill=(0, 0, 0))
    path0 = frames_dir / "frame_0000.png"
    img0.save(path0)
    paths.append(path0)

    # Frame 1: black background with yellow circle
    img1 = Image.new("RGB", (200, 200), (0, 0, 0))
    draw1 = ImageDraw.Draw(img1)
    draw1.ellipse([20, 20, 180, 180], fill=(255, 255, 0))
    path1 = frames_dir / "frame_0001.png"
    img1.save(path1)
    paths.append(path1)

    # Frame 2: blue background with red diagonal stripe
    img2 = Image.new("RGB", (200, 200), (0, 0, 255))
    draw2 = ImageDraw.Draw(img2)
    draw2.polygon([(0, 0), (200, 150), (200, 200), (0, 50)], fill=(255, 0, 0))
    path2 = frames_dir / "frame_0002.png"
    img2.save(path2)
    paths.append(path2)

    return paths


class TestExtractionFlowEndToEnd:
    """T028: End-to-end extraction pipeline integration test."""

    def test_full_pipeline_produces_transcript_and_apkg(self, tmp_path, sample_video, sample_frames):
        output_dir = tmp_path / "output"
        output_dir.mkdir(exist_ok=True)

        config = ExtractionConfig(
            video_path=sample_video,
            learning_language=LearningLanguage.JAPANESE,
            output_directory=output_dir,
        )

        # Mock FFmpeg to return our sample frames
        mock_ffmpeg_result = [
            {"path": str(sample_frames[0]), "timestamp": 0.0},
            {"path": str(sample_frames[1]), "timestamp": 5.5},
            {"path": str(sample_frames[2]), "timestamp": 12.0},
        ]

        # Mock OCR to return predictable text
        mock_ocr_results = {
            str(sample_frames[0]): [OCRResult(text="こんにちは", confidence=0.95, bounding_box=(10, 20, 100, 50))],
            str(sample_frames[1]): [OCRResult(text="世界", confidence=0.88, bounding_box=(15, 25, 90, 55))],
            str(sample_frames[2]): [OCRResult(text="こんにちは", confidence=0.92, bounding_box=(10, 20, 100, 50))],  # Duplicate
        }

        def mock_extract_text(frame_path):
            return mock_ocr_results.get(str(frame_path), [])

        with (
            patch("src.extractor.frame_sampler.FrameSampler._run_ffmpeg", return_value=mock_ffmpeg_result),
            patch("src.extractor.ocr_engine.OCREngine.__init__", return_value=None),
            patch("src.extractor.ocr_engine.OCREngine.extract_text", side_effect=mock_extract_text),
        ):
            pipeline = ExtractionPipeline(config)
            session = pipeline.run()

        # Verify session completed
        assert session.status == ExtractionStatus.COMPLETE
        assert session.end_time is not None

        # Verify frame sampling
        assert session.total_frames_sampled == 3

        # Verify text extraction
        assert len(session.all_entries) == 3  # All OCR results
        assert len(session.unique_entries) == 2  # "こんにちは" deduplicated

        # Verify transcript was written
        transcript_path = output_dir / "test_game_transcript.txt"
        assert transcript_path.exists()
        transcript_content = transcript_path.read_text(encoding="utf-8")
        assert "こんにちは" in transcript_content
        assert "世界" in transcript_content

        # Verify .apkg was created
        apkg_path = output_dir / "test_game.apkg"
        assert apkg_path.exists()
        assert apkg_path.stat().st_size > 0

        # Verify media directory has screenshots
        media_dir = output_dir / "media"
        assert media_dir.exists()
        media_files = list(media_dir.glob("*.png"))
        assert len(media_files) == 2  # One per unique entry

    def test_pipeline_with_no_text_produces_transcript_only(self, tmp_path, sample_video, sample_frames):
        output_dir = tmp_path / "output"
        output_dir.mkdir(exist_ok=True)

        config = ExtractionConfig(
            video_path=sample_video,
            learning_language=LearningLanguage.JAPANESE,
            output_directory=output_dir,
        )

        mock_ffmpeg_result = [
            {"path": str(sample_frames[0]), "timestamp": 0.0},
        ]

        with (
            patch("src.extractor.frame_sampler.FrameSampler._run_ffmpeg", return_value=mock_ffmpeg_result),
            patch("src.extractor.ocr_engine.OCREngine.__init__", return_value=None),
            patch("src.extractor.ocr_engine.OCREngine.extract_text", return_value=[]),
        ):
            pipeline = ExtractionPipeline(config)
            session = pipeline.run()

        assert session.status == ExtractionStatus.COMPLETE
        assert len(session.unique_entries) == 0

        # Transcript should still be created (empty)
        transcript_path = output_dir / "test_game_transcript.txt"
        assert transcript_path.exists()

        # No .apkg should be created
        apkg_path = output_dir / "test_game.apkg"
        assert not apkg_path.exists()

    def test_pipeline_raises_for_missing_video(self, tmp_path):
        config = ExtractionConfig(
            video_path=tmp_path / "nonexistent.mp4",
            learning_language=LearningLanguage.JAPANESE,
            output_directory=tmp_path / "output",
        )

        pipeline = ExtractionPipeline(config)
        with pytest.raises(FileNotFoundError):
            pipeline.run()
