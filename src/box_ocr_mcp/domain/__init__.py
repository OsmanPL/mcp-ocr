"""Domain layer for OCR concepts and ports."""

from box_ocr_mcp.domain.entities import OcrResult
from box_ocr_mcp.domain.ports import ImagePreprocessorPort, OcrEnginePort

__all__ = ["ImagePreprocessorPort", "OcrEnginePort", "OcrResult"]
