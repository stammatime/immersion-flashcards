"""Data models for the screen recorder."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


class RecordingStatus(enum.Enum):
    """State machine for a recording session.

    Transitions::

        IDLE → RECORDING → STOPPING → COMPLETE
                       └──────────────► PARTIAL  (unexpected termination, file preserved)
                                    ──► FAILED   (FFmpeg exited non-zero, file may be corrupt)
    """

    IDLE = "idle"
    RECORDING = "recording"
    STOPPING = "stopping"
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass
class Display:
    """A connected monitor available for capture.

    Derived at runtime from Qt's QScreen list; never persisted directly.
    """

    id: str
    """Platform-specific display identifier (Qt screen name)."""

    label: str
    """Human-readable name, e.g. 'Display 1 — Primary'."""

    width: int
    """Display width in physical pixels."""

    height: int
    """Display height in physical pixels."""

    x: int
    """Left offset in the virtual desktop coordinate space."""

    y: int
    """Top offset in the virtual desktop coordinate space."""

    is_primary: bool
    """True if this is the OS-designated primary display."""

    scale_factor: float
    """DPI scale factor (1.0 = 96 DPI; 2.0 = HiDPI/Retina)."""


@dataclass
class Recording:
    """A single screen capture session from start to stop."""

    id: str
    """UUID v4 identifier generated at session start."""

    start_time: datetime
    """When recording began (local time with timezone)."""

    end_time: datetime | None
    """When recording ended; None while in progress."""

    duration_seconds: float | None
    """Elapsed time; derived as end_time - start_time; None if still in progress."""

    save_path: Path
    """Full filesystem path of the output MP4 file."""

    display_id: str
    """Identifier of the captured display (matches Display.id)."""

    status: RecordingStatus
    """Current state of this recording session."""

    partial: bool = field(default=False)
    """True if recording ended unexpectedly (crash, disk full) but file was preserved."""
