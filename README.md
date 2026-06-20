# MCP OCR

Python MCP server for running OCR on photos of cardboard boxes.

The server exposes MCP tools for raw OCR on cardboard box images. It is designed to run as an MCP server, not as a REST API.

See [PLAN.md](PLAN.md) for the implementation checklist.

See [HORIZON_PLAN.md](HORIZON_PLAN.md) for the FastMCP Cloud / Prefect Horizon compatibility plan.

See [RUNBOOK.md](RUNBOOK.md) for installation, validation, local execution, and remote deployment notes.

Current implementation status: the local MCP server is complete, and the FastMCP Cloud / Prefect Horizon technical compatibility work is implemented through `horizon_server.py:mcp` and `image_box_ocr_base64`.

## Purpose

This project is designed for box-label OCR where images may contain Latin-alphabet text in Spanish, English, or Portuguese.

The server must return what the OCR engine detects, even when the result is incomplete, noisy, misspelled, or incorrect. It does not validate the text against expected values.

## What This Server Does

- Receives an image.
- Preprocesses the image for better OCR readability.
- Runs OCR.
- Returns raw detected text.
- Returns detected lines.
- Returns average OCR confidence when available.

## What This Server Does Not Do

The server does not:

- Parse business fields.
- Extract lot, expiration, manufacturing, or equivalent fields.
- Search for patterns.
- Correct OCR mistakes.
- Translate text.
- Normalize terms.
- Infer dates.
- Decide whether the detected text is correct.
- Compare OCR output against expected data.

Any validation or comparison must be handled by another agent or external service.

## MCP Tools

### `image_box_ocr`

Use this tool when the image path exists inside the server runtime, such as local development or a mounted server file.

Input:

```json
{
  "image_path": "local/path/to/image.jpg"
}
```

### `image_box_ocr_base64`

Use this tool for hosted or remote MCP clients, including FastMCP Cloud / Prefect Horizon, ChatGPT, Copilot, Claude, or any client that cannot place files directly inside the server runtime.

Input:

```json
{
  "image_base64": "..."
}
```

Successful output:

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

Error output:

```json
{
  "error": "Human-readable error description",
  "raw_text": "",
  "lines": [],
  "average_confidence": 0
}
```

## FastMCP Cloud / Prefect Horizon

Deploy this project as a remote MCP server, not as a normal REST API.

Use this Horizon entrypoint:

```txt
src/box_ocr_mcp/interfaces/mcp/horizon_server.py:mcp
```

Hosted clients should prefer:

```txt
image_box_ocr_base64
```

Successful output:

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

Error output:

```json
{
  "error": "Human-readable error description",
  "raw_text": "",
  "lines": [],
  "average_confidence": 0
}
```

## Optional Tool

A secondary base64 tool may be added later:

```txt
image_box_ocr_base64
```

The required primary tool remains `image_box_ocr`.

## Architecture

The project uses hexagonal architecture, also known as ports and adapters.

Application logic must depend on abstractions, not concrete OCR engines, MCP frameworks, image libraries, file-system details, or base64 handling.

Expected structure:

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

## OCR Engine

PaddleOCR is the default OCR engine.

Suggested configuration:

```python
PaddleOCR(
    lang="latin",
    use_angle_cls=True,
)
```

This is intended to support Latin-alphabet text in Spanish, English, and Portuguese without requiring the user to provide a language.

## Image Preprocessing

Before OCR, the image should be preprocessed with basic improvements:

- Convert to grayscale.
- Increase contrast.
- Increase sharpness.
- Save a temporary processed image.
- Run OCR on the processed image.

The detected text must not be modified after OCR.

## Package Management

Use `uv`.

Requires Python 3.12 or newer.

Install runtime dependencies:

```bash
uv add mcp paddleocr paddlepaddle pillow
```

Install development dependencies:

```bash
uv add --dev pytest ruff mypy
```

Run the MCP server:

```bash
uv run python -m box_ocr_mcp.interfaces.mcp.server
```

## Testing

Expected test coverage:

- The use case calls the image preprocessor.
- The use case calls the OCR engine.
- Raw OCR text is returned without modification.
- The OCR adapter returns detected lines.
- The OCR adapter calculates average confidence.
- The MCP tool returns a controlled error when image processing fails.

Run tests with:

```bash
uv run pytest
```

## Quality Checks

Run linting with:

```bash
uv run ruff check .
```

Run type checking with:

```bash
uv run mypy src
```

## Acceptance Criteria

The project is complete when:

- It runs with `uv run`.
- The MCP server exposes `image_box_ocr`.
- The tool accepts a local image path.
- The tool returns raw OCR text.
- The tool returns detected lines.
- The tool returns average OCR confidence when available.
- The tool does not parse lot, expiration, manufacturing, or equivalent fields.
- The tool does not correct, translate, normalize, or infer text.
- It supports Spanish, English, and Portuguese Latin-alphabet text.
- The architecture follows ports and adapters.
- Application logic does not depend directly on PaddleOCR or MCP framework classes.
