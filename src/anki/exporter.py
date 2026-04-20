"""Anki .apkg file exporter with media embedding."""

from __future__ import annotations

from pathlib import Path

import genanki

from src.anki.deck_builder import DeckBuilder


class AnkiExporter:
    """Writes a built deck to an .apkg file with embedded media."""

    def export(
        self,
        deck_builder: DeckBuilder,
        media_dir: Path,
        output_path: Path,
    ) -> Path:
        """Export the deck as an .apkg file.

        Args:
            deck_builder: A populated DeckBuilder with cards added.
            media_dir: Directory containing screenshot images referenced by cards.
            output_path: Path for the output .apkg file.

        Returns:
            Path to the written .apkg file.

        Raises:
            ValueError: If the deck has zero cards.
            IOError: If writing fails.
        """
        meta = deck_builder.get_metadata()
        if meta.card_count == 0:
            msg = "Cannot export a deck with zero cards"
            raise ValueError(msg)

        # Collect media files referenced by cards
        media_files = []
        for card in deck_builder.cards:
            media_path = media_dir / card.screenshot_filename
            if media_path.exists():
                media_files.append(str(media_path))

        output_path.parent.mkdir(parents=True, exist_ok=True)

        package = genanki.Package(deck_builder.deck)
        package.media_files = media_files
        package.write_to_file(str(output_path))

        return output_path
