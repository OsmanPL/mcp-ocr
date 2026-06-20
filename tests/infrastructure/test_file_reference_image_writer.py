"""Tests for ChatGPT file reference image writing."""

from pathlib import Path

import pytest

from box_ocr_mcp.infrastructure.image import (
    FileReferenceImageError,
    FileReferenceImageWriter,
)


def test_file_reference_image_writer_writes_file_url_to_temp_file(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "uploaded.png"
    source_path.write_bytes(b"uploaded image bytes")
    writer = FileReferenceImageWriter()

    image_path = writer.write_to_temp_file(
        {
            "download_url": source_path.as_uri(),
            "file_id": "file_test",
            "mime_type": "image/png",
            "file_name": "uploaded.png",
        }
    )

    try:
        assert Path(image_path).exists()
        assert Path(image_path).read_bytes() == b"uploaded image bytes"
    finally:
        Path(image_path).unlink(missing_ok=True)


def test_file_reference_image_writer_requires_download_url() -> None:
    writer = FileReferenceImageWriter()

    with pytest.raises(
        FileReferenceImageError,
        match="image_file.download_url is required.",
    ):
        writer.write_to_temp_file({"file_id": "file_test"})
