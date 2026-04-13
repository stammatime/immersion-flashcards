"""Custom exceptions for the screen recorder module."""


class RecorderStateError(RuntimeError):
    """Raised when a recorder operation is called in the wrong state.

    Example: calling stop() while status is IDLE.
    """


class DiskSpaceError(OSError):
    """Raised when the save directory has insufficient free space.

    The check requires at least 500 MB free before launching FFmpeg.
    """

    def __init__(self, available_bytes: int, required_bytes: int = 500 * 1024 * 1024) -> None:
        self.available_bytes = available_bytes
        self.required_bytes = required_bytes
        available_mb = available_bytes / (1024 * 1024)
        required_mb = required_bytes / (1024 * 1024)
        super().__init__(
            f"Insufficient disk space: {available_mb:.0f} MB available, "
            f"{required_mb:.0f} MB required."
        )


class FFmpegNotFoundError(FileNotFoundError):
    """Raised when the FFmpeg binary cannot be found at the expected location."""

    def __init__(self, searched_path: str = "") -> None:
        self.searched_path = searched_path
        msg = "FFmpeg binary not found"
        if searched_path:
            msg += f" (searched: {searched_path})"
        super().__init__(msg)
