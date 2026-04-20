"""Tests for OCR engine wrapper."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.extractor.exceptions import OCREngineError
from src.extractor.models import LearningLanguage
from src.extractor.ocr_engine import OCREngine


class TestOCREngineInit:
    """T016: Tests for OCREngine initialization."""

    def test_init_with_japanese(self):
        with patch("src.extractor.ocr_engine.OCREngine._init_backend"):
            engine = OCREngine(LearningLanguage.JAPANESE)
            assert engine.language == LearningLanguage.JAPANESE

    def test_init_with_english(self):
        with patch("src.extractor.ocr_engine.OCREngine._init_backend"):
            engine = OCREngine(LearningLanguage.ENGLISH)
            assert engine.language == LearningLanguage.ENGLISH

    def test_init_with_chinese_simplified(self):
        with patch("src.extractor.ocr_engine.OCREngine._init_backend"):
            engine = OCREngine(LearningLanguage.CHINESE_SIMPLIFIED)
            assert engine.language == LearningLanguage.CHINESE_SIMPLIFIED

    def test_raises_ocr_engine_error_on_backend_failure(self):
        with patch(
            "src.extractor.ocr_engine.OCREngine._init_backend",
            side_effect=OCREngineError("Backend init failed"),
        ), pytest.raises(OCREngineError):
            OCREngine(LearningLanguage.JAPANESE)


class TestOCREngineExtractText:
    """T016: Tests for OCREngine.extract_text() with mocked backends."""

    def test_returns_ocr_results(self, tmp_path):
        frame = tmp_path / "frame.png"
        # Create a minimal image
        from PIL import Image
        Image.new("RGB", (100, 100)).save(frame)

        with patch("src.extractor.ocr_engine.OCREngine._init_backend"):
            engine = OCREngine(LearningLanguage.JAPANESE)

        with patch.object(engine, "_run_ocr") as mock_ocr:
            mock_ocr.return_value = [
                {"text": "hello", "confidence": 0.95, "bbox": (10, 20, 100, 30)},
            ]
            results = engine.extract_text(frame)

        assert len(results) == 1
        assert results[0].text == "hello"
        assert results[0].confidence == 0.95

    def test_returns_empty_for_no_text(self, tmp_path):
        frame = tmp_path / "frame.png"
        from PIL import Image
        Image.new("RGB", (100, 100)).save(frame)

        with patch("src.extractor.ocr_engine.OCREngine._init_backend"):
            engine = OCREngine(LearningLanguage.ENGLISH)

        with patch.object(engine, "_run_ocr", return_value=[]):
            results = engine.extract_text(frame)

        assert results == []

    def test_results_ordered_top_to_bottom(self, tmp_path):
        frame = tmp_path / "frame.png"
        from PIL import Image
        Image.new("RGB", (100, 100)).save(frame)

        with patch("src.extractor.ocr_engine.OCREngine._init_backend"):
            engine = OCREngine(LearningLanguage.JAPANESE)

        with patch.object(engine, "_run_ocr") as mock_ocr:
            mock_ocr.return_value = [
                {"text": "bottom", "confidence": 0.9, "bbox": (10, 100, 100, 30)},
                {"text": "top", "confidence": 0.9, "bbox": (10, 10, 100, 30)},
            ]
            results = engine.extract_text(frame)

        assert results[0].text == "top"
        assert results[1].text == "bottom"

    def test_raises_on_engine_failure(self, tmp_path):
        frame = tmp_path / "frame.png"
        from PIL import Image
        Image.new("RGB", (100, 100)).save(frame)

        with patch("src.extractor.ocr_engine.OCREngine._init_backend"):
            engine = OCREngine(LearningLanguage.JAPANESE)

        with (
            patch.object(engine, "_run_ocr", side_effect=OCREngineError("OCR failed")),
            pytest.raises(OCREngineError),
        ):
            engine.extract_text(frame)
