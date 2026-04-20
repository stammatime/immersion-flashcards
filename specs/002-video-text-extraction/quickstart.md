# Quickstart: Video Text Extraction

**Date**: 2026-04-19
**Branch**: `002-video-text-extraction`

## Prerequisites

- Python 3.11+
- FFmpeg 5.0+ on PATH (already required by 001-screen-recorder)
- pip (Python package manager)

## Setup

```bash
# Clone and switch to feature branch
git checkout 002-video-text-extraction

# Install dependencies (from repo root)
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### New Dependencies (added by this feature)

```text
# OCR engines
manga-ocr          # Japanese text recognition
paddleocr           # Chinese/English text recognition
paddlepaddle        # PaddleOCR runtime

# Anki export
genanki             # .apkg file generation

# Image processing
Pillow              # Image handling (likely already installed via PyQt6)
imagehash           # Perceptual hashing for frame dedup
```

### Platform Notes

**Windows**: PaddlePaddle installs cleanly via pip. No additional setup needed.

**macOS (Apple Silicon)**: PaddlePaddle may require the CPU-only wheel:
```bash
pip install paddlepaddle -f https://www.paddlepaddle.org.cn/whl/mac/cpu/develop.html
```

**First run**: manga-ocr and PaddleOCR download their model files on first use (~400MB for
manga-ocr, ~50-200MB for PaddleOCR). This is a one-time download. An internet connection
is required for the initial setup but not for subsequent use.

## Validate Setup

```bash
# Run all tests
cd src && pytest

# Run only extraction tests
pytest tests/unit/extractor/ tests/unit/anki/

# Run integration test (requires a sample video in tests/fixtures/)
pytest tests/integration/test_extraction_flow.py

# Lint
ruff check .
```

## Golden Path Validation

1. Launch the application: `python src/main.py`
2. Navigate to the extraction panel/tab
3. Select a video file containing visible Japanese text
4. Set learning language to "Japanese"
5. Click "Extract"
6. Verify: progress bar advances through Sampling → Extracting → Building
7. Verify: completion screen shows card count > 0, transcript path, and .apkg path
8. Open the .apkg file in Anki — verify cards display text on front, screenshot on back
9. Open the transcript file — verify chronological entries with timestamps

## Test Fixtures

Place sample test data in `tests/fixtures/`:

```text
tests/fixtures/
├── sample_frames/
│   ├── japanese_dialogue.png     # RPG dialogue box with Japanese text
│   ├── chinese_menu.png          # Game menu with Chinese text
│   ├── english_ui.png            # English UI overlay
│   ├── mixed_language.png        # Frame with multiple languages
│   └── no_text.png               # Game scene with no text
└── expected_outputs/
    ├── japanese_transcript.txt   # Expected transcript for Japanese frames
    └── expected_cards.json       # Expected card content for validation
```
