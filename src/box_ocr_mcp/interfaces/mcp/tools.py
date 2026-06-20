"""MCP tool registration."""

from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from box_ocr_mcp.application import ExtractTextFromBoxImageUseCase
from box_ocr_mcp.infrastructure.image import (
    Base64ImageError,
    Base64ImageWriter,
    FileReferenceImageError,
    FileReferenceImageWriter,
)


def _error_response(message: str) -> dict[str, Any]:
    return {
        "error": message,
        "raw_text": "",
        "lines": [],
        "average_confidence": 0,
    }


def _validate_image_path(image_path: str) -> str | None:
    if not image_path:
        return "image_path is required."

    path = Path(image_path)
    if not path.exists():
        return "Image path does not exist."

    if not path.is_file():
        return "Image path must point to a file."

    return None


def register_tools(
    server: FastMCP,
    use_case: ExtractTextFromBoxImageUseCase,
    base64_image_writer: Base64ImageWriter,
    file_reference_image_writer: FileReferenceImageWriter,
) -> None:
    """Register MCP tools on the provided server."""

    @server.tool(
        name="image_box_ocr",
        description="Run OCR on a local cardboard box image and return raw text.",
    )
    def image_box_ocr(image_path: str) -> dict[str, Any]:
        """Run OCR on a local image path and return raw detected text only."""
        validation_error = _validate_image_path(image_path)
        if validation_error is not None:
            return _error_response(validation_error)

        try:
            result = use_case.execute(image_path)
        except OSError:
            return _error_response("Image processing failed.")
        except RuntimeError:
            return _error_response("OCR processing failed.")
        except Exception:
            return _error_response("Unexpected OCR processing error.")
        else:
            return {
                "raw_text": result.raw_text,
                "lines": result.lines,
                "average_confidence": result.average_confidence,
            }

    @server.tool(
        name="image_box_ocr_base64",
        description="Run OCR on a base64-encoded cardboard box image.",
    )
    def image_box_ocr_base64(image_base64: str) -> dict[str, Any]:
        """Run OCR on a base64 image payload and return raw detected text only."""
        try:
            image_path = base64_image_writer.write_to_temp_file(image_base64)
            result = use_case.execute(image_path)
        except Base64ImageError as exc:
            return _error_response(str(exc))
        except OSError:
            return _error_response("Image processing failed.")
        except RuntimeError:
            return _error_response("OCR processing failed.")
        except Exception:
            return _error_response("Unexpected OCR processing error.")
        else:
            return {
                "raw_text": result.raw_text,
                "lines": result.lines,
                "average_confidence": result.average_confidence,
            }

    @server.tool(
        name="image_box_ocr_file",
        description="Run OCR on an image uploaded in ChatGPT.",
        meta={"openai/fileParams": ["image_file"]},
    )
    def image_box_ocr_file(image_file: dict[str, Any]) -> dict[str, Any]:
        """Run OCR on a ChatGPT file reference and return raw detected text only."""
        try:
            image_path = file_reference_image_writer.write_to_temp_file(image_file)
            result = use_case.execute(image_path)
        except FileReferenceImageError as exc:
            return _error_response(str(exc))
        except OSError:
            return _error_response("Image processing failed.")
        except RuntimeError:
            return _error_response("OCR processing failed.")
        except Exception:
            return _error_response("Unexpected OCR processing error.")
        else:
            return {
                "raw_text": result.raw_text,
                "lines": result.lines,
                "average_confidence": result.average_confidence,
            }
