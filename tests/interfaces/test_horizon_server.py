"""Tests for the Horizon-compatible MCP entrypoint."""

import asyncio

from mcp.server.fastmcp import FastMCP

from box_ocr_mcp.interfaces.mcp.horizon_server import mcp


def test_horizon_entrypoint_exposes_importable_mcp_server() -> None:
    assert isinstance(mcp, FastMCP)
    assert mcp.name == "box-ocr-mcp"


def test_horizon_entrypoint_exposes_expected_tools() -> None:
    async def list_tool_names() -> list[str]:
        tools = await mcp.list_tools()
        return sorted(tool.name for tool in tools)

    assert asyncio.run(list_tool_names()) == [
        "image_box_ocr",
        "image_box_ocr_base64",
    ]
