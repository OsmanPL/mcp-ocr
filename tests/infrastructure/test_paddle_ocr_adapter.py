"""Tests for the PaddleOCR adapter."""

from typing import Any

from box_ocr_mcp.infrastructure.ocr import PaddleOcrAdapter


class FakeOcrEngine:
    """Fake OCR engine that returns predefined PaddleOCR-like payloads."""

    def __init__(self, payload: Any) -> None:
        self.payload = payload
        self.calls: list[str] = []

    def predict(self, image_path: str) -> Any:
        self.calls.append(image_path)
        return self.payload


def test_adapter_returns_detected_lines_from_mapping_payload() -> None:
    fake_engine = FakeOcrEngine(
        [
            {
                "rec_texts": ["LOTE A12345", "VENCE 15/08/2026"],
                "rec_scores": [0.8, 1.0],
            }
        ]
    )
    adapter = PaddleOcrAdapter(ocr_engine=fake_engine)

    result = adapter.extract_text("processed.png")

    assert fake_engine.calls == ["processed.png"]
    assert result.lines == ["LOTE A12345", "VENCE 15/08/2026"]
    assert result.raw_text == "LOTE A12345\nVENCE 15/08/2026"


def test_adapter_calculates_average_confidence() -> None:
    adapter = PaddleOcrAdapter(
        ocr_engine=FakeOcrEngine(
            [{"rec_texts": ["A", "B", "C"], "rec_scores": [0.6, 0.9, 0.75]}]
        )
    )

    result = adapter.extract_text("processed.png")

    assert result.average_confidence == 0.75


def test_adapter_returns_zero_confidence_when_scores_are_missing() -> None:
    adapter = PaddleOcrAdapter(ocr_engine=FakeOcrEngine([{"rec_texts": ["A"]}]))

    result = adapter.extract_text("processed.png")

    assert result.lines == ["A"]
    assert result.average_confidence == 0


def test_adapter_supports_legacy_nested_sequence_payload() -> None:
    adapter = PaddleOcrAdapter(
        ocr_engine=FakeOcrEngine(
            [[[[0, 0], [1, 0], [1, 1], [0, 1]], ["BATCH A12345", 0.88]]]
        )
    )

    result = adapter.extract_text("processed.png")

    assert result.lines == ["BATCH A12345"]
    assert result.average_confidence == 0.88
