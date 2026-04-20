# Contract: Anki Exporter Module

**Module**: `src/anki/`
**Date**: 2026-04-19

## DeckBuilder

Builds an Anki deck from deduplicated text entries and their screenshots.

### `__init__(deck_name: str, description: str = "")`

- Creates a new deck builder with the given name
- Generates deterministic `deck_id` and `model_id` from the deck name
- Sets up the Anki note model with fields: Front, Back, Language, Timestamp

### `add_card(entry: FlashcardEntry) -> None`

- **Input**: A FlashcardEntry with text, screenshot filename, and metadata
- **Side effect**: Adds a note to the internal deck
- **Invariant**: Cards are added in the order they were first encountered in the video

### `get_metadata() -> DeckMetadata`

- **Output**: Current deck metadata including card count

## AnkiExporter

Writes the built deck to an .apkg file with embedded media.

### `export(deck_builder: DeckBuilder, media_dir: Path, output_path: Path) -> Path`

- **Input**: A populated DeckBuilder, directory containing screenshot images, output .apkg path
- **Output**: Path to the written .apkg file
- **Errors**: `IOError` on write failure; `ValueError` if deck has zero cards
- **Side effects**: Creates the .apkg file at `output_path`
- **Invariant**: All screenshot files referenced by cards exist in `media_dir`
- **Format**: Standard Anki package (ZIP containing collection.anki2 + media files)

## Card Template

### Note Model Fields

| Field | Content |
|---|---|
| Front | Extracted text (plain text) |
| Back | `<img src="screenshot.png"><br><small>Language · Timestamp · Confidence</small>` |
| Language | Language tag (e.g., "Japanese", "Chinese (Simplified)") |
| Timestamp | Video timestamp where text first appeared (HH:MM:SS) |

### Card Layout

- **Front template**: `{{Front}}`
- **Back template**: `{{FrontSide}}<hr id="answer">{{Back}}`
- **Styling**: Clean, readable font; image scaled to fit card width
