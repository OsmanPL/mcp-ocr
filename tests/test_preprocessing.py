from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageDraw

from mcp_ocr.preprocessing import generate_ocr_variants


def png_bytes(width: int = 20, height: int = 10) -> bytes:
    output = BytesIO()
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((1, 1, 5, 3), fill="black")
    image.save(output, format="PNG")
    return output.getvalue()


def test_generate_ocr_variants_includes_rotations_and_enhancements() -> None:
    variants = generate_ocr_variants(png_bytes(), ".png")
    names = {variant.name for variant in variants}

    assert "rot0_original" in names
    assert "rot90_original" in names
    assert "rot180_original" in names
    assert "rot270_original" in names
    assert "rot0_enhanced" in names
    assert "rot0_binary" in names
    assert all(variant.suffix == ".png" for variant in variants)


def test_generate_ocr_variants_respects_exif_and_returns_png_bytes() -> None:
    variants = generate_ocr_variants(png_bytes(), ".jpg")

    assert variants
    assert all(variant.data.startswith(b"\x89PNG") for variant in variants)
