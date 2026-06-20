"""FastMCP Cloud / Prefect Horizon entrypoint."""

from box_ocr_mcp.interfaces.mcp.server import create_mcp_server

mcp = create_mcp_server()
