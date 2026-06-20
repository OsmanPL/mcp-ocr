"""Ports used by the application layer."""

from typing import Protocol

from box_ocr_mcp.domain.entities import OcrResult


class OcrEnginePort(Protocol):
    """Abstraction for OCR engines."""

    def extract_text(self, image_path: str) -> OcrResult:
        """Extract raw OCR text from an image path."""
        ...


class ImagePreprocessorPort(Protocol):
    """Abstraction for image preprocessing."""

    def preprocess(self, image_path: str) -> str:
        """Preprocess an image and return the processed image path."""
        ...
