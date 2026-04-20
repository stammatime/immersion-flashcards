# Research: Video Text Extraction for Anki Flashcards

**Date**: 2026-04-19
**Branch**: `002-video-text-extraction`

## Decision 1: OCR Engine Selection

### Decision

Use a **two-engine strategy**:
- **manga-ocr** for Japanese text (hiragana, katakana, kanji)
- **PaddleOCR (PP-OCRv5)** for Chinese (simplified + traditional) and English

### Rationale

- **manga-ocr** is purpose-built for Japanese text in manga and games. It uses a fine-tuned
  vision-language transformer and handles stylized game fonts, furigana, and vertical text
  with the highest accuracy among all evaluated options. MIT licensed, easy to install.
- **PaddleOCR PP-OCRv5** is the best general-purpose CJK engine. It handles simplified
  Chinese, traditional Chinese, and English in a single pass with strong accuracy on dense
  game UI text. Fast on CPU (~0.5-2s per frame). Apache 2.0 licensed.
- The user selects their learning language in the UI, so the system knows which engine to
  invoke — no runtime language detection overhead required.

### Alternatives Considered

| Engine | Why Rejected |
|---|---|
| Tesseract (pytesseract) | Poor CJK accuracy on video game text; struggles with stylized fonts and mixed-orientation text |
| EasyOCR | Good multi-language support but too slow on CPU (~3-10s per frame); accuracy weaker than PaddleOCR on game UIs |
| PaddleOCR alone | Capable of Japanese but manga-ocr is measurably better for game/manga-style Japanese text |
| manga-ocr alone | Japanese only; cannot handle Chinese or English |

## Decision 2: Anki Export Format

### Decision

Use the **genanki** Python library to generate `.apkg` (Anki deck package) files with
embedded media (screenshot images).

### Rationale

- `.apkg` is Anki's native import format — a ZIP archive containing a SQLite database
  (`collection.anki2`) plus a media folder and manifest.
- **genanki** is the standard Python library for this purpose, actively maintained, and
  straightforward to use. MIT licensed.
- Cards will use a custom note type with fields: Front (extracted text), Back (screenshot
  + metadata), Language, Timestamp.
- Screenshots are embedded via `<img src="filename.jpg">` in the card template and passed
  to `genanki.Package(media_files=[...])`.

### Alternatives Considered

| Format | Why Rejected |
|---|---|
| CSV/TSV import | Cannot embed images inline; user would need to manually copy media to Anki's collection.media folder |
| CrowdAnki JSON | Less widely supported; genanki has better documentation and community adoption |

## Decision 3: Frame Sampling Strategy

### Decision

Use **FFmpeg scene-change detection** to extract key frames, supplemented by **perceptual
hashing** (difference hashing) to skip visually identical frames.

### Rationale

- Processing every frame of a 30-minute video at 30fps = 54,000 frames. Running OCR on
  each is infeasible (~15-27 hours on CPU).
- FFmpeg's `select='gt(scene,0.3)'` filter detects scene changes and extracts only frames
  where the visual content significantly changes — this naturally captures dialogue box
  appearances, menu transitions, and new text screens.
- A secondary perceptual hash comparison (using `imagehash` or simple pixel diffing) skips
  near-duplicate frames that FFmpeg's scene filter still lets through.
- Estimated frame count after filtering: 200-800 frames for a 30-minute video, bringing
  OCR processing time to 2-15 minutes on CPU.

### Alternatives Considered

| Strategy | Why Rejected |
|---|---|
| Fixed interval sampling (e.g., 1 frame/sec) | Misses brief dialogue; processes too many identical frames during static scenes |
| Every frame | Computationally infeasible (54,000 OCR calls for 30 minutes) |
| Text region detection first, then OCR | Adds complexity; scene-change detection achieves similar filtering more simply |

## Decision 4: Language Detection vs. User Selection

### Decision

Use **user-specified learning language** to select the OCR engine. Do not perform automatic
per-frame language detection.

### Rationale

- The user always knows what language their game is in. Asking them to specify it is one
  UI interaction that eliminates an entire class of detection errors.
- Japanese and Chinese share kanji/hanzi characters, making automatic detection unreliable
  without sentence-level context. User selection sidesteps this entirely.
- The OCR engine itself (manga-ocr for JA, PaddleOCR for ZH/EN) implicitly handles the
  language — the engine choice is the language choice.
- For "both languages" mode (e.g., Japanese game with English UI), both engines run and
  results are tagged by which engine produced them.

### Alternatives Considered

| Approach | Why Rejected |
|---|---|
| Automatic language detection per text region | Unreliable for JA/ZH disambiguation; adds latency and complexity |
| Character set heuristics (Unicode ranges) | Kanji/Hanzi overlap makes this unreliable without sentence context |

## Decision 5: Text Deduplication Strategy

### Decision

Use **exact string match** for deduplication. A word/phrase generates a flashcard only on
its first occurrence.

### Rationale

- Simple, predictable, and easy to explain to users.
- Conjugation-aware deduplication (e.g., grouping verb forms) requires a morphological
  analyzer (like MeCab for Japanese), which adds significant complexity and is better
  suited as a future enhancement.
- The spec explicitly states: "first occurrence deduplication is based on exact text match."

### Alternatives Considered

| Approach | Why Rejected (for now) |
|---|---|
| Morphological normalization (MeCab/Jieba) | Scope creep; valuable but belongs in a future feature |
| Fuzzy matching (edit distance) | Too aggressive — would merge intentionally distinct entries |

## Dependencies Summary

| Package | Purpose | License |
|---|---|---|
| manga-ocr | Japanese OCR | MIT |
| paddleocr + paddlepaddle | Chinese/English OCR | Apache 2.0 |
| genanki | Anki .apkg generation | MIT |
| imagehash (or Pillow-based) | Perceptual hashing for frame dedup | BSD |
| Pillow | Image handling | HPND (permissive) |
