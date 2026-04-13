"""Failing unit tests for ScreenRecorder with mocked FFmpeg subprocess.

Run before implementing src/recorder/screen_recorder.py — all tests must fail first.
"""

import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from src.recorder.exceptions import DiskSpaceError, FFmpegNotFoundError, RecorderStateError
from src.recorder.models import Display, RecordingStatus
from src.settings.models import Settings


@pytest.fixture
def primary_display():
    return Display(
        id="screen0",
        label="Display 1 — Primary",
        width=1920,
        height=1080,
        x=0,
        y=0,
        is_primary=True,
        scale_factor=1.0,
    )


@pytest.fixture
def settings(tmp_path):
    save_dir = tmp_path / "recordings"
    save_dir.mkdir()
    return Settings(save_directory=str(save_dir), app_version="0.1.0")


@pytest.fixture
def recorder(settings, qapp):
    from src.recorder.screen_recorder import ScreenRecorder
    return ScreenRecorder(settings)


class TestScreenRecorderInitialState:
    def test_initial_status_is_idle(self, recorder):
        assert recorder.status == RecordingStatus.IDLE

    def test_no_current_recording_initially(self, recorder):
        assert recorder.current_recording is None

    def test_elapsed_seconds_is_zero_initially(self, recorder):
        assert recorder.elapsed_seconds == 0.0


class TestScreenRecorderStart:
    def test_transitions_to_recording_on_start(self, recorder, primary_display):
        with patch("src.recorder.screen_recorder.ScreenRecorder._spawn_ffmpeg") as mock_spawn:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            mock_spawn.return_value = mock_proc
            recorder.start(primary_display)
            assert recorder.status == RecordingStatus.RECORDING

    def test_start_sets_current_recording(self, recorder, primary_display):
        with patch("src.recorder.screen_recorder.ScreenRecorder._spawn_ffmpeg") as mock_spawn:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            mock_spawn.return_value = mock_proc
            recorder.start(primary_display)
            assert recorder.current_recording is not None
            assert recorder.current_recording.start_time is not None

    def test_start_raises_if_already_recording(self, recorder, primary_display):
        with patch("src.recorder.screen_recorder.ScreenRecorder._spawn_ffmpeg") as mock_spawn:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            mock_spawn.return_value = mock_proc
            recorder.start(primary_display)
            with pytest.raises(RecorderStateError):
                recorder.start(primary_display)

    def test_start_raises_disk_space_error(self, recorder, primary_display):
        with patch("src.recorder.screen_recorder.ScreenRecorder._check_disk_space",
                   side_effect=DiskSpaceError(100 * 1024 * 1024)):
            with pytest.raises(DiskSpaceError):
                recorder.start(primary_display)

    def test_ffmpeg_args_contain_display_geometry_on_windows(self, recorder, primary_display):
        if sys.platform != "win32":
            pytest.skip("Windows-only FFmpeg argument test")
        with patch("src.recorder.screen_recorder.ScreenRecorder._spawn_ffmpeg") as mock_spawn:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            mock_spawn.return_value = mock_proc
            recorder.start(primary_display)
            call_args = mock_spawn.call_args[0][0]  # list of args
            joined = " ".join(call_args)
            assert "gdigrab" in joined

    def test_ffmpeg_args_contain_avfoundation_on_macos(self, recorder, primary_display):
        if sys.platform != "darwin":
            pytest.skip("macOS-only FFmpeg argument test")
        with patch("src.recorder.screen_recorder.ScreenRecorder._spawn_ffmpeg") as mock_spawn:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            mock_spawn.return_value = mock_proc
            recorder.start(primary_display)
            call_args = mock_spawn.call_args[0][0]
            joined = " ".join(call_args)
            assert "avfoundation" in joined


class TestScreenRecorderStop:
    def test_transitions_to_complete_on_clean_stop(self, recorder, primary_display, tmp_path):
        with patch("src.recorder.screen_recorder.ScreenRecorder._spawn_ffmpeg") as mock_spawn:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            mock_proc.wait.return_value = 0
            mock_spawn.return_value = mock_proc

            recorder.start(primary_display)
            # Simulate output file being created
            save_path = recorder.current_recording.save_path
            save_path.touch()

            result = recorder.stop()
            assert result.status == RecordingStatus.COMPLETE

    def test_stop_sets_end_time(self, recorder, primary_display):
        with patch("src.recorder.screen_recorder.ScreenRecorder._spawn_ffmpeg") as mock_spawn:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            mock_proc.wait.return_value = 0
            mock_spawn.return_value = mock_proc

            recorder.start(primary_display)
            save_path = recorder.current_recording.save_path
            save_path.touch()
            result = recorder.stop()
            assert result.end_time is not None

    def test_stop_raises_if_not_recording(self, recorder):
        with pytest.raises(RecorderStateError):
            recorder.stop()

    def test_failed_state_on_nonzero_ffmpeg_exit(self, recorder, primary_display):
        with patch("src.recorder.screen_recorder.ScreenRecorder._spawn_ffmpeg") as mock_spawn:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            mock_proc.wait.return_value = 1
            mock_spawn.return_value = mock_proc

            recorder.start(primary_display)
            result = recorder.stop()
            assert result.status == RecordingStatus.FAILED

    def test_stop_force_kills_ffmpeg_on_timeout(self, recorder, primary_display):
        """If FFmpeg doesn't exit within the grace period, it must be killed."""
        import subprocess
        with patch("src.recorder.screen_recorder.ScreenRecorder._spawn_ffmpeg") as mock_spawn:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            # First wait() call times out; kill() is then called; second wait() returns 0
            mock_proc.wait.side_effect = [subprocess.TimeoutExpired(cmd=[], timeout=10), 0]
            mock_spawn.return_value = mock_proc

            recorder.start(primary_display)
            result = recorder.stop()

            mock_proc.kill.assert_called_once()
            assert result.status == RecordingStatus.COMPLETE

    def test_recorder_returns_to_idle_after_stop(self, recorder, primary_display):
        """Recorder must be IDLE after a completed stop so a second recording can start."""
        with patch("src.recorder.screen_recorder.ScreenRecorder._spawn_ffmpeg") as mock_spawn:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            mock_proc.wait.return_value = 0
            mock_spawn.return_value = mock_proc

            recorder.start(primary_display)
            recorder.stop()

            assert recorder.status == RecordingStatus.IDLE

    def test_can_start_second_recording_after_stop(self, recorder, primary_display):
        """A second start() call must succeed after the first recording is stopped."""
        with patch("src.recorder.screen_recorder.ScreenRecorder._spawn_ffmpeg") as mock_spawn:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            mock_proc.wait.return_value = 0
            mock_spawn.return_value = mock_proc

            recorder.start(primary_display)
            recorder.stop()

            # Should not raise
            recorder.start(primary_display)
            assert recorder.status == RecordingStatus.RECORDING
