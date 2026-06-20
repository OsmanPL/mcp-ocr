"""Tests for base64 image writing."""

import base64
from pathlib import Path

import pytest

from box_ocr_mcp.infrastructure.image import Base64ImageError, Base64ImageWriter


def test_base64_image_writer_writes_valid_base64_to_temp_file() -> None:
    expected_bytes = b"fake image bytes"
    writer = Base64ImageWriter()

    image_path = writer.write_to_temp_file(base64.b64encode(expected_bytes).decode())

    try:
        assert Path(image_path).exists()
        assert Path(image_path).read_bytes() == expected_bytes
    finally:
        Path(image_path).unlink(missing_ok=True)


def test_base64_image_writer_accepts_data_url_prefix() -> None:
    expected_bytes = b"fake png bytes"
    payload = "data:image/png;base64," + base64.b64encode(expected_bytes).decode()
    writer = Base64ImageWriter()

    image_path = writer.write_to_temp_file(payload)

    try:
        assert Path(image_path).exists()
        assert Path(image_path).read_bytes() == expected_bytes
    finally:
        Path(image_path).unlink(missing_ok=True)


def test_base64_image_writer_rejects_invalid_base64() -> None:
    writer = Base64ImageWriter()

    with pytest.raises(Base64ImageError, match="Invalid base64 image payload."):
        writer.write_to_temp_file("not base64")
