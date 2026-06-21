# MCP OCR

FastMCP server that receives an image URL or a base64 image, runs OCR, and
returns literal extracted text as JSON.

## Run

```bash
uv run mcp-ocr
```

## Tool

`ocr_image(image_file=None, image_url: str | None = None, image_base64: str | None = None)`

Exactly one image input must be provided.

Preferred client flow:

1. Attach or paste an image in the chat client.
2. Ask the client to call `ocr_image` with the attached image as `image_file`.
3. Use `image_url` or `image_base64` only as fallback inputs.

The tool declares `openai/fileParams = ["image_file"]` so OpenAI-compatible
clients can pass an authorized file reference without sending raw base64 through
the chat prompt.

## OCR Model

By default the server initializes PaddleOCR with:

```text
MCP_OCR_LANG=es
MCP_OCR_VERSION=PP-OCRv5
```

`es` is used to select PaddleOCR's Latin-script recognition model for Spanish,
English, and Portuguese text. The server still returns literal OCR output and
does not translate or normalize text.

## Native Runtime Dependencies

Paddle/PaddleOCR needs the OpenMP runtime library `libgomp.so.1` at runtime.
The repository includes `nixpacks.toml` so cloud builders that support Nixpacks
install `libgomp1` in the container.

The repo also includes `Aptfile`, `packages.txt`, and `Dockerfile` fallbacks for
hosts that use a different buildpack or allow explicit Docker builds.
