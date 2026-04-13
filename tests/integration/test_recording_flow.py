"""Integration test: full recording flow using real FFmpeg.

Requires FFmpeg to be installed and available on PATH (or bundled).
Skipped automatically if FFmpeg is not found.
"""

import shutil
import subprocess
import time

import pytest

from src.recorder.display_enumerator import DisplayEnumerator
from src.recorder.models import RecordingStatus
from src.recorder.screen_recorder import ScreenRecorder
from src.settings.models import Settings


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


@pytest.fixture
def settings(tmp_path):
    save_dir = tmp_path / "recordings"
    save_dir.mkdir()
    return Settings(save_directory=str(save_dir), app_version="0.1.0")


@pytest.mark.skipif(not ffmpeg_available(), reason="FFmpeg not on PATH — skipping integration test")
class TestFullRecordingFlow:
    def test_start_record_stop_produces_mp4(self, settings, qapp):
        enumerator = DisplayEnumerator()
        displays = enumerator.list_displays()
        assert len(displays) >= 1
        primary = next(d for d in displays if d.is_primary)

        recorder = ScreenRecorder(settings)
        recorder.start(primary)
        assert recorder.status == RecordingStatus.RECORDING

        time.sleep(2)

        result = recorder.stop()
        assert result.status == RecordingStatus.COMPLETE
        assert result.save_path.exists()
        assert result.save_path.suffix == ".mp4"
        assert result.save_path.stat().st_size > 0
        assert result.end_time is not None
        assert result.duration_seconds is not None
        assert result.duration_seconds >= 1.0

    def test_recording_file_is_valid_mp4(self, settings, qapp):
        enumerator = DisplayEnumerator()
        displays = enumerator.list_displays()
        primary = next(d for d in displays if d.is_primary)

        recorder = ScreenRecorder(settings)
        recorder.start(primary)
        time.sleep(2)
        result = recorder.stop()

        # Use ffprobe to verify the file is a valid MP4
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(result.save_path)],
            capture_output=True, text=True
        )
        assert probe.returncode == 0
        duration = float(probe.stdout.strip())
        assert duration >= 1.0
