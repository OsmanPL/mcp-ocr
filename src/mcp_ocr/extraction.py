"""Literal key-value extraction from OCR text."""

from __future__ import annotations

import re

KEY_PATTERN = re.compile(r"^[^\W\d_][\w./-]*$", re.UNICODE)


def extract_visible_key_values(raw: str) -> dict[str, str]:
    """Extract visible key-value pairs without normalizing keys or values."""
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    values: dict[str, str] = {}
    pending_key: str | None = None

    for line in lines:
        inline_key, inline_value = _split_inline_pair(line)
        if inline_key is not None:
            if pending_key is not None:
                values[pending_key] = ""
            values[inline_key] = inline_value
            pending_key = None
            continue

        if _looks_like_key(line):
            if pending_key is not None:
                values[pending_key] = ""
            pending_key = line
            continue

        if pending_key is not None:
            values[pending_key] = line
            pending_key = None

    if pending_key is not None:
        values[pending_key] = ""

    return values


def _split_inline_pair(line: str) -> tuple[str, str] | tuple[None, None]:
    if ":" not in line:
        return None, None

    key, value = line.split(":", 1)
    key = key.strip()
    if not key:
        return None, None
    return key, value.strip()


def _looks_like_key(line: str) -> bool:
    return bool(KEY_PATTERN.match(line)) and not any(char.isdigit() for char in line)
