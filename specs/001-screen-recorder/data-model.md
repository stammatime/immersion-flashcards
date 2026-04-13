# Data Model: Screen Recorder

**Feature**: 001-screen-recorder
**Date**: 2026-04-12

---

## Entities

### Recording

Represents a single screen capture session from start to stop.

| Field | Type | Description | Constraints |
|---|---|---|---|
| `id` | str (UUID4) | Unique identifier for this recording session | Auto-generated on start |
| `start_time` | datetime | When recording began (local time) | Set on start; not None while recording |
| `end_time` | datetime \| None | When recording ended | None while in progress |
| `duration_seconds` | float \| None | Elapsed time in seconds | Derived: end_time - start_time; None if in progress |
| `save_path` | Path | Full filesystem path of the output MP4 file | Must resolve to a writable file |
| `display_id` | str | Identifier of the captured display | System display identifier from Qt |
| `status` | RecordingStatus | Current state of this recording | See state machine below |
| `partial` | bool | True if recording ended unexpectedly (crash, disk full) | Defaults to False |

**State machine** (`RecordingStatus`):

```
IDLE ──► RECORDING ──► STOPPING ──► COMPLETE
                   └──────────────► PARTIAL  (unexpected termination)
                                ──► FAILED   (FFmpeg process error)
```

Transitions:
- `IDLE → RECORDING`: User presses Start; FFmpeg process launched; start_time set
- `RECORDING → STOPPING`: User presses Stop; SIGTERM sent to FFmpeg; file being finalized
- `STOPPING → COMPLETE`: FFmpeg process exits 0; end_time set; file verified readable
- `RECORDING → PARTIAL`: Unexpected process termination; partial file preserved if > 0 bytes
- `STOPPING → FAILED`: FFmpeg exits non-zero; error message captured; file may be corrupt

---

### Display

Represents a connected monitor available for capture. Derived at runtime from the OS; not persisted.

| Field | Type | Description |
|---|---|---|
| `id` | str | Platform-specific display identifier (Qt screen name) |
| `label` | str | Human-readable name (e.g., "Display 1 — Primary", "Display 2") |
| `width` | int | Display width in physical pixels |
| `height` | int | Display height in physical pixels |
| `x` | int | Left offset of display in the virtual desktop coordinate space |
| `y` | int | Top offset of display in the virtual desktop coordinate space |
| `is_primary` | bool | True if this is the OS-designated primary display |
| `scale_factor` | float | DPI scale factor (e.g., 1.0 for 96 DPI, 2.0 for HiDPI/Retina) |

**Invariants**:
- At least one Display is always present.
- Exactly one Display has `is_primary = True`.
- Display list is re-enumerated whenever the application window detects a screen change event.

---

### Settings

User configuration persisted across sessions. Stored as JSON in the OS user config directory.

| Field | Type | Default | Description |
|---|---|---|---|
| `save_directory` | str (path) | OS Videos/Movies folder | Absolute path to folder where recordings are saved |
| `selected_display_id` | str \| None | None (primary display) | ID of the last-selected display; None means primary |
| `app_version` | str | Current app version | Used for future settings migration |

**Persistence location**:
- Windows: `%APPDATA%\LanguageReviewApp\settings.json`
- macOS: `~/Library/Application Support/LanguageReviewApp/settings.json`

**Validation on load**:
- If `save_directory` no longer exists or is not writable → reset to OS default and warn user.
- If `selected_display_id` no longer matches any connected display → reset to None (primary).
- If file is missing or malformed JSON → use all defaults; do not crash.

---

## Key Relationships

```
Settings ──references──► Display (by selected_display_id)
Settings ──provides──► Recording.save_path (directory portion)
Recording ──captured from──► Display
```

---

## File Naming Convention

Output files are named deterministically to avoid collisions:

```
recording_YYYYMMDD_HHMMSS.mp4
```

Example: `recording_20260412_143022.mp4`

Generated at Recording start using local time. The full path is:
```
{Settings.save_directory}/{recording_YYYYMMDD_HHMMSS.mp4}
```
