"""Image input validation and loading."""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from io import BytesIO
from urllib.parse import urlparse

import httpx
from PIL import Image, UnidentifiedImageError

MAX_IMAGE_BYTES = 10 * 1024 * 1024
HTTP_TIMEOUT_SECONDS = 10.0
SUPPORTED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/tiff",
    "image/bmp",
}
SUPPORTED_PIL_FORMATS = {"JPEG", "PNG", "WEBP", "TIFF", "BMP"}


class ImageInputError(ValueError):
    """Raised when image input is invalid or unsafe to process."""


@dataclass(frozen=True)
class LoadedImage:
    """Validated image bytes ready for OCR processing."""

    data: bytes
    suffix: str


def load_image(
    *,
    image_url: str | None,
    image_base64: str | None,
    http_client: httpx.Client | None = None,
) -> LoadedImage:
    """Load one image from URL or base64, validating size and format."""
    if bool(image_url) == bool(image_base64):
        raise ImageInputError("Provide exactly one of image_url or image_base64.")

    if image_url:
        data, content_type = _download_image(image_url, http_client=http_client)
        return _validate_image_bytes(data, content_type=content_type)

    assert image_base64 is not None
    data = _decode_base64_image(image_base64)
    return _validate_image_bytes(data, content_type=None)


def _download_image(
    image_url: str,
    *,
    http_client: httpx.Client | None,
) -> tuple[bytes, str]:
    parsed = urlparse(image_url)
    if parsed.scheme not in {"http", "https"}:
        raise ImageInputError("image_url must use http or https.")

    close_client = http_client is None
    client = http_client or httpx.Client(timeout=HTTP_TIMEOUT_SECONDS, follow_redirects=True)

    try:
        with client.stream("GET", image_url) as response:
            response.raise_for_status()
            content_type = _base_content_type(response.headers.get("content-type", ""))
            if content_type not in SUPPORTED_CONTENT_TYPES:
                raise ImageInputError("Unsupported image content type.")

            content_length = response.headers.get("content-length")
            if content_length is not None and int(content_length) > MAX_IMAGE_BYTES:
                raise ImageInputError("Image exceeds maximum size.")

            chunks: list[bytes] = []
            total = 0
            for chunk in response.iter_bytes():
                total += len(chunk)
                if total > MAX_IMAGE_BYTES:
                    raise ImageInputError("Image exceeds maximum size.")
                chunks.append(chunk)
            return b"".join(chunks), content_type
    except httpx.TimeoutException as exc:
        raise ImageInputError("Image download timed out.") from exc
    except httpx.HTTPError as exc:
        raise ImageInputError("Image download failed.") from exc
    finally:
        if close_client:
            client.close()


def _decode_base64_image(image_base64: str) -> bytes:
    payload = image_base64.strip()
    if "," in payload and payload.lower().startswith("data:"):
        payload = payload.split(",", 1)[1]

    try:
        data = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ImageInputError("Invalid base64 image payload.") from exc

    if len(data) > MAX_IMAGE_BYTES:
        raise ImageInputError("Image exceeds maximum size.")

    return data


def _validate_image_bytes(data: bytes, *, content_type: str | None) -> LoadedImage:
    if not data:
        raise ImageInputError("Image payload is empty.")

    try:
        with Image.open(BytesIO(data)) as image:
            image.verify()
            image_format = image.format
    except (UnidentifiedImageError, OSError) as exc:
        raise ImageInputError("Unsupported or invalid image format.") from exc

    if image_format not in SUPPORTED_PIL_FORMATS:
        raise ImageInputError("Unsupported image format.")

    if content_type is not None and content_type not in SUPPORTED_CONTENT_TYPES:
        raise ImageInputError("Unsupported image content type.")

    return LoadedImage(data=data, suffix=_suffix_for_format(image_format))


def _base_content_type(value: str) -> str:
    return value.split(";", 1)[0].strip().lower()


def _suffix_for_format(image_format: str) -> str:
    return {
        "JPEG": ".jpg",
        "PNG": ".png",
        "WEBP": ".webp",
        "TIFF": ".tiff",
        "BMP": ".bmp",
    }[image_format]
