"""Tests for the extract text use case."""

from box_ocr_mcp.application import ExtractTextFromBoxImageUseCase
from box_ocr_mcp.domain import OcrResult


class RecordingPreprocessor:
    """Test preprocessor that records received paths."""

    def __init__(self, processed_path: str = "processed.png") -> None:
        self.processed_path = processed_path
        self.calls: list[str] = []

    def preprocess(self, image_path: str) -> str:
        self.calls.append(image_path)
        return self.processed_path


class RecordingOcrEngine:
    """Test OCR engine that records received paths."""

    def __init__(self, result: OcrResult) -> None:
        self.result = result
        self.calls: list[str] = []

    def extract_text(self, image_path: str) -> OcrResult:
        self.calls.append(image_path)
        return self.result


def test_use_case_calls_preprocessor_and_ocr_engine() -> None:
    expected_result = OcrResult(
        raw_text="LOTE A12345\nVENCE 15/08/2026",
        lines=["LOTE A12345", "VENCE 15/08/2026"],
        average_confidence=0.91,
    )
    preprocessor = RecordingPreprocessor(processed_path="processed-image.png")
    ocr_engine = RecordingOcrEngine(result=expected_result)
    use_case = ExtractTextFromBoxImageUseCase(
        preprocessor=preprocessor,
        ocr_engine=ocr_engine,
    )

    result = use_case.execute("source-image.png")

    assert preprocessor.calls == ["source-image.png"]
    assert ocr_engine.calls == ["processed-image.png"]
    assert result == expected_result


def test_use_case_returns_raw_ocr_text_without_modification() -> None:
    raw_text = "B4TCH A12345\nEXP 15/O8/2026"
    expected_result = OcrResult(
        raw_text=raw_text,
        lines=["B4TCH A12345", "EXP 15/O8/2026"],
        average_confidence=0.5,
    )
    use_case = ExtractTextFromBoxImageUseCase(
        preprocessor=RecordingPreprocessor(),
        ocr_engine=RecordingOcrEngine(result=expected_result),
    )

    result = use_case.execute("source-image.png")

    assert result.raw_text == raw_text
