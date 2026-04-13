# Contract: Recorder Module

**Module**: `src/recorder/`
**Consumer**: UI layer (`src/ui/`)
**Date**: 2026-04-12

This contract defines the public interface that the recorder module exposes to the UI.
The UI MUST NOT access FFmpeg or OS screen-capture APIs directly; all capture logic
goes through this interface.

---

## ScreenRecorder (class)

### Constructor

```python
ScreenRecorder(settings: Settings)
```

- Accepts the current application settings.
- Does NOT start a recording. Does NOT launch FFmpeg.
- Raises `ValueError` if `settings.save_directory` does not exist.

---

### Properties

| Property | Type | Description |
|---|---|---|
| `status` | `RecordingStatus` | Current state (IDLE, RECORDING, STOPPING, COMPLETE, PARTIAL, FAILED) |
| `current_recording` | `Recording \| None` | The active or most-recently completed Recording object; None if never started |
| `elapsed_seconds` | `float` | Seconds elapsed since recording started; 0.0 when IDLE |

---

### Methods

#### `start(display: Display) -> None`

Begins recording the given display.

**Preconditions**:
- `status == RecordingStatus.IDLE`
- `settings.save_directory` exists and is writable
- Sufficient disk space (checked before launch; raises `DiskSpaceError` if < 500 MB free)

**Postconditions**:
- `status == RecordingStatus.RECORDING`
- `current_recording.start_time` is set
- FFmpeg subprocess is running

**Raises**:
- `RecorderStateError` — if not in IDLE state
- `DiskSpaceError` — if insufficient disk space
- `PermissionError` — if save directory is not writable
- `FFmpegNotFoundError` — if FFmpeg binary is not found

---

#### `stop() -> Recording`

Stops the active recording and returns the completed Recording object.

**Preconditions**:
- `status == RecordingStatus.RECORDING`

**Postconditions**:
- `status == RecordingStatus.COMPLETE` (or PARTIAL/FAILED on error)
- `current_recording.end_time` is set
- Output file exists at `current_recording.save_path`

**Raises**:
- `RecorderStateError` — if not in RECORDING state

**Returns**: The completed `Recording` object.

---

### Signals (Qt signals for UI binding)

| Signal | Payload | Emitted when |
|---|---|---|
| `status_changed` | `RecordingStatus` | State transitions |
| `elapsed_updated` | `float` | Every second while RECORDING (elapsed seconds) |
| `recording_completed` | `Recording` | Successful COMPLETE transition |
| `error_occurred` | `str` | Any FAILED or unexpected termination (human-readable message) |

---

## DisplayEnumerator (class)

### `list_displays() -> list[Display]`

Returns all currently connected displays. Always returns at least one element (the primary display).
Display list reflects the physical state at the time of the call; call again after
`QApplication.screenAdded` / `QApplication.screenRemoved` events.

---

## Error Types

| Exception | Description |
|---|---|
| `RecorderStateError` | Operation called in wrong state |
| `DiskSpaceError` | Less than 500 MB free in save directory |
| `FFmpegNotFoundError` | FFmpeg binary not found in expected location |
