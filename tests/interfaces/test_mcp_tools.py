"""Tests for MCP tool behavior."""

import asyncio
import base64
from pathlib import Path

from box_ocr_mcp.application import ExtractTextFromBoxImageUseCase
from box_ocr_mcp.domain import OcrResult
from box_ocr_mcp.interfaces.mcp.server import create_mcp_server


class PassPreprocessor:
    """Preprocessor that returns the original image path."""

    def preprocess(self, image_path: str) -> str:
        return image_path


class FailingPreprocessor:
    """Preprocessor that simulates image processing failure."""

    def preprocess(self, image_path: str) -> str:
        raise OSError("raw pillow failure")


class FakeOcrEngine:
    """OCR engine that returns a fixed result."""

    def extract_text(self, image_path: str) -> OcrResult:
        return OcrResult(
            raw_text="LOTE A12345",
            lines=["LOTE A12345"],
            average_confidence=0.9,
        )


def call_image_box_ocr(
    use_case: ExtractTextFromBoxImageUseCase,
    image_path: str,
) -> dict[str, object]:
    async def call_tool() -> dict[str, object]:
        server = create_mcp_server(use_case=use_case)
        _content, structured = await server.call_tool(
            "image_box_ocr",
            {"image_path": image_path},
        )
        assert isinstance(structured, dict)
        return structured

    return asyncio.run(call_tool())


def call_image_box_ocr_base64(
    use_case: ExtractTextFromBoxImageUseCase,
    image_base64: str,
) -> dict[str, object]:
    async def call_tool() -> dict[str, object]:
        server = create_mcp_server(use_case=use_case)
        _content, structured = await server.call_tool(
            "image_box_ocr_base64",
            {"image_base64": image_base64},
        )
        assert isinstance(structured, dict)
        return structured

    return asyncio.run(call_tool())


def test_mcp_tool_returns_success_payload(tmp_path: Path) -> None:
    image_path = tmp_path / "box.png"
    image_path.write_bytes(b"fake image bytes")
    use_case = ExtractTextFromBoxImageUseCase(PassPreprocessor(), FakeOcrEngine())

    result = call_image_box_ocr(use_case, str(image_path))

    assert result == {
        "raw_text": "LOTE A12345",
        "lines": ["LOTE A12345"],
        "average_confidence": 0.9,
    }


def test_mcp_tool_returns_controlled_error_when_image_processing_fails(
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "box.png"
    image_path.write_bytes(b"fake image bytes")
    use_case = ExtractTextFromBoxImageUseCase(FailingPreprocessor(), FakeOcrEngine())

    result = call_image_box_ocr(use_case, str(image_path))

    assert result == {
        "error": "Image processing failed.",
        "raw_text": "",
        "lines": [],
        "average_confidence": 0,
    }


def test_mcp_tool_returns_controlled_error_when_image_path_is_missing() -> None:
    use_case = ExtractTextFromBoxImageUseCase(PassPreprocessor(), FakeOcrEngine())

    result = call_image_box_ocr(use_case, "/missing/box.png")

    assert result == {
        "error": "Image path does not exist.",
        "raw_text": "",
        "lines": [],
        "average_confidence": 0,
    }


def test_mcp_base64_tool_returns_success_payload() -> None:
    use_case = ExtractTextFromBoxImageUseCase(PassPreprocessor(), FakeOcrEngine())
    image_base64 = base64.b64encode(b"fake image bytes").decode()

    result = call_image_box_ocr_base64(use_case, image_base64)

    assert result == {
        "raw_text": "LOTE A12345",
        "lines": ["LOTE A12345"],
        "average_confidence": 0.9,
    }


def test_mcp_base64_tool_returns_controlled_error_for_invalid_base64() -> None:
    use_case = ExtractTextFromBoxImageUseCase(PassPreprocessor(), FakeOcrEngine())

    result = call_image_box_ocr_base64(use_case, "not base64")

    assert result == {
        "error": "Invalid base64 image payload.",
        "raw_text": "",
        "lines": [],
        "average_confidence": 0,
    }


def test_mcp_base64_tool_returns_controlled_error_when_image_processing_fails() -> None:
    use_case = ExtractTextFromBoxImageUseCase(FailingPreprocessor(), FakeOcrEngine())
    image_base64 = base64.b64encode(b"fake image bytes").decode()

    result = call_image_box_ocr_base64(use_case, image_base64)

    assert result == {
        "error": "Image processing failed.",
        "raw_text": "",
        "lines": [],
        "average_confidence": 0,
    }
