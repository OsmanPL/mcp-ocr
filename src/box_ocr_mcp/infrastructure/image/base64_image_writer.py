"""Base64 image input handling."""

import base64
import binascii

from box_ocr_mcp.infrastructure.filesystem import TempFileManager


class Base64ImageError(ValueError):
    """Raised when a base64 image payload cannot be decoded or written."""


class Base64ImageWriter:
    """Decode base64 image payloads into temporary image files."""

    def __init__(
        self,
        temp_file_manager: TempFileManager | None = None,
        suffix: str = ".png",
    ) -> None:
        self._temp_file_manager = temp_file_manager or TempFileManager()
        self._suffix = suffix

    def write_to_temp_file(self, image_base64: str) -> str:
        """Decode base64 input, write it to a temp file, and return its path."""
        image_bytes = self._decode_base64(image_base64)
        image_path = self._temp_file_manager.create_temp_path(suffix=self._suffix)

        try:
            with open(image_path, "wb") as image_file:
                image_file.write(image_bytes)
        except OSError as exc:
            raise Base64ImageError("Failed to write decoded image.") from exc

        return image_path

    def _decode_base64(self, image_base64: str) -> bytes:
        if not image_base64:
            raise Base64ImageError("image_base64 is required.")

        payload = self._strip_data_url_prefix(image_base64.strip())

        try:
            return base64.b64decode(payload, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise Base64ImageError("Invalid base64 image payload.") from exc

    def _strip_data_url_prefix(self, image_base64: str) -> str:
        if image_base64.startswith("data:") and "," in image_base64:
            return image_base64.split(",", maxsplit=1)[1]
        return image_base64
