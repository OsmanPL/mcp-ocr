"""Pillow-based image preprocessing."""

from PIL import Image, ImageEnhance

from box_ocr_mcp.infrastructure.filesystem import TempFileManager


class PillowImagePreprocessor:
    """Preprocess images to improve OCR readability."""

    def __init__(
        self,
        temp_file_manager: TempFileManager | None = None,
        contrast_factor: float = 1.5,
        sharpness_factor: float = 1.5,
    ) -> None:
        self._temp_file_manager = temp_file_manager or TempFileManager()
        self._contrast_factor = contrast_factor
        self._sharpness_factor = sharpness_factor

    def preprocess(self, image_path: str) -> str:
        """Convert an image to grayscale, enhance it, and save a temp copy."""
        processed_path = self._temp_file_manager.create_temp_path(suffix=".png")

        with Image.open(image_path) as image:
            processed_image = image.convert("L")
            processed_image = ImageEnhance.Contrast(processed_image).enhance(
                self._contrast_factor
            )
            processed_image = ImageEnhance.Sharpness(processed_image).enhance(
                self._sharpness_factor
            )
            processed_image.save(processed_path)

        return processed_path
