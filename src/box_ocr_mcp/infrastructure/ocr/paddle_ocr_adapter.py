"""PaddleOCR adapter."""

from collections.abc import Mapping, Sequence
from typing import Any

from box_ocr_mcp.domain.entities import OcrResult


class PaddleOcrAdapter:
    """Run OCR with PaddleOCR and convert results to domain entities."""

    def __init__(self, ocr_engine: Any | None = None) -> None:
        self._ocr_engine = ocr_engine

    def extract_text(self, image_path: str) -> OcrResult:
        """Extract raw OCR text from an image path."""
        result = self._get_ocr_engine().predict(image_path)
        return self._to_ocr_result(result)

    def _get_ocr_engine(self) -> Any:
        if self._ocr_engine is None:
            from paddleocr import PaddleOCR  # type: ignore[import-untyped]

            self._ocr_engine = PaddleOCR(
                lang="latin",
                use_angle_cls=True,
            )
        return self._ocr_engine

    def _to_ocr_result(self, result: Any) -> OcrResult:
        entries = list(self._extract_entries(result))
        lines = [text for text, _score in entries]
        scores = [score for _text, score in entries if score is not None]
        average_confidence = sum(scores) / len(scores) if scores else 0

        return OcrResult(
            raw_text="\n".join(lines),
            lines=lines,
            average_confidence=average_confidence,
        )

    def _extract_entries(self, value: Any) -> list[tuple[str, float | None]]:
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

            entries = []
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
        entries = []
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

        if isinstance(first_item, str):
            return (first_item, self._score_or_none(second_item))

        if self._is_sequence(second_item) and len(second_item) >= 2:
            nested_text = second_item[0]
            nested_score = second_item[1]
            if isinstance(nested_text, str):
                return (nested_text, self._score_or_none(nested_score))

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
