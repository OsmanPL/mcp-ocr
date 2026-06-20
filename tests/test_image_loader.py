from __future__ import annotations

import base64
from io import BytesIO

import httpx
import pytest
from PIL import Image

from mcp_ocr import image_loader
from mcp_ocr.image_loader import ImageInputError, load_image


def png_bytes() -> bytes:
    output = BytesIO()
    Image.new("RGB", (2, 2), color="white").save(output, format="PNG")
    return output.getvalue()


def test_rejects_missing_image_input() -> None:
    with pytest.raises(ImageInputError, match="exactly one"):
        load_image(image_url=None, image_base64=None)


def test_rejects_both_image_inputs() -> None:
    with pytest.raises(ImageInputError, match="exactly one"):
        load_image(image_url="https://example.com/a.png", image_base64="abc")


def test_loads_base64_image_in_memory() -> None:
    encoded = base64.b64encode(png_bytes()).decode()

    loaded = load_image(image_url=None, image_base64=encoded)

    assert loaded.data.startswith(b"\x89PNG")
    assert loaded.suffix == ".png"


def test_loads_data_uri_base64_with_line_breaks() -> None:
    encoded = base64.b64encode(png_bytes()).decode()
    wrapped = "\n".join([encoded[:12], encoded[12:24], encoded[24:]])

    loaded = load_image(
        image_url=None,
        image_base64=f"data:image/png;base64,{wrapped}",
    )

    assert loaded.data.startswith(b"\x89PNG")
    assert loaded.suffix == ".png"


def test_loads_urlsafe_base64_without_padding() -> None:
    encoded = base64.urlsafe_b64encode(png_bytes()).decode().rstrip("=")

    loaded = load_image(image_url=None, image_base64=encoded)

    assert loaded.data.startswith(b"\x89PNG")
    assert loaded.suffix == ".png"


def test_rejects_url_passed_as_base64() -> None:
    with pytest.raises(ImageInputError, match="Use image_url"):
        load_image(image_url=None, image_base64="https://example.com/box.png")


def test_rejects_invalid_base64() -> None:
    with pytest.raises(ImageInputError, match="Invalid base64"):
        load_image(image_url=None, image_base64="not base64")


def test_rejects_oversized_base64(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(image_loader, "MAX_IMAGE_BYTES", 3)
    encoded = base64.b64encode(png_bytes()).decode()

    with pytest.raises(ImageInputError, match="maximum size"):
        load_image(image_url=None, image_base64=encoded)


def test_downloads_image_url_and_validates_content_type() -> None:
    transport = httpx.MockTransport(
        lambda _request: httpx.Response(
            200,
            headers={"content-type": "image/png"},
            content=png_bytes(),
        )
    )

    with httpx.Client(transport=transport) as client:
        loaded = load_image(
            image_url="https://example.com/box.png",
            image_base64=None,
            http_client=client,
        )

    assert loaded.suffix == ".png"


def test_rejects_unsupported_url_content_type() -> None:
    transport = httpx.MockTransport(
        lambda _request: httpx.Response(
            200,
            headers={"content-type": "text/plain"},
            content=b"not an image",
        )
    )

    with httpx.Client(transport=transport) as client:
        with pytest.raises(ImageInputError, match="content type"):
            load_image(
                image_url="https://example.com/box.txt",
                image_base64=None,
                http_client=client,
            )


def test_rejects_non_http_url() -> None:
    with pytest.raises(ImageInputError, match="http or https"):
        load_image(image_url="file:///tmp/box.png", image_base64=None)
