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

The server uses RapidOCR with ONNXRuntime and OpenCV headless. This avoids the
`paddlepaddle` runtime and its `libgomp.so.1` system dependency on FastMCP Cloud.

You can tune the minimum OCR text confidence with:

```text
MCP_OCR_TEXT_SCORE=0.5
```

The server still returns literal OCR output and does not translate or normalize
text.
