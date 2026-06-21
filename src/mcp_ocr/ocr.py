"""OCR adapter and result conversion."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class OcrText:
    """Raw OCR text and confidence values."""

    raw: str
    confidence: float | None


class RapidOcrEngine:
    """Run OCR with RapidOCR/ONNXRuntime and return literal recognized text."""

    def __init__(
        self,
        ocr_engine: Any | None = None,
        _lang: str | None = None,
        _ocr_version: str | None = None,
    ) -> None:
        self._ocr_engine = ocr_engine
        self._text_score = float(os.getenv("MCP_OCR_TEXT_SCORE", "0.5"))

    def extract_text(self, image_bytes: bytes, suffix: str) -> OcrText:
        """Extract text from image bytes using a temporary file for OCR."""
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
                temp_file.write(image_bytes)
                temp_path = Path(temp_file.name)

            result = self._predict(str(temp_path))
            return self._to_ocr_text(result)
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

    def _predict(self, image_path: str) -> Any:
        engine = self._get_ocr_engine()
        if callable(engine):
            return engine(image_path, text_score=self._text_score)
        if hasattr(engine, "predict"):
            return engine.predict(image_path)
        if hasattr(engine, "ocr"):
            return engine.ocr(image_path)
        raise RuntimeError("OCR engine does not expose a supported prediction method.")

    def _get_ocr_engine(self) -> Any:
        if self._ocr_engine is None:
            from rapidocr_onnxruntime import RapidOCR

            self._ocr_engine = RapidOCR()
        return self._ocr_engine

    def _to_ocr_text(self, result: Any) -> OcrText:
        entries = self._extract_entries(result)
        lines = [text for text, _score in entries]
        scores = [score for _text, score in entries if score is not None]

        confidence = None
        if scores:
            average = sum(scores) / len(scores)
            confidence = average * 100 if average <= 1 else average
            confidence = max(0.0, min(100.0, confidence))
            confidence = round(confidence, 1)

        return OcrText(raw="\n".join(lines), confidence=confidence)

    def _extract_entries(self, value: Any) -> list[tuple[str, float | None]]:
        if _is_rapidocr_result(value):
            return self._extract_entries(value[0])

        if isinstance(value, Mapping):
            entries = self._extract_mapping_entries(value)
            if entries:
                return entries

            nested_entries: list[tuple[str, float | None]] = []
            for nested_value in value.values():
                nested_entries.extend(self._extract_entries(nested_value))
            return nested_entries

        if self._is_sequence(value):
            direct_entry = self._extract_direct_sequence_entry(value)
            if direct_entry is not None:
                return [direct_entry]

            entries: list[tuple[str, float | None]] = []
            for item in value:
                entries.extend(self._extract_entries(item))
            return entries

        return []

    def _extract_mapping_entries(
        self, value: Mapping[Any, Any]
    ) -> list[tuple[str, float | None]]:
        texts = self._first_present(value, "rec_texts", "texts", "text")
        scores = self._first_present(value, "rec_scores", "scores", "confidence")

        if isinstance(texts, str):
            return [(texts, self._score_or_none(scores))]

        if not self._is_sequence(texts):
            return []

        score_values = scores if self._is_sequence(scores) else []
        entries: list[tuple[str, float | None]] = []
        for index, text in enumerate(texts):
            if isinstance(text, str):
                score = score_values[index] if index < len(score_values) else None
                entries.append((text, self._score_or_none(score)))
        return entries

    def _extract_direct_sequence_entry(
        self, value: Sequence[Any]
    ) -> tuple[str, float | None] | None:
        if len(value) < 2:
            return None

        first_item = value[0]
        second_item = value[1]
        third_item = value[2] if len(value) >= 3 else None

        if isinstance(first_item, str):
            return first_item, self._score_or_none(second_item)

        if isinstance(second_item, str):
            return second_item, self._score_or_none(third_item)

        if self._is_sequence(second_item) and len(second_item) >= 2:
            nested_text = second_item[0]
            nested_score = second_item[1]
            if isinstance(nested_text, str):
                return nested_text, self._score_or_none(nested_score)

        return None

    def _first_present(self, value: Mapping[Any, Any], *keys: str) -> Any:
        for key in keys:
            if key in value:
                return value[key]
        return None

    def _is_sequence(self, value: Any) -> bool:
        return isinstance(value, Sequence) and not isinstance(
            value, str | bytes | bytearray
        )

    def _score_or_none(self, value: Any) -> float | None:
        if isinstance(value, int | float):
            return float(value)
        return None


def _is_rapidocr_result(value: Any) -> bool:
    if not isinstance(value, tuple) or len(value) != 2:
        return False
    ocr_entries, timing = value
    return isinstance(timing, list) and (
        ocr_entries is None or isinstance(ocr_entries, list)
    )


OcrEngine = RapidOcrEngine
