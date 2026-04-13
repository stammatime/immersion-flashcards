# Research: Screen Recorder

**Feature**: 001-screen-recorder
**Date**: 2026-04-12
**Status**: Complete — all NEEDS CLARIFICATION resolved

---

## Decision 1: Programming Language

**Decision**: Python 3.11+

**Rationale**: The overarching Language Review App will require NLP processing, OCR for subtitle
extraction, and flashcard generation — all domains where Python has the deepest library ecosystem
(spaCy, EasyOCR, Anki-connect, etc.). Keeping the screen recorder in Python avoids a language
boundary that would complicate the eventual pipeline integration. Python 3.11 is the current LTS
with the best performance improvements.

**Alternatives considered**:
- *Electron/TypeScript*: Good screen capture support via `desktopCapturer`, but introduces a
  Node.js boundary that would complicate the NLP pipeline later. Heavy runtime.
- *Rust + Tauri*: Excellent performance and small binary, but the Rust NLP ecosystem is immature
  compared to Python's, making future pipeline work harder.
- *Go + Fyne*: Limited GUI ecosystem; screen capture libraries are thin on macOS.

---

## Decision 2: GUI Framework

**Decision**: PyQt6 (Qt6 bindings for Python)

**Rationale**: PyQt6 renders native-looking controls on both Windows and macOS with a single
codebase. It supports the Qt file dialog (`QFileDialog`) which is exactly what FR-006 requires
for the OS-native folder picker. WCAG 2.1 AA compliance (Principle IV) is achievable via Qt's
built-in accessibility APIs. MIT-compatible for commercial use with PyQt6 Commercial or using
PySide6 (LGPL) as a drop-in alternative.

**Alternatives considered**:
- *Tkinter*: Built into Python but visually dated; native folder picker support is inconsistent
  on macOS.
- *PySide6*: Functionally equivalent to PyQt6 (same Qt6 base), LGPL license. Viable drop-in
  if licensing is a concern; plan is compatible with either.
- *wxPython*: Older, less actively maintained; smaller community.
- *Dear PyGui*: Immediate-mode; not well-suited to a simple form-style app.

---

## Decision 3: Screen Capture & Video Encoding

**Decision**: FFmpeg via subprocess, using platform-native input devices

**Rationale**: FFmpeg is the most reliable, widely tested, and performant cross-platform video
capture and encoding tool available. It ships platform-native capture backends:
- **Windows**: `gdigrab` (GDI-based, all Windows 10+ GPUs) and optionally `dshow`
- **macOS**: `avfoundation` (ScreenCaptureKit-backed on macOS 12+, system permission dialog built in)

By driving FFmpeg from Python via subprocess, the Python code is thin orchestration; the
heavy lifting (frame capture, encoding, muxing) is handled by a battle-tested C library. This
also means codec choices (H.264/libx264 for maximum compatibility) are configuration, not code.

FFmpeg will be bundled with the application via PyInstaller to ensure users don't need to
install it manually (satisfying FR-009 and FR-010).

**Output format**: MP4 container, H.264 video (libx264), no audio track. MP4+H.264 is playable
on Windows and macOS without additional codecs (FR-005).

**Alternatives considered**:
- *mss + OpenCV/PyAV*: `mss` captures PIL/numpy frames; OpenCV can encode. Works but at 30 fps
  capturing 1080p frames in Python creates a CPU bottleneck not present when FFmpeg handles
  the capture natively. Also requires bundling multiple large libraries.
- *OBS via websocket*: Powerful but introduces an external application dependency that users
  must install and configure.
- *Platform SDKs directly (DirectShow / ScreenCaptureKit via pyobjc)*: Maximum performance
  but requires maintaining two completely separate code paths.

---

## Decision 4: Settings Persistence

**Decision**: JSON file stored in the OS user config directory

**Rationale**: Settings are a simple key-value store (save path, display index). A JSON file
is readable/writable without any dependencies, trivially testable, and portable. The OS user
config directory (`%APPDATA%\LanguageReviewApp` on Windows, `~/Library/Application Support/LanguageReviewApp`
on macOS) is the standard location for per-user config and avoids polluting the install
directory.

**Alternatives considered**:
- *SQLite*: Overkill for a handful of settings keys.
- *Windows Registry / macOS NSUserDefaults*: Platform-specific; would require two separate
  implementations.
- *INI / TOML*: Viable but adds a parsing dependency; JSON is built into Python.

---

## Decision 5: Multi-Display Enumeration

**Decision**: Enumerate displays via Qt's `QScreen` API for display listing; pass selected
display coordinates to FFmpeg's capture offset arguments.

**Rationale**: `QScreen` provides display geometry (position, size, scale factor) in a
platform-agnostic way. The selected display's geometry is translated to FFmpeg arguments:
- **Windows** (`gdigrab`): `-offset_x`, `-offset_y`, `-video_size` to crop to the chosen display
- **macOS** (`avfoundation`): Display index passed as the input device number (e.g., `"1"`, `"2"`)

**Alternatives considered**:
- *screeninfo Python library*: Cross-platform but adds a dependency that QScreen already replaces.
- *Platform-specific APIs (EnumDisplayMonitors / NSScreen)*: Unnecessary given Qt's abstraction.

---

## Decision 6: Testing Strategy

**Decision**: pytest with a FFmpeg mock for unit tests; real FFmpeg subprocess for integration tests

**Rationale**: FFmpeg subprocess calls are the main side-effecting boundary. Unit tests mock
the subprocess to verify the recorder module constructs correct FFmpeg arguments for each
platform and configuration. Integration tests launch FFmpeg against a test display area and
verify that an MP4 file is produced and is valid (readable duration > 0).

Settings persistence is tested by writing to a temp directory and reading back.
GUI is tested via PyQt's `QTest` module for widget interactions.

---

## NEEDS CLARIFICATION — All Resolved

| Question | Resolution | Source |
|---|---|---|
| Audio capture included? | Out of scope — video-only per spec Assumptions | spec.md |
| Linux supported? | Out of scope — Windows + macOS only per spec Assumptions | spec.md |
| Window-level capture? | Out of scope — full-display capture only per spec Assumptions | spec.md |
| Output codec? | MP4 + H.264 (libx264) — maximum compatibility, no decoder install required | Decision 3 |
| Settings file location? | OS user config dir — standard convention for both platforms | Decision 4 |
| FFmpeg bundled or expected? | Bundled via PyInstaller — satisfies FR-009/FR-010 | Decision 3 |
