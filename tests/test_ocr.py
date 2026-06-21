from __future__ import annotations

from io import BytesIO
from typing import Any

from PIL import Image

from mcp_ocr.ocr import RapidOcrEngine


class FakePredictEngine:
    def __init__(self, payload: Any) -> None:
        self.payload = payload
        self.calls: list[str] = []

    def predict(self, image_path: str) -> Any:
        self.calls.append(image_path)
        return self.payload


class SequentialPredictEngine:
    def __init__(self, payloads: list[Any]) -> None:
        self.payloads = payloads
        self.calls: list[str] = []

    def predict(self, image_path: str) -> Any:
        self.calls.append(image_path)
        index = min(len(self.calls) - 1, len(self.payloads) - 1)
        return self.payloads[index]


def png_bytes() -> bytes:
    output = BytesIO()
    Image.new("RGB", (4, 4), "white").save(output, format="PNG")
    return output.getvalue()


def test_ocr_engine_converts_scores_to_percentage() -> None:
    fake = FakePredictEngine(
        [{"rec_texts": ["LOTE", "ABC123"], "rec_scores": [0.9, 1.0]}]
    )
    engine = RapidOcrEngine(ocr_engine=fake)

    result = engine.extract_text(png_bytes(), ".png")

    assert fake.calls
    assert result.raw == "LOTE\nABC123"
    assert result.confidence == 95.0


def test_ocr_engine_returns_null_confidence_without_scores() -> None:
    engine = RapidOcrEngine(ocr_engine=FakePredictEngine([{"rec_texts": ["LOTE"]}]))

    result = engine.extract_text(png_bytes(), ".png")

    assert result.raw == "LOTE"
    assert result.confidence is None


def test_ocr_engine_supports_legacy_nested_sequence_payload() -> None:
    payload = [[[[0, 0], [1, 0], [1, 1], [0, 1]], ["VENC 20/10/2026", 0.88]]]
    engine = RapidOcrEngine(ocr_engine=FakePredictEngine(payload))

    result = engine.extract_text(png_bytes(), ".png")

    assert result.raw == "VENC 20/10/2026"
    assert result.confidence == 88.0


def test_ocr_engine_supports_rapidocr_payload() -> None:
    payload = (
        [
            [[[0, 0], [1, 0], [1, 1], [0, 1]], "LOTE", 0.9],
            [[[0, 2], [1, 2], [1, 3], [0, 3]], "ABC123", 0.8],
        ],
        [0.1, 0.2, 0.3],
    )
    engine = RapidOcrEngine(ocr_engine=FakePredictEngine(payload))

    result = engine.extract_text(png_bytes(), ".png")

    assert result.raw == "LOTE\nABC123"
    assert result.confidence == 85.0


def test_ocr_engine_initializes_rapidocr_lazily(monkeypatch) -> None:
    calls: list[bool] = []

    class FakeRapidOCR:
        def __init__(self) -> None:
            calls.append(True)

        def __call__(self, _image_path: str, **_kwargs: Any) -> Any:
            return ([[[[0, 0], [1, 0], [1, 1], [0, 1]], "LOTE", 0.9]], [0.1])

    monkeypatch.setattr("rapidocr_onnxruntime.RapidOCR", FakeRapidOCR)

    engine = RapidOcrEngine()
    result = engine.extract_text(png_bytes(), ".png")

    assert result.raw == "LOTE"
    assert calls == [True]


def test_ocr_engine_chooses_highest_confidence_variant() -> None:
    engine = RapidOcrEngine(
        ocr_engine=SequentialPredictEngine(
            [
                [{"rec_texts": ["OTE"], "rec_scores": [0.6]}],
                [{"rec_texts": ["LOTE"], "rec_scores": [0.9]}],
            ]
        )
    )

    result = engine.extract_text(png_bytes(), ".png")

    assert result.raw == "LOTE"
    assert result.confidence == 90.0
