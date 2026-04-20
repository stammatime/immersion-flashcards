"""Exception classes for the video text extraction pipeline."""


class ExtractionError(Exception):
    """Base exception for extraction pipeline errors."""


class OCREngineError(ExtractionError):
    """Raised when the OCR engine fails to initialize or process a frame."""


class NoTextDetectedError(ExtractionError):
    """Raised when no text is detected in the entire video."""
