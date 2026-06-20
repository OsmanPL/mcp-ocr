# AGENTS.md

## Project Goal

Build a Python MCP server that performs OCR on photos of cardboard boxes.

The server MUST expose one primary MCP tool:

```txt
image_box_ocr
```

The tool MUST receive an image and return only the text detected by OCR. It MUST NOT interpret, validate, correct, translate, normalize, or semantically reorder the detected text.

The project MUST remain an MCP server. Do NOT add normal REST OCR endpoints such as `/ocr`.

## Primary Use Case

Input images are photos of cardboard boxes that may contain printed or stamped text in:

- Spanish
- English
- Portuguese

The user will not provide the language. The OCR workflow MUST support Latin-alphabet text across these languages without requiring a manual language parameter.

Example text that may appear on a box:

```txt
LOTE A12345
VENCE 15/08/2026
FABR 15/08/2024
```

```txt
BATCH A12345
EXP 15/08/2026
MFG 15/08/2024
```

```txt
LOTE A12345
VALIDADE 15/08/2026
FABRICADO 15/08/2024
```

The MCP server MUST return what the OCR engine detects, even if the result is misspelled, incomplete, noisy, or obviously incorrect.

## Functional Scope

The MCP server is responsible only for:

1. Receiving an image.
2. Preprocessing the image to improve OCR readability.
3. Running OCR.
4. Returning the raw detected text.
5. Returning the detected text lines.
6. Returning the average confidence score if the OCR engine provides one.

The MCP server is NOT responsible for comparing OCR output against expected files, rules, templates, product data, or external references. Any comparison or validation MUST be handled by another agent or external service.

## Strict Non-Goals

The implementation MUST NOT:

- Parse business fields.
- Return structured business fields such as lot, expiration date, manufacturing date, or equivalent concepts.
- Search for patterns.
- Correct words.
- Translate text.
- Normalize terms.
- Infer dates.
- Reorder information based on semantic meaning.
- Decide whether the text is correct or incorrect.
- Compare the OCR result with an expected value.

Do NOT return data like this:

```json
{
  "lot": "...",
  "expiration_date": "...",
  "manufacturing_date": "..."
}
```

Return raw OCR output only.

## Required Tool Contract

### Tool Name

```txt
image_box_ocr
```

### Input

```json
{
  "image_path": "local/path/to/image.jpg"
}
```

### Successful Output

Use these exact JSON keys:

```json
{
  "raw_text": "LOTE A12345\nVENCE 15/08/2026\nFABR 15/08/2024",
  "lines": [
    "LOTE A12345",
    "VENCE 15/08/2026",
    "FABR 15/08/2024"
  ],
  "average_confidence": 0.91
}
```

### Error Output

Never expose raw internal exceptions to the MCP client. On failure, return a controlled response:

```json
{
  "error": "Human-readable error description",
  "raw_text": "",
  "lines": [],
  "average_confidence": 0
}
```

## Remote Secondary Tool

The project also exposes a secondary tool for remote MCP clients that cannot provide server-local file paths:

```txt
image_box_ocr_base64
```

Input:

```json
{
  "image_base64": "..."
}
```

This tool MUST return the same OCR result shape as `image_box_ocr`.

The project also exposes a ChatGPT file-upload tool:

```txt
image_box_ocr_file
```

This tool MUST declare OpenAI file params metadata for `image_file` and accept ChatGPT file references shaped like:

```json
{
  "image_file": {
    "download_url": "https://...",
    "file_id": "file_...",
    "mime_type": "image/png",
    "file_name": "box.png"
  }
}
```

Use this tool for images uploaded directly in ChatGPT. Do not ask ChatGPT to convert large uploaded images into base64.

The primary required local path tool remains:

```txt
image_box_ocr
```

## Architecture Requirements

Use hexagonal architecture, also known as ports and adapters.

Business and application logic MUST NOT depend directly on PaddleOCR, EasyOCR, FastMCP, file-system details, base64 handling, or external framework APIs.

Keep project layers separated as follows:

```txt
src/
  box_ocr_mcp/
    domain/
      entities.py
      ports.py

    application/
      use_cases/
        extract_text_from_box_image.py

    infrastructure/
      ocr/
        paddle_ocr_adapter.py
      image/
        pillow_preprocessor.py
      filesystem/
        temp_file_manager.py

    interfaces/
      mcp/
        server.py
        tools.py

    config/
      settings.py
```

## Domain Entities

Create a simple immutable domain entity for OCR results:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class OcrResult:
    raw_text: str
    lines: list[str]
    average_confidence: float
```

The entity represents OCR output only. It MUST NOT contain parsed business fields.

## Ports

Define a small OCR port:

```python
from typing import Protocol

from box_ocr_mcp.domain.entities import OcrResult


class OcrEnginePort(Protocol):
    def extract_text(self, image_path: str) -> OcrResult:
        ...
```

Define a small image preprocessing port:

```python
from typing import Protocol


class ImagePreprocessorPort(Protocol):
    def preprocess(self, image_path: str) -> str:
        ...
```

Keep interfaces small and specific. Do not create a broad interface that mixes OCR, preprocessing, file handling, and MCP concerns.

## Main Use Case

The main application use case MUST coordinate preprocessing and OCR through ports:

```python
class ExtractTextFromBoxImageUseCase:
    def __init__(
        self,
        preprocessor: ImagePreprocessorPort,
        ocr_engine: OcrEnginePort,
    ):
        self.preprocessor = preprocessor
        self.ocr_engine = ocr_engine

    def execute(self, image_path: str) -> OcrResult:
        processed_path = self.preprocessor.preprocess(image_path)
        return self.ocr_engine.extract_text(processed_path)
```

The use case MUST NOT import PaddleOCR, Pillow, MCP server classes, or concrete adapters.

## SOLID Principles

Apply SOLID throughout the implementation.

### Single Responsibility Principle

Each class should have one clear responsibility.

Examples:

- `PaddleOcrAdapter`: runs OCR.
- `PillowImagePreprocessor`: improves image readability.
- `ExtractTextFromBoxImageUseCase`: coordinates the application flow.
- `McpTools`: exposes MCP tools.

### Open/Closed Principle

It MUST be easy to replace PaddleOCR with another OCR engine, such as EasyOCR, without modifying the use case.

### Liskov Substitution Principle

Any implementation of `OcrEnginePort` MUST be usable anywhere another `OcrEnginePort` implementation is expected.

### Interface Segregation Principle

Prefer small, focused ports over large interfaces.

### Dependency Inversion Principle

Application logic MUST depend on abstractions, not concrete implementations.

## OCR Engine

Use PaddleOCR as the default OCR engine.

Suggested configuration:

```python
PaddleOCR(
    lang="latin",
    use_angle_cls=True,
)
```

This configuration is intended for Latin-alphabet text in Spanish, English, and Portuguese.

## Image Preprocessing

Before OCR, apply basic preprocessing:

- Convert the image to grayscale.
- Increase contrast.
- Increase sharpness.
- Save the processed image as a temporary file.
- Run OCR on the processed temporary image.

Do NOT alter the detected text after OCR.

## Error Handling

The MCP layer MUST catch expected failures and return controlled error payloads.

Examples of expected failures:

- The image path does not exist.
- The image cannot be opened.
- The OCR engine fails.
- Temporary file creation fails.

Error responses MUST follow this shape:

```json
{
  "error": "...",
  "raw_text": "",
  "lines": [],
  "average_confidence": 0
}
```

## Package Manager

Use `uv`.

Do NOT use `pip` directly for project setup.

Expected commands:

```bash
uv init
uv add mcp paddleocr paddlepaddle pillow
uv run python -m box_ocr_mcp.interfaces.mcp.server
```

## Dependencies

Primary dependencies:

```txt
mcp
paddleocr
paddlepaddle
pillow
```

Recommended development dependencies:

```txt
pytest
ruff
mypy
```

Install dependencies with:

```bash
uv add mcp paddleocr paddlepaddle pillow
uv add --dev pytest ruff mypy
```

## Code Quality Requirements

The implementation MUST include:

- Type hints.
- Docstrings for public MCP tools.
- Controlled error handling.
- Clear layer separation.
- Unit tests for the main use case.
- Mock-based tests for OCR behavior.
- No hardcoded absolute paths.
- No mixing of MCP transport logic with OCR logic.

## Documentation Maintenance

Whenever a change affects setup, dependencies, commands, architecture, tool contracts, supported inputs, outputs, behavior, testing, or acceptance criteria, the implementation MUST update `README.md` in the same change.

Keep `README.md` aligned with this file. `AGENTS.md` is the implementation guidance for AI agents; `README.md` is the human-facing project documentation.

## Testing Requirements

Create tests that verify:

1. The use case calls the image preprocessor.
2. The use case calls the OCR engine.
3. Raw OCR text is returned without modification.
4. The OCR adapter returns detected lines.
5. The OCR adapter calculates average confidence.
6. The MCP tool returns a controlled error when image processing fails.

## Acceptance Criteria

The project is complete when:

- It runs with `uv run`.
- The MCP server exposes the `image_box_ocr` tool.
- The tool accepts a local image path.
- The tool returns raw OCR text.
- The tool returns detected lines.
- The tool returns average OCR confidence when available.
- The tool does not parse lot, expiration, manufacturing, or equivalent fields.
- The tool does not correct, translate, normalize, or infer text.
- It supports images containing Spanish, English, and Portuguese Latin-alphabet text.
- The architecture follows ports and adapters.
- Application logic does not depend directly on PaddleOCR or MCP framework classes.
