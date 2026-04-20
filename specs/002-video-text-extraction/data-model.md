# Data Model: Video Text Extraction

**Date**: 2026-04-19
**Branch**: `002-video-text-extraction`

## Entities

### ExtractionConfig

User-specified configuration for an extraction session.

| Field | Type | Description |
|---|---|---|
| video_path | Path | Absolute path to the input video file |
| learning_language | LearningLanguage | User's target language for flashcard generation |
| additional_languages | list[LearningLanguage] | Optional extra languages for transcript capture (no flashcards) |
| output_directory | Path | Where to write the .apkg, transcript, and screenshots |
| scene_threshold | float | FFmpeg scene change sensitivity (default: 0.3) |
| confidence_threshold | float | Minimum OCR confidence to accept a result (default: 0.5) |

### LearningLanguage (Enum)

| Value | Description |
|---|---|
| JAPANESE | Japanese (hiragana, katakana, kanji) — uses manga-ocr engine |
| CHINESE_SIMPLIFIED | Simplified Chinese — uses PaddleOCR |
| CHINESE_TRADITIONAL | Traditional Chinese — uses PaddleOCR |
| ENGLISH | English — uses PaddleOCR |

### TextEntry

A single piece of text detected from a video frame.

| Field | Type | Description |
|---|---|---|
| id | str | UUID v4 identifier |
| text | str | The detected text content |
| language | LearningLanguage | Detected/assigned language |
| timestamp_seconds | float | Approximate position in the video (seconds) |
| frame_index | int | Index of the sampled frame this was extracted from |
| confidence | float | OCR confidence score (0.0 to 1.0) |
| bounding_box | tuple[int, int, int, int] | (x, y, width, height) pixel region in the frame |
| is_low_confidence | bool | True if confidence < confidence_threshold |
| screenshot_path | Path | None | Path to the saved screenshot; None until screenshot is captured |

### ExtractionSession

Tracks the state of a single extraction run.

| Field | Type | Description |
|---|---|---|
| id | str | UUID v4 identifier |
| config | ExtractionConfig | The configuration used for this session |
| status | ExtractionStatus | Current state of the extraction |
| start_time | datetime | When extraction began |
| end_time | datetime | None | When extraction completed; None while in progress |
| total_frames_sampled | int | Number of frames extracted from the video |
| total_frames_processed | int | Number of frames OCR has been run on so far |
| all_entries | list[TextEntry] | All detected text entries (for transcript) |
| unique_entries | list[TextEntry] | First-occurrence entries only (for flashcards) |
| seen_texts | set[str] | Set of text strings already encountered (for deduplication) |
| error_message | str | None | Error details if extraction failed |

### ExtractionStatus (Enum)

| Value | Transitions To | Description |
|---|---|---|
| PENDING | SAMPLING | Initial state before processing begins |
| SAMPLING | EXTRACTING, FAILED | FFmpeg is extracting key frames from the video |
| EXTRACTING | BUILDING, FAILED | OCR is processing sampled frames |
| BUILDING | COMPLETE, FAILED | Anki deck is being assembled |
| COMPLETE | — | Extraction finished successfully |
| FAILED | — | Extraction failed with an error |

State machine:
```
PENDING → SAMPLING → EXTRACTING → BUILDING → COMPLETE
             ↓            ↓           ↓
           FAILED       FAILED      FAILED
```

### FlashcardEntry

A single Anki card derived from a first-occurrence TextEntry.

| Field | Type | Description |
|---|---|---|
| front_text | str | The extracted text (card front) |
| back_html | str | HTML content for card back (screenshot image tag + metadata) |
| screenshot_filename | str | Basename of the screenshot file (for Anki media) |
| language | LearningLanguage | Language of the text |
| timestamp_seconds | float | Where in the video this text first appeared |
| confidence | float | OCR confidence score |
| tags | list[str] | Anki tags (e.g., language name, low-confidence flag) |

### DeckMetadata

Metadata for the generated Anki deck.

| Field | Type | Description |
|---|---|---|
| deck_name | str | Name of the Anki deck (derived from video filename + language) |
| deck_id | int | Unique deck ID for genanki (deterministic hash of deck name) |
| model_id | int | Unique model/note type ID for genanki |
| description | str | Deck description including source video and extraction date |
| card_count | int | Number of cards in the deck |

## Relationships

```
ExtractionConfig ──1:1──► ExtractionSession
ExtractionSession ──1:*──► TextEntry (all_entries)
ExtractionSession ──1:*──► TextEntry (unique_entries, subset of all_entries)
TextEntry ──1:0..1──► FlashcardEntry (only for first-occurrence learning-language entries)
FlashcardEntry ──*:1──► DeckMetadata (all cards belong to one deck)
```

## Validation Rules

- `ExtractionConfig.video_path` MUST exist and be a readable file
- `ExtractionConfig.learning_language` MUST be set (no default)
- `ExtractionConfig.scene_threshold` MUST be between 0.0 and 1.0
- `ExtractionConfig.confidence_threshold` MUST be between 0.0 and 1.0
- `TextEntry.confidence` MUST be between 0.0 and 1.0
- `FlashcardEntry.screenshot_filename` MUST not contain path separators (basename only)
- `DeckMetadata.deck_name` MUST be non-empty
