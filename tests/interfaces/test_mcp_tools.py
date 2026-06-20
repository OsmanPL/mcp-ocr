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


class FakeFileReferenceImageWriter:
    """File reference writer that returns a fixed image path."""

    def __init__(self, image_path: str = "uploaded-image.png") -> None:
        self.image_path = image_path
        self.calls: list[dict[str, object]] = []

    def write_to_temp_file(self, image_file: dict[str, object]) -> str:
        self.calls.append(image_file)
        return self.image_path


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


def call_image_box_ocr_file(
    use_case: ExtractTextFromBoxImageUseCase,
    image_file: dict[str, object],
    file_reference_image_writer: FakeFileReferenceImageWriter | None = None,
) -> dict[str, object]:
    async def call_tool() -> dict[str, object]:
        server = create_mcp_server(
            use_case=use_case,
            file_reference_image_writer=(
                file_reference_image_writer or FakeFileReferenceImageWriter()
            ),
        )
        _content, structured = await server.call_tool(
            "image_box_ocr_file",
            {"image_file": image_file},
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


def test_mcp_file_tool_returns_success_payload() -> None:
    use_case = ExtractTextFromBoxImageUseCase(PassPreprocessor(), FakeOcrEngine())
    writer = FakeFileReferenceImageWriter(image_path="uploaded-image.png")
    image_file: dict[str, object] = {
        "download_url": "file:///tmp/uploaded.png",
        "file_id": "file_test",
        "mime_type": "image/png",
        "file_name": "uploaded.png",
    }

    result = call_image_box_ocr_file(
        use_case=use_case,
        image_file=image_file,
        file_reference_image_writer=writer,
    )

    assert writer.calls == [image_file]
    assert result == {
        "raw_text": "LOTE A12345",
        "lines": ["LOTE A12345"],
        "average_confidence": 0.9,
    }


def test_mcp_file_tool_returns_controlled_error_when_image_processing_fails() -> None:
    use_case = ExtractTextFromBoxImageUseCase(FailingPreprocessor(), FakeOcrEngine())

    result = call_image_box_ocr_file(
        use_case=use_case,
        image_file={
            "download_url": "file:///tmp/uploaded.png",
            "file_id": "file_test",
        },
    )

    assert result == {
        "error": "Image processing failed.",
        "raw_text": "",
        "lines": [],
        "average_confidence": 0,
    }


def test_mcp_file_tool_declares_openai_file_params() -> None:
    async def get_file_tool_meta() -> dict[str, object]:
        server = create_mcp_server(
            use_case=ExtractTextFromBoxImageUseCase(
                PassPreprocessor(),
                FakeOcrEngine(),
            ),
            file_reference_image_writer=FakeFileReferenceImageWriter(),
        )
        tools = await server.list_tools()
        file_tool = next(tool for tool in tools if tool.name == "image_box_ocr_file")
        assert file_tool.meta is not None
        return dict(file_tool.meta)

    meta = asyncio.run(get_file_tool_meta())

    assert meta["openai/fileParams"] == ["image_file"]
