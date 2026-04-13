# Language Review App

A cross-platform screen recorder designed for language learners. Record gameplay or movies, then extract subtitles, parse new vocabulary, and generate flashcards — all from what you actually watched.

> **Current scope:** Screen recording only. Subtitle extraction and flashcard generation are planned for future releases.

## Features

- Record any display at 30 fps (Windows and macOS)
- Start and stop recording with a single button
- Choose where recordings are saved
- Select which display to record when multiple monitors are connected
- Elapsed recording time displayed live
- Recordings saved as MP4 (H.264)

## Requirements

- Python 3.11+
- FFmpeg (see [FFmpeg Setup](#ffmpeg-setup) below)

## Installation

```bash
git clone https://github.com/stammatime/immersion-flashcards.git
cd immersion-flashcards

python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS
source .venv/bin/activate

pip install -r requirements-dev.txt
```

## Running

```bash
python -m src.main
```

## FFmpeg Setup

FFmpeg is required for screen capture. The app finds it in this order:

1. **Bundled binary** — placed alongside the executable (used in distributed builds)
2. **`imageio-ffmpeg`** — installed automatically with `requirements-dev.txt`; no manual setup needed for development
3. **System PATH** — if `ffmpeg` is available globally

For development, `imageio-ffmpeg` handles FFmpeg automatically. No extra steps needed.

## Running Tests

```bash
python -m pytest
```

The test suite uses mocked FFmpeg subprocesses — no recording hardware or FFmpeg binary required.

## Building a Distributable

Place an `ffmpeg.exe` (Windows) or `ffmpeg` (macOS) binary at the project root, then:

```bash
pip install pyinstaller
pyinstaller language_review_app.spec
```

Output: `dist/LanguageReviewApp.exe` (Windows) or `dist/LanguageReviewApp` (macOS).

## Project Structure

```
src/
  main.py                  # Entry point
  recorder/
    screen_recorder.py     # FFmpeg orchestration
    display_enumerator.py  # Detect connected displays
    models.py              # RecordingStatus, Display, Recording
    exceptions.py          # DiskSpaceError, FFmpegNotFoundError, etc.
  settings/
    settings_manager.py    # Load/save user preferences
    models.py              # Settings dataclass
  ui/
    main_window.py         # Main application window
tests/
  unit/
    recorder/
    settings/
  integration/
specs/                     # Feature specifications and implementation plans
```

## Settings

User preferences are saved automatically to:

- **Windows:** `%APPDATA%\LanguageReviewApp\settings.json`
- **macOS:** `~/Library/Application Support/LanguageReviewApp/settings.json`

## Roadmap

- [ ] Subtitle extraction from recordings
- [ ] Vocabulary parsing and deduplication
- [ ] Flashcard generation and export
- [ ] Linux support
