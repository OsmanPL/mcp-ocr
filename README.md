# MCP OCR

FastMCP server that receives an image URL or a base64 image, runs OCR, and
returns literal extracted text as JSON.

## Run

```bash
uv run mcp-ocr
```

## Tool

`ocr_image(image_url: str | None = None, image_base64: str | None = None)`

Exactly one image input must be provided.
