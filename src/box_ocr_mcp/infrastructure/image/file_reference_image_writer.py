"""ChatGPT file reference image input handling."""

from collections.abc import Mapping
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from box_ocr_mcp.infrastructure.filesystem import TempFileManager


class FileReferenceImageError(ValueError):
    """Raised when a file reference cannot be read or written."""


class FileReferenceImageWriter:
    """Write ChatGPT file references into temporary image files."""

    def __init__(
        self,
        temp_file_manager: TempFileManager | None = None,
        suffix: str = ".png",
        timeout_seconds: int = 30,
    ) -> None:
        self._temp_file_manager = temp_file_manager or TempFileManager()
        self._suffix = suffix
        self._timeout_seconds = timeout_seconds

    def write_to_temp_file(self, image_file: Mapping[str, Any]) -> str:
        """Read an authorized file reference and return a temporary image path."""
        download_url = image_file.get("download_url")
        if not isinstance(download_url, str) or not download_url:
            raise FileReferenceImageError("image_file.download_url is required.")

        image_bytes = self._read_file_reference(download_url)
        image_path = self._temp_file_manager.create_temp_path(suffix=self._suffix)

        try:
            with open(image_path, "wb") as image_output:
                image_output.write(image_bytes)
        except OSError as exc:
            raise FileReferenceImageError("Failed to write uploaded image.") from exc

        return image_path

    def _read_file_reference(self, download_url: str) -> bytes:
        request = Request(download_url, headers={"User-Agent": "box-ocr-mcp/0.1.0"})

        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                return response.read()
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise FileReferenceImageError("Failed to read uploaded image.") from exc
