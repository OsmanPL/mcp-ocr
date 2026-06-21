from __future__ import annotations

import sys
import types
from typing import Any

from mcp_ocr.ocr import PaddleOcrEngine


class FakePredictEngine:
    def __init__(self, payload: Any) -> None:
        self.payload = payload
        self.calls: list[str] = []

    def predict(self, image_path: str) -> Any:
        self.calls.append(image_path)
        return self.payload


def test_ocr_engine_converts_scores_to_percentage() -> None:
    fake = FakePredictEngine(
        [{"rec_texts": ["LOTE", "ABC123"], "rec_scores": [0.9, 1.0]}]
    )
    engine = PaddleOcrEngine(ocr_engine=fake)

    result = engine.extract_text(b"fake image bytes", ".png")

    assert fake.calls
    assert result.raw == "LOTE\nABC123"
    assert result.confidence == 95.0


def test_ocr_engine_returns_null_confidence_without_scores() -> None:
    engine = PaddleOcrEngine(ocr_engine=FakePredictEngine([{"rec_texts": ["LOTE"]}]))

    result = engine.extract_text(b"fake image bytes", ".png")

    assert result.raw == "LOTE"
    assert result.confidence is None


def test_ocr_engine_supports_legacy_nested_sequence_payload() -> None:
    payload = [[[[0, 0], [1, 0], [1, 1], [0, 1]], ["VENC 20/10/2026", 0.88]]]
    engine = PaddleOcrEngine(ocr_engine=FakePredictEngine(payload))

    result = engine.extract_text(b"fake image bytes", ".png")

    assert result.raw == "VENC 20/10/2026"
    assert result.confidence == 88.0


def test_ocr_engine_defaults_to_valid_latin_language_model(monkeypatch) -> None:
    calls: list[dict[str, Any]] = []

    class FakePaddleOCR:
        def __init__(self, **kwargs: Any) -> None:
            calls.append(kwargs)

        def predict(self, _image_path: str) -> list[dict[str, list[object]]]:
            return [{"rec_texts": ["LOTE"], "rec_scores": [0.9]}]

    fake_module = types.SimpleNamespace(PaddleOCR=FakePaddleOCR)
    monkeypatch.setitem(sys.modules, "paddleocr", fake_module)

    engine = PaddleOcrEngine()
    result = engine.extract_text(b"fake image bytes", ".png")

    assert result.raw == "LOTE"
    assert calls == [
        {
            "lang": "es",
            "ocr_version": "PP-OCRv5",
            "use_textline_orientation": True,
        }
    ]
