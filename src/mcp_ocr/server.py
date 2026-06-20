"""FastMCP server entrypoint for OCR."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from mcp_ocr.extraction import extract_visible_key_values
from mcp_ocr.image_loader import load_image
from mcp_ocr.ocr import PaddleOcrEngine
from mcp_ocr.schemas import OcrImageResult

mcp = FastMCP(name="mcp-ocr")
_ocr_engine = PaddleOcrEngine()


@mcp.tool(
    name="ocr_image",
    description=(
        "Receive an image file, image URL, or Base64 image, perform OCR, and "
        "return literal extracted text as JSON."
    ),
    meta={"openai/fileParams": ["image_file"]},
)
def ocr_image(
    image_file: dict[str, Any] | str | None = None,
    image_url: str | None = None,
    image_base64: str | None = None,
) -> dict[str, object]:
    """Run OCR on an image file, image URL, or base64 image."""
    image = load_image(
        image_file=image_file,
        image_url=image_url,
        image_base64=image_base64,
    )
    ocr_text = _ocr_engine.extract_text(image.data, image.suffix)
    result = OcrImageResult(
        raw=ocr_text.raw,
        valores=extract_visible_key_values(ocr_text.raw),
        porcentaje_confianza=ocr_text.confidence,
    )
    return result.model_dump()


def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
