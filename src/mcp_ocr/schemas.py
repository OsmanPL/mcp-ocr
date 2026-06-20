"""Public schemas for the OCR MCP tool."""

from pydantic import BaseModel, ConfigDict, Field


class OcrImageResult(BaseModel):
    """Exact response shape returned by the OCR tool."""

    model_config = ConfigDict(extra="forbid")

    raw: str = Field(description="Literal raw text detected by OCR.")
    valores: dict[str, str] = Field(
        description="Visible key-value pairs extracted without normalizing keys."
    )
    porcentaje_confianza: float | None = Field(
        description="Average OCR confidence from 0 to 100, or null if unavailable."
    )
