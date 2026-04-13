"""Display enumeration — maps Qt QScreen objects to Display models."""

from __future__ import annotations

from PyQt6.QtWidgets import QApplication

from src.recorder.models import Display


class DisplayEnumerator:
    """Enumerates connected monitors using Qt's screen list.

    The list reflects the physical state at the time of the call; callers
    should re-enumerate after QApplication.screenAdded / screenRemoved events.
    """

    def list_displays(self) -> list[Display]:
        """Return all currently connected displays.

        Always returns at least one element (the primary display).
        """
        app = QApplication.instance()
        if app is None:
            raise RuntimeError("QApplication must be created before enumerating displays")

        primary_screen = app.primaryScreen()
        displays: list[Display] = []

        for i, screen in enumerate(app.screens(), start=1):
            geo = screen.geometry()
            is_primary = screen is primary_screen
            label_suffix = " — Primary" if is_primary else ""
            label = f"Display {i}{label_suffix}"

            displays.append(
                Display(
                    id=screen.name(),
                    label=label,
                    width=geo.width(),
                    height=geo.height(),
                    x=geo.x(),
                    y=geo.y(),
                    is_primary=is_primary,
                    scale_factor=screen.devicePixelRatio(),
                )
            )

        return displays
