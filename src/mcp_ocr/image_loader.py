"""Image input validation and loading."""

from __future__ import annotations

import base64
import binascii
import re
from collections.abc import Mapping
from dataclasses import dataclass
from io import BytesIO
from typing import Any
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
DATA_URI_PATTERN = re.compile(r"^data:[^,]*;base64,", re.IGNORECASE)


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
    image_file: Mapping[str, Any] | str | None = None,
    http_client: httpx.Client | None = None,
) -> LoadedImage:
    """Load one image from URL, base64, or a client-provided file object."""
    provided_count = sum(value is not None for value in (image_url, image_base64, image_file))
    if provided_count != 1:
        raise ImageInputError("Provide exactly one of image_url, image_base64, or image_file.")

    if image_url:
        data, content_type = _download_image(image_url, http_client=http_client)
        return _validate_image_bytes(data, content_type=content_type)

    if image_file is not None:
        return _load_image_file(image_file, http_client=http_client)

    assert image_base64 is not None
    data = _decode_base64_image(image_base64)
    return _validate_image_bytes(data, content_type=None)


def _load_image_file(
    image_file: Mapping[str, Any] | str,
    *,
    http_client: httpx.Client | None,
) -> LoadedImage:
    """Load common MCP/client file payload shapes through the same validation path."""
    if isinstance(image_file, str):
        if image_file.startswith(("http://", "https://")):
            data, content_type = _download_image(image_file, http_client=http_client)
            return _validate_image_bytes(data, content_type=content_type)
        data = _decode_base64_image(image_file)
        return _validate_image_bytes(data, content_type=None)

    url = _first_string_value(
        image_file,
        "download_url",
        "url",
        "uri",
        "href",
    )
    if url is not None:
        data, content_type = _download_image(url, http_client=http_client)
        return _validate_image_bytes(data, content_type=content_type)

    payload = _first_string_value(
        image_file,
        "image_base64",
        "base64",
        "data",
        "content",
    )
    if payload is not None:
        data = _decode_base64_image(payload)
        return _validate_image_bytes(data, content_type=None)

    raise ImageInputError(
        "image_file must include a download_url, url, uri, or base64 image payload."
    )


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
    payload = _clean_base64_payload(image_base64)
    if payload.startswith(("http://", "https://")):
        raise ImageInputError("Use image_url for URL inputs, not image_base64.")

    if DATA_URI_PATTERN.match(payload):
        payload = payload.split(",", 1)[1]

    try:
        data = _decode_base64_payload(payload)
    except (binascii.Error, ValueError) as exc:
        raise ImageInputError("Invalid base64 image payload.") from exc

    if len(data) > MAX_IMAGE_BYTES:
        raise ImageInputError("Image exceeds maximum size.")

    return data


def _clean_base64_payload(image_base64: str) -> str:
    return "".join(image_base64.strip().split())


def _decode_base64_payload(payload: str) -> bytes:
    padded_payload = _with_base64_padding(payload)
    try:
        return base64.b64decode(padded_payload, validate=True)
    except binascii.Error:
        urlsafe_payload = padded_payload.replace("-", "+").replace("_", "/")
        return base64.b64decode(urlsafe_payload, validate=True)


def _with_base64_padding(payload: str) -> str:
    missing_padding = len(payload) % 4
    if missing_padding:
        payload = f"{payload}{'=' * (4 - missing_padding)}"
    return payload


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


def _first_string_value(value: Mapping[str, Any], *keys: str) -> str | None:
    for key in keys:
        candidate = value.get(key)
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return None


def _suffix_for_format(image_format: str) -> str:
    return {
        "JPEG": ".jpg",
        "PNG": ".png",
        "WEBP": ".webp",
        "TIFF": ".tiff",
        "BMP": ".bmp",
    }[image_format]
