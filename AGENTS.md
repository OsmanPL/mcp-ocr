# AGENTS.md

## Purpose

Build an MCP server in Python using `uv` and `FastMCP`.

This MCP server will be deployed on FastMCP Cloud and consumed by AI clients such as ChatGPT, Claude, Windows Copilot, and other MCP-compatible hosts.

The server performs OCR on images and returns literal extracted text as JSON.

The server must not normalize, transform, translate, infer, or reinterpret detected data.

---

## Image Input Strategy

The MCP server must support only two image input methods:

1. `image_url`
2. `image_base64`

The preferred method is `image_url`.

Base64 is only a fallback when the client cannot provide a downloadable image URL.

---

## Input Rules

Exactly one of these fields must be provided:

```json
{
  "image_url": "https://example.com/image.jpg",
  "image_base64": null
}
```

or:

```json
{
  "image_url": null,
  "image_base64": "<base64 image>"
}
```

Rules:

* Do not accept both at the same time.
* Do not accept requests without an image.
* Do not use `file_path`.
* If `image_url` is provided, download the image.
* If `image_base64` is provided, decode it in memory.

---

## MCP Tool

Tool name:

```text
ocr_image
```

Description:

```text
Receive an image URL or Base64 image, perform OCR, and return literal extracted text as JSON.
```

---

## Output Format

The tool must always return JSON with this exact structure:

```json
{
  "raw": "texto crudo detectado por OCR",
  "valores": {
    "LOTE": "ABC123",
    "VENC": "20/10/2026",
    "FABR": "20/10/2024"
  },
  "porcentaje_confianza": 92.5
}
```

---

## OCR Rules

The OCR output must be literal.

Do not:

* Normalize field names.
* Convert dates.
* Translate text.
* Guess missing values.
* Correct spelling unless the OCR engine itself returns it that way.
* Convert uppercase to lowercase.
* Change abbreviations.
* Interpret product data.
* Add fields that are not visible in the image.

---

## Key-Value Extraction Rules

Extract key-value pairs exactly as they appear in the image.

Examples:

Image text:

```text
LOTE
ABC123
VENC
20/10/2026
FABR
20/10/2024
```

Output:

```json
{
  "raw": "LOTE\nABC123\nVENC\n20/10/2026\nFABR\n20/10/2024",
  "valores": {
    "LOTE": "ABC123",
    "VENC": "20/10/2026",
    "FABR": "20/10/2024"
  },
  "porcentaje_confianza": 91.8
}
```

If the OCR detects text in the same line:

```text
LOTE: ABC123
VENC: 20/10/2026
FABR: 20/10/2024
```

Output:

```json
{
  "raw": "LOTE: ABC123\nVENC: 20/10/2026\nFABR: 20/10/2024",
  "valores": {
    "LOTE": "ABC123",
    "VENC": "20/10/2026",
    "FABR": "20/10/2024"
  },
  "porcentaje_confianza": 93.2
}
```

If a key is detected but no value is confidently detected, include the key with an empty string:

```json
{
  "raw": "LOTE\nVENC\n20/10/2026",
  "valores": {
    "LOTE": "",
    "VENC": "20/10/2026"
  },
  "porcentaje_confianza": 76.4
}
```

---

## Confidence

`porcentaje_confianza` must be a number between 0 and 100.

Use the OCR engine confidence if available.

If the OCR engine returns confidence by word or line, calculate the average confidence of detected text.

If confidence is not available, return:

```json
{
  "porcentaje_confianza": null
}
```

---

## Security Requirements

* Do not log full Base64 payloads.
* Do not store images by default.
* Enforce maximum image size.
* Validate URL content type.
* Use HTTP timeout when downloading images.
* Reject unsupported formats.
* Process images in memory whenever possible.
* Never execute user-provided content.

---

## Suggested Stack

```bash
uv add fastmcp
uv add pillow
uv add pydantic
uv add httpx
uv add opencv-python
uv add pytesseract
```

---

## Success Criteria

The MCP server is complete when:

* It runs with `uv run`.
* It exposes the `ocr_image` MCP tool.
* It accepts `image_url`.
* It accepts `image_base64`.
* It rejects invalid input.
* It performs OCR.
* It returns literal raw text.
* It extracts visible key-value pairs.
* It returns confidence as `porcentaje_confianza`.
* It does not normalize or interpret the data.
