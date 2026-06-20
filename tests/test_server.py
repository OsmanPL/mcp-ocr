from __future__ import annotations

import asyncio
import base64
from io import BytesIO

from PIL import Image

from mcp_ocr.ocr import OcrText
from mcp_ocr.server import mcp
import mcp_ocr.server as server_module


class FakeOcrEngine:
    def __init__(self) -> None:
        self.calls: list[tuple[bytes, str]] = []

    def extract_text(self, image_bytes: bytes, suffix: str) -> OcrText:
        self.calls.append((image_bytes, suffix))
        return OcrText(
            raw="LOTE\nABC123\nVENC: 20/10/2026",
            confidence=92.5,
        )


def png_base64() -> str:
    output = BytesIO()
    Image.new("RGB", (2, 2), color="white").save(output, format="PNG")
    return base64.b64encode(output.getvalue()).decode()


def call_ocr_image(arguments: dict[str, object]) -> dict[str, object]:
    async def call_tool() -> dict[str, object]:
        result = await mcp.call_tool("ocr_image", arguments)
        structured = result.structured_content
        assert isinstance(structured, dict)
        return structured

    return asyncio.run(call_tool())


def test_ocr_image_returns_exact_success_shape(
    monkeypatch,
) -> None:
    fake_engine = FakeOcrEngine()
    monkeypatch.setattr(server_module, "_ocr_engine", fake_engine)

    result = call_ocr_image({"image_base64": png_base64()})

    assert fake_engine.calls
    assert result == {
        "raw": "LOTE\nABC123\nVENC: 20/10/2026",
        "valores": {
            "LOTE": "ABC123",
            "VENC": "20/10/2026",
        },
        "porcentaje_confianza": 92.5,
    }


def test_only_ocr_image_tool_is_registered() -> None:
    async def list_tool_names() -> list[str]:
        tools = await mcp.list_tools()
        return [tool.name for tool in tools]

    assert asyncio.run(list_tool_names()) == ["ocr_image"]
