"""OCR engine wrapper for text detection in video frames."""

from __future__ import annotations

from pathlib import Path

from src.extractor.exceptions import OCREngineError
from src.extractor.models import LearningLanguage, OCRResult


class OCREngine:
    """Runs text detection on a single frame image.

    Wraps manga-ocr for Japanese and PaddleOCR for Chinese/English.
    """

    def __init__(self, language: LearningLanguage) -> None:
        self.language = language
        self._backend = None
        self._init_backend()

    def _init_backend(self) -> None:
        """Initialize the appropriate OCR backend for the language."""
        try:
            if self.language == LearningLanguage.JAPANESE:
                from manga_ocr import MangaOcr
                self._backend = MangaOcr()
                self._backend_type = "manga_ocr"
            else:
                from paddleocr import PaddleOCR
                lang_map = {
                    LearningLanguage.CHINESE_SIMPLIFIED: "ch",
                    LearningLanguage.CHINESE_TRADITIONAL: "chinese_cht",
                    LearningLanguage.ENGLISH: "en",
                }
                lang_code = lang_map[self.language]
                self._backend = PaddleOCR(use_angle_cls=True, lang=lang_code)
                self._backend_type = "paddleocr"
        except Exception as e:
            msg = f"Failed to initialize OCR backend for {self.language.value}: {e}"
            raise OCREngineError(msg) from e

    def extract_text(self, frame_path: Path) -> list[OCRResult]:
        """Extract text from a single frame image."""
        raw_results = self._run_ocr(frame_path)

        results = []
        for r in raw_results:
            results.append(
                OCRResult(
                    text=r["text"],
                    confidence=r["confidence"],
                    bounding_box=tuple(r["bbox"]),
                )
            )

        # Sort top-to-bottom, left-to-right by bounding box y then x
        results.sort(key=lambda r: (r.bounding_box[1], r.bounding_box[0]))
        return results

    def _run_ocr(self, frame_path: Path) -> list[dict]:
        """Run the OCR backend on a frame and return raw results."""
        try:
            if self._backend_type == "manga_ocr":
                text = self._backend(str(frame_path))
                if text and text.strip():
                    return [{"text": text.strip(), "confidence": 0.9, "bbox": (0, 0, 0, 0)}]
                return []
            else:
                result = self._backend.ocr(str(frame_path), cls=True)
                if not result or not result[0]:
                    return []
                entries = []
                for line in result[0]:
                    box_points = line[0]
                    text = line[1][0]
                    confidence = line[1][1]
                    x = int(min(p[0] for p in box_points))
                    y = int(min(p[1] for p in box_points))
                    w = int(max(p[0] for p in box_points)) - x
                    h = int(max(p[1] for p in box_points)) - y
                    entries.append({
                        "text": text,
                        "confidence": confidence,
                        "bbox": (x, y, w, h),
                    })
                return entries
        except OCREngineError:
            raise
        except Exception as e:
            msg = f"OCR processing failed: {e}"
            raise OCREngineError(msg) from e
