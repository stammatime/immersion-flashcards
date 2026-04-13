"""Failing tests for Recording, RecordingStatus, and Display models.

Run before implementing src/recorder/models.py — all tests must fail first.
"""

import pytest
from datetime import datetime, timezone
from pathlib import Path

from src.recorder.models import Display, Recording, RecordingStatus


class TestRecordingStatus:
    def test_has_all_six_states(self):
        states = {s.name for s in RecordingStatus}
        assert states == {"IDLE", "RECORDING", "STOPPING", "COMPLETE", "PARTIAL", "FAILED"}

    def test_idle_is_default_comparable(self):
        assert RecordingStatus.IDLE != RecordingStatus.RECORDING


class TestDisplay:
    def test_create_display(self):
        d = Display(
            id="screen0",
            label="Display 1 — Primary",
            width=1920,
            height=1080,
            x=0,
            y=0,
            is_primary=True,
            scale_factor=1.0,
        )
        assert d.id == "screen0"
        assert d.is_primary is True
        assert d.width == 1920

    def test_secondary_display(self):
        d = Display(
            id="screen1",
            label="Display 2",
            width=2560,
            height=1440,
            x=1920,
            y=0,
            is_primary=False,
            scale_factor=1.5,
        )
        assert d.is_primary is False
        assert d.x == 1920


class TestRecording:
    def test_create_idle_recording(self):
        r = Recording(
            id="test-uuid",
            start_time=datetime.now(tz=timezone.utc),
            end_time=None,
            duration_seconds=None,
            save_path=Path("/tmp/recording_20260412_143022.mp4"),
            display_id="screen0",
            status=RecordingStatus.RECORDING,
            partial=False,
        )
        assert r.end_time is None
        assert r.duration_seconds is None
        assert r.status == RecordingStatus.RECORDING

    def test_completed_recording_has_duration(self):
        start = datetime(2026, 4, 12, 14, 30, 0, tzinfo=timezone.utc)
        end = datetime(2026, 4, 12, 14, 30, 42, tzinfo=timezone.utc)
        r = Recording(
            id="test-uuid",
            start_time=start,
            end_time=end,
            duration_seconds=(end - start).total_seconds(),
            save_path=Path("/tmp/recording.mp4"),
            display_id="screen0",
            status=RecordingStatus.COMPLETE,
            partial=False,
        )
        assert r.duration_seconds == 42.0
        assert r.status == RecordingStatus.COMPLETE

    def test_partial_recording_flag(self):
        r = Recording(
            id="test-uuid",
            start_time=datetime.now(tz=timezone.utc),
            end_time=None,
            duration_seconds=None,
            save_path=Path("/tmp/recording.mp4"),
            display_id="screen0",
            status=RecordingStatus.PARTIAL,
            partial=True,
        )
        assert r.partial is True
        assert r.status == RecordingStatus.PARTIAL
