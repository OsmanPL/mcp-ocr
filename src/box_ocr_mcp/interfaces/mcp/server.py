"""MCP server entrypoint."""

from mcp.server.fastmcp import FastMCP

from box_ocr_mcp.application import ExtractTextFromBoxImageUseCase
from box_ocr_mcp.infrastructure.filesystem import TempFileManager
from box_ocr_mcp.infrastructure.image import Base64ImageWriter, PillowImagePreprocessor
from box_ocr_mcp.infrastructure.ocr import PaddleOcrAdapter
from box_ocr_mcp.interfaces.mcp.tools import register_tools


def create_use_case() -> ExtractTextFromBoxImageUseCase:
    """Create the default OCR use case with concrete infrastructure adapters."""
    temp_file_manager = TempFileManager()
    preprocessor = PillowImagePreprocessor(temp_file_manager=temp_file_manager)
    ocr_engine = PaddleOcrAdapter()
    return ExtractTextFromBoxImageUseCase(
        preprocessor=preprocessor,
        ocr_engine=ocr_engine,
    )


def create_mcp_server(
    use_case: ExtractTextFromBoxImageUseCase | None = None,
) -> FastMCP:
    """Create and configure the MCP server."""
    server = FastMCP(name="box-ocr-mcp")
    register_tools(
        server=server,
        use_case=use_case or create_use_case(),
        base64_image_writer=Base64ImageWriter(),
    )
    return server


def main() -> None:
    """Run the MCP server over stdio."""
    create_mcp_server().run()


if __name__ == "__main__":
    main()
