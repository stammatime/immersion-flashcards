"""Tests for frame sampling from video files."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.extractor.exceptions import ExtractionError
from src.extractor.frame_sampler import FrameSampler


class TestFrameSamplerSampleFrames:
    """T015: Tests for FrameSampler.sample_frames()."""

    def test_returns_list_of_sampled_frames(self, tmp_path):
        video = tmp_path / "test.mp4"
        video.touch()
        output_dir = tmp_path / "frames"
        output_dir.mkdir()

        # Create fake frame files that FFmpeg would produce
        for i in range(3):
            (output_dir / f"frame_{i:04d}.png").touch()

        sampler = FrameSampler()
        with patch.object(sampler, "_run_ffmpeg") as mock_ff:
            mock_ff.return_value = [
                {"path": str(output_dir / "frame_0000.png"), "timestamp": 0.0},
                {"path": str(output_dir / "frame_0001.png"), "timestamp": 5.2},
                {"path": str(output_dir / "frame_0002.png"), "timestamp": 12.8},
            ]
            frames = sampler.sample_frames(video, output_dir, scene_threshold=0.3)

        assert len(frames) == 3
        assert frames[0].index == 0
        assert frames[0].timestamp_seconds == 0.0
        assert frames[2].timestamp_seconds == 12.8

    def test_frames_ordered_by_timestamp(self, tmp_path):
        video = tmp_path / "test.mp4"
        video.touch()
        output_dir = tmp_path / "frames"
        output_dir.mkdir()

        sampler = FrameSampler()
        with patch.object(sampler, "_run_ffmpeg") as mock_ff:
            mock_ff.return_value = [
                {"path": str(tmp_path / "a.png"), "timestamp": 1.0},
                {"path": str(tmp_path / "b.png"), "timestamp": 3.0},
                {"path": str(tmp_path / "c.png"), "timestamp": 7.0},
            ]
            for name in ["a.png", "b.png", "c.png"]:
                (tmp_path / name).touch()
            frames = sampler.sample_frames(video, output_dir)

        timestamps = [f.timestamp_seconds for f in frames]
        assert timestamps == sorted(timestamps)

    def test_raises_file_not_found_for_missing_video(self, tmp_path):
        sampler = FrameSampler()
        with pytest.raises(FileNotFoundError):
            sampler.sample_frames(
                tmp_path / "nonexistent.mp4", tmp_path / "frames"
            )

    def test_raises_extraction_error_on_ffmpeg_failure(self, tmp_path):
        video = tmp_path / "test.mp4"
        video.touch()
        output_dir = tmp_path / "frames"
        output_dir.mkdir()

        sampler = FrameSampler()
        with (
            patch.object(sampler, "_run_ffmpeg", side_effect=ExtractionError("FFmpeg failed")),
            pytest.raises(ExtractionError),
        ):
            sampler.sample_frames(video, output_dir)


class TestFrameSamplerIsDuplicateFrame:
    """T015: Tests for FrameSampler.is_duplicate_frame()."""

    def test_identical_images_are_duplicates(self, tmp_path):
        from PIL import Image

        img = Image.new("RGB", (100, 100), (255, 0, 0))
        path_a = tmp_path / "a.png"
        path_b = tmp_path / "b.png"
        img.save(path_a)
        img.save(path_b)

        sampler = FrameSampler()
        assert sampler.is_duplicate_frame(path_a, path_b) is True

    def test_different_images_are_not_duplicates(self, tmp_path):
        from PIL import Image, ImageDraw

        # Create visually distinct images (not just solid colors)
        img_a = Image.new("RGB", (200, 200), (255, 255, 255))
        draw_a = ImageDraw.Draw(img_a)
        draw_a.rectangle([0, 0, 100, 200], fill=(0, 0, 0))

        img_b = Image.new("RGB", (200, 200), (0, 0, 0))
        draw_b = ImageDraw.Draw(img_b)
        draw_b.ellipse([50, 50, 150, 150], fill=(255, 255, 0))

        path_a = tmp_path / "a.png"
        path_b = tmp_path / "b.png"
        img_a.save(path_a)
        img_b.save(path_b)

        sampler = FrameSampler()
        assert sampler.is_duplicate_frame(path_a, path_b) is False

    def test_raises_file_not_found_for_missing_frame(self, tmp_path):
        sampler = FrameSampler()
        with pytest.raises(FileNotFoundError):
            sampler.is_duplicate_frame(
                tmp_path / "missing_a.png", tmp_path / "missing_b.png"
            )
