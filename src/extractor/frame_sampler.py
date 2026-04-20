"""Frame sampling from video files using FFmpeg scene-change detection."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import imagehash
from PIL import Image

from src.extractor.exceptions import ExtractionError
from src.extractor.models import SampledFrame


def _find_ffmpeg() -> str:
    """Locate the FFmpeg binary.

    Resolution order:
    1. Alongside the executable (bundled via PyInstaller)
    2. imageio-ffmpeg bundled binary (dev convenience)
    3. System PATH
    """
    exe_dir = Path(sys.executable).parent
    for candidate in [exe_dir / "ffmpeg", exe_dir / "ffmpeg.exe"]:
        if candidate.exists():
            return str(candidate)

    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        pass

    found = shutil.which("ffmpeg")
    if found:
        return found

    msg = "FFmpeg not found. Ensure FFmpeg is installed and on PATH."
    raise ExtractionError(msg)


class FrameSampler:
    """Extracts key frames from a video using FFmpeg scene-change detection."""

    def sample_frames(
        self,
        video_path: Path,
        output_dir: Path,
        scene_threshold: float = 0.3,
    ) -> list[SampledFrame]:
        if not video_path.exists():
            msg = f"Video file not found: {video_path}"
            raise FileNotFoundError(msg)

        output_dir.mkdir(parents=True, exist_ok=True)

        raw_frames = self._run_ffmpeg(video_path, output_dir, scene_threshold)

        frames = []
        for i, frame_data in enumerate(raw_frames):
            frames.append(
                SampledFrame(
                    index=i,
                    path=Path(frame_data["path"]),
                    timestamp_seconds=frame_data["timestamp"],
                )
            )

        frames.sort(key=lambda f: f.timestamp_seconds)
        return frames

    def _run_ffmpeg(
        self,
        video_path: Path,
        output_dir: Path,
        scene_threshold: float,
    ) -> list[dict]:
        """Run FFmpeg to extract scene-change frames with timestamps."""
        output_pattern = str(output_dir / "frame_%04d.png")

        ffmpeg_bin = _find_ffmpeg()

        # First, probe for scene changes and get timestamps
        probe_cmd = [
            ffmpeg_bin,
            "-i", str(video_path),
            "-vf", f"select='gt(scene,{scene_threshold})',showinfo",
            "-vsync", "vfr",
            output_pattern,
            "-y",
            "-loglevel", "info",
        ]

        try:
            result = subprocess.run(
                probe_cmd,
                capture_output=True,
                text=True,
                timeout=600,
                check=False,
            )
        except subprocess.TimeoutExpired as e:
            msg = "FFmpeg timed out during frame extraction"
            raise ExtractionError(msg) from e

        # Parse timestamps from showinfo output
        frames = []
        frame_files = sorted(output_dir.glob("frame_*.png"))

        # Extract pts_time from stderr (showinfo filter output)
        timestamps = []
        for line in result.stderr.split("\n"):
            if "pts_time:" in line:
                try:
                    pts_part = line.split("pts_time:")[1].split()[0]
                    timestamps.append(float(pts_part))
                except (IndexError, ValueError):
                    continue

        for i, frame_file in enumerate(frame_files):
            timestamp = timestamps[i] if i < len(timestamps) else i * 1.0
            frames.append({"path": str(frame_file), "timestamp": timestamp})

        return frames

    def is_duplicate_frame(
        self,
        frame_a_path: Path,
        frame_b_path: Path,
        threshold: int = 10,
    ) -> bool:
        if not frame_a_path.exists():
            msg = f"Frame file not found: {frame_a_path}"
            raise FileNotFoundError(msg)
        if not frame_b_path.exists():
            msg = f"Frame file not found: {frame_b_path}"
            raise FileNotFoundError(msg)

        hash_a = imagehash.dhash(Image.open(frame_a_path))
        hash_b = imagehash.dhash(Image.open(frame_b_path))
        return bool((hash_a - hash_b) <= threshold)
