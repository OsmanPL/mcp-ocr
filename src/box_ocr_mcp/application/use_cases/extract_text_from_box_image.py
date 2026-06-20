"""Use case for extracting OCR text from a box image."""

from box_ocr_mcp.domain.entities import OcrResult
from box_ocr_mcp.domain.ports import ImagePreprocessorPort, OcrEnginePort


class ExtractTextFromBoxImageUseCase:
    """Coordinate image preprocessing and OCR extraction."""

    def __init__(
        self,
        preprocessor: ImagePreprocessorPort,
        ocr_engine: OcrEnginePort,
    ) -> None:
        self._preprocessor = preprocessor
        self._ocr_engine = ocr_engine

    def execute(self, image_path: str) -> OcrResult:
        """Extract raw OCR text from an image path."""
        processed_path = self._preprocessor.preprocess(image_path)
        return self._ocr_engine.extract_text(processed_path)
