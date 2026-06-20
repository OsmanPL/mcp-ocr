"""Domain entities for OCR results."""

from dataclasses import dataclass


@dataclass(frozen=True)
class OcrResult:
    """Raw OCR output produced from an image."""

    raw_text: str
    lines: list[str]
    average_confidence: float
