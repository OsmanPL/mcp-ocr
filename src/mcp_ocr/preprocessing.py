"""Image preprocessing variants for OCR."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


@dataclass(frozen=True)
class ImageVariant:
    """One image candidate to run through OCR."""

    name: str
    data: bytes
    suffix: str


def generate_ocr_variants(image_bytes: bytes, suffix: str) -> list[ImageVariant]:
    """Create OCR-friendly image variants without changing detected text."""
    with Image.open(BytesIO(image_bytes)) as image:
        source = ImageOps.exif_transpose(image).convert("RGB")

    variants: list[ImageVariant] = []
    seen: set[bytes] = set()

    for angle in (0, 90, 180, 270):
        rotated = source.rotate(angle, expand=True) if angle else source.copy()
        _append_variant(
            variants,
            seen,
            name=f"rot{angle}_original",
            image=rotated,
            suffix=suffix,
        )
        _append_variant(
            variants,
            seen,
            name=f"rot{angle}_enhanced",
            image=_enhance_for_ocr(rotated),
            suffix=suffix,
        )
        _append_variant(
            variants,
            seen,
            name=f"rot{angle}_binary",
            image=_binarize_for_ocr(rotated),
            suffix=suffix,
        )

    return variants


def _enhance_for_ocr(image: Image.Image) -> Image.Image:
    scale = 2 if min(image.size) < 1000 else 1
    working = _resize(image, scale)
    working = ImageOps.grayscale(working)
    working = ImageOps.autocontrast(working)
    working = ImageEnhance.Contrast(working).enhance(1.8)
    working = working.filter(ImageFilter.SHARPEN)
    return working.convert("RGB")


def _binarize_for_ocr(image: Image.Image) -> Image.Image:
    enhanced = _enhance_for_ocr(image).convert("L")
    threshold = 160
    binary = enhanced.point(lambda pixel: 255 if pixel > threshold else 0)
    return binary.convert("RGB")


def _resize(image: Image.Image, scale: int) -> Image.Image:
    if scale <= 1:
        return image.copy()

    width, height = image.size
    return image.resize((width * scale, height * scale), Image.Resampling.LANCZOS)


def _append_variant(
    variants: list[ImageVariant],
    seen: set[bytes],
    *,
    name: str,
    image: Image.Image,
    suffix: str,
) -> None:
    data = _encode_png(image)
    if data in seen:
        return

    seen.add(data)
    variants.append(ImageVariant(name=name, data=data, suffix=".png"))


def _encode_png(image: Image.Image) -> bytes:
    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()
