"""Data models for the video text extraction pipeline."""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


class LearningLanguage(enum.Enum):
    """Supported languages for text extraction and flashcard generation."""

    JAPANESE = "japanese"
    CHINESE_SIMPLIFIED = "chinese_simplified"
    CHINESE_TRADITIONAL = "chinese_traditional"
    ENGLISH = "english"


class ExtractionStatus(enum.Enum):
    """State machine for an extraction session.

    Transitions::

        PENDING → SAMPLING → EXTRACTING → BUILDING → COMPLETE
                     ↓            ↓           ↓
                   FAILED       FAILED      FAILED
    """

    PENDING = "pending"
    SAMPLING = "sampling"
    EXTRACTING = "extracting"
    BUILDING = "building"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class ExtractionConfig:
    """User-specified configuration for an extraction session."""

    video_path: Path
    learning_language: LearningLanguage
    output_directory: Path
    additional_languages: list[LearningLanguage] = field(default_factory=list)
    scene_threshold: float = 0.3
    confidence_threshold: float = 0.5

    def __post_init__(self) -> None:
        if not 0.0 <= self.scene_threshold <= 1.0:
            msg = "scene_threshold must be between 0.0 and 1.0"
            raise ValueError(msg)
        if not 0.0 <= self.confidence_threshold <= 1.0:
            msg = "confidence_threshold must be between 0.0 and 1.0"
            raise ValueError(msg)


@dataclass
class TextEntry:
    """A single piece of text detected from a video frame."""

    text: str
    language: LearningLanguage
    timestamp_seconds: float
    frame_index: int
    confidence: float
    bounding_box: tuple[int, int, int, int]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    is_low_confidence: bool = False
    screenshot_path: Path | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            msg = "confidence must be between 0.0 and 1.0"
            raise ValueError(msg)


@dataclass
class SampledFrame:
    """A single frame extracted from the video by FFmpeg."""

    index: int
    path: Path
    timestamp_seconds: float


@dataclass
class OCRResult:
    """A single text detection result from the OCR engine."""

    text: str
    confidence: float
    bounding_box: tuple[int, int, int, int]


@dataclass
class ExtractionSession:
    """Tracks the state of a single extraction run."""

    config: ExtractionConfig
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: ExtractionStatus = ExtractionStatus.PENDING
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    total_frames_sampled: int = 0
    total_frames_processed: int = 0
    all_entries: list[TextEntry] = field(default_factory=list)
    unique_entries: list[TextEntry] = field(default_factory=list)
    seen_texts: set[str] = field(default_factory=set)
    error_message: str | None = None
