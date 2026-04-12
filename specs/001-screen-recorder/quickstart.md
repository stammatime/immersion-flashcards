# Quickstart: Screen Recorder

**Feature**: 001-screen-recorder
**Date**: 2026-04-12

This guide covers how to set up a development environment, run the app, and verify
the golden path end-to-end.

---

## Prerequisites

- Python 3.11 or later
- pip (comes with Python)
- FFmpeg installed and on PATH **or** will be bundled (see below)
- Windows 10+ **or** macOS 12 (Monterey)+

---

## Setup

```bash
# Clone the repo and enter the project directory
git clone <repo-url>
cd language-review-app

# Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Run the Application

```bash
python -m src.main
```

The main window opens. On macOS, the first time you record, macOS will display a system
permission prompt for screen recording access — you must grant this in
**System Settings → Privacy & Security → Screen Recording**.

---

## Golden Path Validation

Follow these steps to verify the screen recorder works end-to-end:

1. Launch the app: `python -m src.main`
2. Note the default save folder shown in the UI (should be your Videos/Movies folder).
3. Click **Start Recording**.
   - Status indicator turns red and shows "Recording".
   - Elapsed timer begins counting.
4. Wait at least 3 seconds.
5. Click **Stop Recording**.
   - Status returns to "Idle".
   - Timer resets to `00:00`.
6. Open the save folder. Verify that a file named `recording_YYYYMMDD_HHMMSS.mp4` exists.
7. Open the file in a media player and confirm it plays the captured screen content.

---

## Run Tests

```bash
# All tests
pytest

# Unit tests only (no FFmpeg subprocess spawned)
pytest tests/unit/

# Integration tests (requires FFmpeg on PATH or bundled binary)
pytest tests/integration/
```

---

## Change Save Location

1. Click **Choose Folder** in the UI.
2. Select any writable folder in the OS folder dialog.
3. Confirm. The displayed path updates immediately.
4. Settings are saved automatically — restart the app and verify the folder is remembered.

---

## Multi-Monitor (if applicable)

If you have more than one display connected:
1. A **Display** dropdown appears in the UI.
2. Select a non-primary display.
3. Record for a few seconds.
4. Verify the output video shows only that display's content.

---

## Packaging (Distribution Build)

```bash
# Install PyInstaller
pip install pyinstaller

# Build a single-file executable (bundles Python + FFmpeg)
pyinstaller src/main.py --name LanguageReviewApp --onefile --windowed \
    --add-binary "path/to/ffmpeg:ffmpeg"

# Output: dist/LanguageReviewApp (macOS) or dist/LanguageReviewApp.exe (Windows)
```

---

## Common Issues

| Problem | Likely Cause | Fix |
|---|---|---|
| "FFmpeg not found" error | FFmpeg not on PATH and not bundled | Install FFmpeg or add it to PATH |
| macOS: recording is a black screen | Screen Recording permission not granted | Grant in System Settings → Privacy & Security |
| "Save folder is not writable" warning | Folder permissions or read-only drive | Choose a different folder |
| Timer counts but no file appears | FFmpeg crashed — check console output | Check logs; verify FFmpeg version is 5.0+ |
