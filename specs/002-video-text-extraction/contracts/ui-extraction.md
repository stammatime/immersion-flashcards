# Contract: Extraction UI State Machine

**Module**: `src/ui/extraction_panel.py`
**Date**: 2026-04-19

## UI States

```
IDLE → CONFIGURED → PROCESSING → COMPLETE
                        ↓
                      ERROR
```

| State | User Can | Displays |
|---|---|---|
| IDLE | Select video file, select learning language | File picker, language dropdown, disabled Extract button |
| CONFIGURED | Click Extract, change settings | Enabled Extract button, video info summary |
| PROCESSING | Cancel extraction | Progress bar, frames processed count, current status label |
| COMPLETE | Open output folder, import to Anki (if available), start new extraction | Results summary: card count, transcript path, .apkg path |
| ERROR | Retry, change settings, start new extraction | Error message, retry button |

## State Transitions

| From | To | Trigger |
|---|---|---|
| IDLE | CONFIGURED | User selects a valid video file AND a learning language |
| CONFIGURED | IDLE | User clears the video selection or learning language |
| CONFIGURED | PROCESSING | User clicks "Extract" |
| PROCESSING | COMPLETE | Extraction finishes successfully |
| PROCESSING | ERROR | Extraction fails (OCR error, FFmpeg error, disk error) |
| PROCESSING | IDLE | User clicks "Cancel" |
| COMPLETE | IDLE | User clicks "New Extraction" |
| ERROR | CONFIGURED | User clicks "Retry" or adjusts settings |

## UI Elements

### Input Panel
- **Video file picker**: File dialog filtered to common video formats (mp4, mkv, avi, webm)
- **Learning language dropdown**: Required selection from supported languages
- **Additional languages checkboxes**: Optional, for transcript-only capture
- **Extract button**: Enabled only in CONFIGURED state

### Progress Panel (visible during PROCESSING)
- **Progress bar**: Shows frames processed / total frames sampled
- **Status label**: Current phase (Sampling frames... / Extracting text... / Building deck...)
- **Cancel button**: Stops extraction gracefully

### Results Panel (visible in COMPLETE state)
- **Card count**: Number of flashcards generated
- **Transcript path**: Clickable link to open transcript file
- **Deck path**: Clickable link to open .apkg file location
- **Low-confidence count**: Number of entries flagged for review
- **Open in Anki button**: Launches .apkg file with system default handler

## Accessibility Requirements (WCAG 2.1 AA)

- All controls have visible labels and accessible names
- Progress bar has `aria-valuenow`, `aria-valuemin`, `aria-valuemax` equivalents (Qt accessibility)
- Status changes announced to screen readers
- Keyboard navigable: Tab order follows visual layout
- Color is not the sole indicator of state (text labels accompany all states)
