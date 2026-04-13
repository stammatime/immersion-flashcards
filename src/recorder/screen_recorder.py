"""Screen recorder — orchestrates FFmpeg for cross-platform screen capture."""

from __future__ import annotations

import logging
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from src.recorder.exceptions import DiskSpaceError, FFmpegNotFoundError, RecorderStateError
from src.recorder.models import Display, Recording, RecordingStatus
from src.settings.models import Settings

logger = logging.getLogger(__name__)

_MIN_FREE_BYTES = 500 * 1024 * 1024  # 500 MB


class ScreenRecorder(QObject):
    """Manages a single screen capture session using FFmpeg as a subprocess.

    Signals:
        status_changed(RecordingStatus): Emitted on every state transition.
        elapsed_updated(float): Emitted every second while RECORDING.
        recording_completed(Recording): Emitted when status reaches COMPLETE.
        error_occurred(str): Emitted on FAILED or unexpected termination.
    """

    status_changed = pyqtSignal(object)       # payload: RecordingStatus
    elapsed_updated = pyqtSignal(float)        # payload: elapsed seconds
    recording_completed = pyqtSignal(object)   # payload: Recording
    error_occurred = pyqtSignal(str)           # payload: human-readable message

    def __init__(self, settings: Settings, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._settings = settings
        self._status = RecordingStatus.IDLE
        self._current_recording: Recording | None = None
        self._process: subprocess.Popen | None = None
        self._elapsed_seconds: float = 0.0

        self._elapsed_timer = QTimer(self)
        self._elapsed_timer.setInterval(1000)
        self._elapsed_timer.timeout.connect(self._on_elapsed_tick)

        self._watchdog_timer = QTimer(self)
        self._watchdog_timer.setInterval(500)
        self._watchdog_timer.timeout.connect(self._on_watchdog_tick)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def status(self) -> RecordingStatus:
        return self._status

    @property
    def current_recording(self) -> Recording | None:
        return self._current_recording

    @property
    def elapsed_seconds(self) -> float:
        return self._elapsed_seconds

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self, display: Display) -> None:
        """Begin recording the given display.

        Raises:
            RecorderStateError: if not in IDLE state.
            DiskSpaceError: if < 500 MB free in save directory.
            PermissionError: if save directory is not writable.
            FFmpegNotFoundError: if FFmpeg binary is not found.
        """
        if self._status != RecordingStatus.IDLE:
            raise RecorderStateError(
                f"Cannot start recording: current state is {self._status.name}"
            )

        save_dir = self._resolve_save_directory()
        self._check_disk_space(save_dir)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = save_dir / f"recording_{timestamp}.mp4"

        recording_id = str(uuid.uuid4())
        start_time = datetime.now(tz=timezone.utc)

        self._current_recording = Recording(
            id=recording_id,
            start_time=start_time,
            end_time=None,
            duration_seconds=None,
            save_path=output_path,
            display_id=display.id,
            status=RecordingStatus.RECORDING,
            partial=False,
        )

        args = self._build_ffmpeg_args(display, output_path)
        logger.info(
            "Starting recording",
            extra={"event": "recording_start", "recording_id": recording_id,
                   "display": display.id, "save_path": str(output_path)}
        )
        self._process = self._spawn_ffmpeg(args)
        self._elapsed_seconds = 0.0
        self._set_status(RecordingStatus.RECORDING)
        self._elapsed_timer.start()
        self._watchdog_timer.start()

    def stop(self) -> Recording:
        """Stop the active recording and return the completed Recording.

        Raises:
            RecorderStateError: if not in RECORDING state.
        """
        if self._status != RecordingStatus.RECORDING:
            raise RecorderStateError(
                f"Cannot stop recording: current state is {self._status.name}"
            )

        self._elapsed_timer.stop()
        self._watchdog_timer.stop()
        self._set_status(RecordingStatus.STOPPING)

        assert self._process is not None
        assert self._current_recording is not None

        # Send 'q' to FFmpeg stdin to trigger graceful stop
        try:
            if self._process.stdin:
                self._process.stdin.write(b"q")
                self._process.stdin.flush()
        except OSError:
            pass

        try:
            exit_code = self._process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            # Graceful stop timed out — force kill
            logger.warning(
                "FFmpeg did not exit after graceful stop; killing process",
                extra={"event": "recording_stop_force_kill",
                       "recording_id": self._current_recording.id}
            )
            self._process.kill()
            exit_code = self._process.wait()
        end_time = datetime.now(tz=timezone.utc)
        duration = (end_time - self._current_recording.start_time).total_seconds()

        if exit_code == 0:
            final_status = RecordingStatus.COMPLETE
        else:
            final_status = RecordingStatus.FAILED
            logger.error(
                "FFmpeg exited with non-zero code",
                extra={"event": "recording_failed", "exit_code": exit_code,
                       "recording_id": self._current_recording.id}
            )

        self._current_recording.end_time = end_time
        self._current_recording.duration_seconds = duration
        self._current_recording.status = final_status
        self._process = None

        self._set_status(final_status)
        self._elapsed_seconds = 0.0

        logger.info(
            "Recording stopped",
            extra={"event": "recording_stop", "recording_id": self._current_recording.id,
                   "duration_seconds": duration, "status": final_status.name}
        )

        completed = self._current_recording
        self._current_recording = None
        self._set_status(RecordingStatus.IDLE)

        if final_status == RecordingStatus.COMPLETE:
            self.recording_completed.emit(completed)

        return completed

    # ------------------------------------------------------------------
    # Internal helpers (prefixed with _ for testability via mock)
    # ------------------------------------------------------------------

    def _spawn_ffmpeg(self, args: list[str]) -> subprocess.Popen:
        """Spawn the FFmpeg subprocess. Separated for easy mocking in tests."""
        ffmpeg_bin = self._find_ffmpeg()
        cmd = [ffmpeg_bin] + args
        logger.debug("FFmpeg command: %s", " ".join(cmd))
        return subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def _find_ffmpeg(self) -> str:
        """Locate the FFmpeg binary.

        Resolution order:
        1. Alongside the executable (bundled via PyInstaller)
        2. imageio-ffmpeg bundled binary (dev convenience)
        3. System PATH
        """
        # 1. Bundled via PyInstaller
        exe_dir = Path(sys.executable).parent
        for candidate in [exe_dir / "ffmpeg", exe_dir / "ffmpeg.exe"]:
            if candidate.exists():
                return str(candidate)

        # 2. imageio-ffmpeg (installed as a dev dependency)
        try:
            import imageio_ffmpeg
            return imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            pass

        # 3. System PATH
        found = shutil.which("ffmpeg")
        if found:
            return found

        raise FFmpegNotFoundError(str(exe_dir))

    def _build_ffmpeg_args(self, display: Display, output_path: Path) -> list[str]:
        """Build platform-specific FFmpeg capture arguments."""
        if sys.platform == "win32":
            return self._build_windows_args(display, output_path)
        elif sys.platform == "darwin":
            return self._build_macos_args(display, output_path)
        else:
            raise RuntimeError(f"Unsupported platform: {sys.platform}")

    def _build_windows_args(self, display: Display, output_path: Path) -> list[str]:
        """gdigrab — captures a region of the Windows desktop by offset + size."""
        return [
            "-f", "gdigrab",
            "-framerate", "30",
            "-offset_x", str(display.x),
            "-offset_y", str(display.y),
            "-video_size", f"{display.width}x{display.height}",
            "-i", "desktop",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            "-y",
            str(output_path),
        ]

    def _build_macos_args(self, display: Display, output_path: Path) -> list[str]:
        """avfoundation — selects display by index (0 = primary, 1 = secondary, …)."""
        # avfoundation display index must be resolved separately if needed;
        # for now use "1" (primary display on macOS is index 1 in avfoundation)
        display_index = "1"
        return [
            "-f", "avfoundation",
            "-framerate", "30",
            "-i", f"{display_index}:none",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            "-y",
            str(output_path),
        ]

    def _check_disk_space(self, save_dir: Path) -> None:
        """Raise DiskSpaceError if save_dir has less than 500 MB free."""
        import shutil as _shutil
        usage = _shutil.disk_usage(save_dir)
        if usage.free < _MIN_FREE_BYTES:
            logger.warning(
                "Insufficient disk space",
                extra={"event": "disk_space_error", "available_bytes": usage.free}
            )
            raise DiskSpaceError(available_bytes=usage.free)

    def _resolve_save_directory(self) -> Path:
        """Return a valid, writable save directory from settings."""
        import os
        if self._settings.save_directory:
            p = Path(self._settings.save_directory)
            if p.exists() and os.access(p, os.W_OK):
                return p
        # Fallback: use home Videos directory
        if sys.platform == "win32":
            return Path.home() / "Videos"
        elif sys.platform == "darwin":
            return Path.home() / "Movies"
        return Path.home() / "Videos"

    def _set_status(self, new_status: RecordingStatus) -> None:
        self._status = new_status
        if self._current_recording is not None:
            self._current_recording.status = new_status
        self.status_changed.emit(new_status)

    def _on_elapsed_tick(self) -> None:
        self._elapsed_seconds += 1.0
        self.elapsed_updated.emit(self._elapsed_seconds)

    def _on_watchdog_tick(self) -> None:
        """Check if FFmpeg process has died unexpectedly while RECORDING."""
        if self._status != RecordingStatus.RECORDING:
            return
        if self._process is None:
            return
        exit_code = self._process.poll()
        if exit_code is not None:
            self._handle_unexpected_termination(exit_code)

    def _handle_unexpected_termination(self, exit_code: int) -> None:
        """Handle FFmpeg process dying unexpectedly during recording."""
        self._elapsed_timer.stop()
        self._watchdog_timer.stop()

        assert self._current_recording is not None
        end_time = datetime.now(tz=timezone.utc)
        duration = (end_time - self._current_recording.start_time).total_seconds()
        self._current_recording.end_time = end_time
        self._current_recording.duration_seconds = duration

        save_path = self._current_recording.save_path
        if save_path.exists() and save_path.stat().st_size > 0:
            final_status = RecordingStatus.PARTIAL
            self._current_recording.partial = True
            msg = "Recording stopped unexpectedly — partial file preserved."
        else:
            final_status = RecordingStatus.FAILED
            msg = "Recording failed — FFmpeg process terminated unexpectedly."

        self._current_recording.status = final_status
        self._process = None
        self._elapsed_seconds = 0.0
        self._set_status(final_status)

        logger.error(
            "Unexpected FFmpeg termination",
            extra={"event": "recording_crash", "exit_code": exit_code,
                   "recording_id": self._current_recording.id,
                   "status": final_status.name}
        )
        self._current_recording = None
        self._set_status(RecordingStatus.IDLE)
        self.error_occurred.emit(msg)

    def _handle_display_lost(self) -> None:
        """Called when a display is disconnected during recording (US3)."""
        if self._status != RecordingStatus.RECORDING:
            return
        self._elapsed_timer.stop()
        self._watchdog_timer.stop()

        if self._process and self._process.poll() is None:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except Exception:
                pass

        if self._current_recording:
            self._current_recording.partial = True
            self._current_recording.status = RecordingStatus.PARTIAL

        self._process = None
        self._elapsed_seconds = 0.0
        self._current_recording = None
        self._set_status(RecordingStatus.PARTIAL)
        self._set_status(RecordingStatus.IDLE)
        self.error_occurred.emit("Display disconnected during recording — recording stopped.")
