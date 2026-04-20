# Contract: Extractor Module

**Module**: `src/extractor/`
**Date**: 2026-04-19

## FrameSampler

Extracts key frames from a video file using FFmpeg scene-change detection.

### `sample_frames(video_path, output_dir, scene_threshold=0.3) -> list[SampledFrame]`

- **Input**: Path to video file, directory to save frames, scene change sensitivity
- **Output**: List of `SampledFrame(index: int, path: Path, timestamp_seconds: float)`
- **Errors**: `FileNotFoundError` if video does not exist; `ExtractionError` if FFmpeg fails
- **Side effects**: Writes PNG files to `output_dir`
- **Invariant**: Frames are ordered by timestamp; no two frames have the same timestamp

### `is_duplicate_frame(frame_a_path, frame_b_path, threshold=10) -> bool`

- **Input**: Paths to two frame images, perceptual hash distance threshold
- **Output**: True if frames are visually near-identical
- **Errors**: `FileNotFoundError` if either file does not exist

## OCREngine

Runs text detection on a single frame image. Wraps manga-ocr and PaddleOCR.

### `__init__(language: LearningLanguage)`

- Initializes the appropriate OCR backend for the given language
- **Errors**: `OCREngineError` if the backend fails to initialize (missing model files, etc.)

### `extract_text(frame_path: Path) -> list[OCRResult]`

- **Input**: Path to a frame image (PNG)
- **Output**: List of `OCRResult(text: str, confidence: float, bounding_box: tuple[int,int,int,int])`
- **Errors**: `OCREngineError` on engine failure
- **Invariant**: Results are ordered top-to-bottom, left-to-right by bounding box position

## TextDeduplicator

Tracks seen text and emits only first occurrences.

### `__init__()`

- Creates an empty deduplicator with no seen entries

### `process(entry: TextEntry) -> bool`

- **Input**: A TextEntry to check
- **Output**: True if this is the first occurrence (not seen before); False if duplicate
- **Side effect**: Adds the entry's text to the seen set if it was new
- **Invariant**: For any text string, only the first call returns True

### `reset()`

- Clears all seen entries

## TranscriptWriter

Writes the full chronological transcript to a file.

### `write(entries: list[TextEntry], output_path: Path) -> Path`

- **Input**: All text entries in chronological order, output file path
- **Output**: Path to the written transcript file
- **Format**: One entry per line: `[HH:MM:SS] [LANG] text content`
- **Errors**: `IOError` on write failure
